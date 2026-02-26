"""Shortcut 节点模块（v2：Plan → Execute，多步、按风险确认）。

约定：
- 全流程 UI 统一复用 `mcp_workflow`（push_ui_message），不依赖额外 UI name。
- interrupt 仅用于收集用户决策（approve/skip/cancel）。
"""

from __future__ import annotations

import json
import re
import time
import uuid
from typing import Any, Literal

from langchain_core.messages import AIMessage, AIMessageChunk
from langgraph.config import get_stream_writer
from langgraph.graph.message import push_message
from langgraph.graph.ui import AnyUIMessage, push_ui_message
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from agent.config import get_logger
from agent.state import ShortcutState
from agent.tools.auth import ensure_mcp_token
from agent.tools.site_mcp import call_mcp_tool, get_mcp_tools, is_mcp_error_result
from agent.utils.helpers import message_text, find_ai_message_by_id
from agent.utils.llm import llm_nano, llm_nostream

logger = get_logger(__name__)

# ============ 数据模型 ============

class PlanStepModel(BaseModel):
    """计划步骤模型。"""

    title: str = Field(default="", description="步骤标题")
    tool: str = Field(default="", description="工具 code")
    args_json: str = Field(default="", description="工具参数 JSON 字符串")
    needs_params: bool = Field(default=False, description="是否缺少必需参数")
    missing_params: list[str] = Field(default_factory=list, description="缺少的必需参数名称")

class IntentClassificationResult(BaseModel):
    """意图分类和能力说明结果。"""

    intent: Literal["capability_inquiry", "action_request"] = Field(
        ...,
        description="用户意图类型：'capability_inquiry'（能力询问）或 'action_request'（操作请求）",
    )
    capability_response: str = Field(
        default="",
        description="如果是能力询问，这里是生成的能力说明（markdown 格式）；如果是操作请求，这里是空字符串",
    )
    steps: list[PlanStepModel] = Field(
        default_factory=list,
        description="当 intent 为 action_request 时，输出多步工具调用计划",
    )
    param_prompt: str = Field(
        default="",
        description="当存在缺失参数时，输出面向用户的补充信息提示文本",
    )


# ============ 内部工具函数 ============

def _get_anchor_msg(state: ShortcutState) -> AIMessage:
    anchor_id = state.get("shortcut_anchor_id")
    if anchor_id:
        for m in state.get("messages", []):
            if isinstance(m, AIMessage) and getattr(m, "id", None) == anchor_id:
                return m
    return AIMessage(id=str(uuid.uuid4()), content="")


def _push_workflow_ui(
    state: ShortcutState,
    props: dict[str, Any],
    *,
    merge: bool = True,
) -> AnyUIMessage:
    """推送/更新 mcp_workflow UI，并尽量立即 flush。"""
    writer = get_stream_writer()
    anchor = _get_anchor_msg(state)
    ui_id = state.get("shortcut_ui_id") if merge else None
    ui_msg = push_ui_message(
        "mcp_workflow",
        props,
        id=ui_id,
        message=anchor,
        merge=merge,
    )
    if writer is not None:
        writer(ui_msg)
        # 有些运行时会缓冲 custom/ui 事件，这里尽量 flush，避免“最后才一次性显示”
        try:
            flush = getattr(writer, "flush", None)
            if callable(flush):
                flush()
        except Exception:
            pass
    return ui_msg


def _extract_json_object(text: str) -> dict[str, Any] | None:
    t = (text or "").strip()
    if not t:
        return None
    # 直接解析
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    # 截取第一个 { 到最后一个 }
    l = t.find("{")
    r = t.rfind("}")
    if 0 <= l < r:
        try:
            obj = json.loads(t[l : r + 1])
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None


def _risk_of_tool(code: str, desc: str | None) -> bool:
    """按规则标记风险：写操作/破坏性操作需要确认。"""
    c = (code or "").lower()
    d = (desc or "").lower()
    risky_tokens = [
        "set",
        "update",
        "save",
        "delete",
        "remove",
        "create",
        "patch",
        "post",
        "put",
        "write",
        # 中文
        "更新",
        "保存",
        "删除",
        "写入",
        "修改",
        "创建",
    ]
    return any(tok in c for tok in risky_tokens) or any(tok in d for tok in risky_tokens)


def _parse_decision(value: Any) -> str:
    """将 interrupt 返回值解析为 action：approve/skip/cancel。"""
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"approve", "skip", "cancel"}:
            return v
    if isinstance(value, dict):
        v = value.get("value") or value.get("action")
        if isinstance(v, str):
            v2 = v.strip().lower()
            if v2 in {"approve", "skip", "cancel"}:
                return v2
    # 兼容 boolean：True=approve，False=cancel
    if isinstance(value, bool):
        return "approve" if value else "cancel"
    return "cancel"


def _last_user_text(state: ShortcutState) -> str:
    t = (state.get("user_text") or "").strip()
    if t:
        return t
    for m in reversed(state.get("messages", [])):
        # 只要能取到文本就行
        txt = (message_text(m) or "").strip()
        if txt:
            return txt
    return ""


def _format_conversation_history(
    state: ShortcutState,
    *,
    max_messages: int = 8,
    max_chars: int = 2000,
) -> str:
    """提取最近对话历史，供 LLM 理解上下文。"""
    messages = state.get("messages") or []
    lines: list[str] = []
    for m in reversed(messages):
        txt = (message_text(m) or "").strip()
        if not txt:
            continue
        role = "assistant" if isinstance(m, AIMessage) else "user"
        if isinstance(m, dict):
            t = (m.get("type") or "").lower()
            if t in {"human", "user"}:
                role = "user"
            elif t in {"ai", "assistant"}:
                role = "assistant"
            elif t == "system":
                role = "system"
        if role == "system":
            continue
        label = "用户" if role == "user" else "助手"
        lines.append(f"{label}: {txt}")
        if len(lines) >= max_messages:
            break
    lines.reverse()
    history = "\n".join(lines)
    if max_chars > 0 and len(history) > max_chars:
        history = "（对话过长，已截断）\n" + history[-max_chars:]
    return history or "（无）"


def _format_plan_brief(steps: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for i, s in enumerate(steps, start=1):
        title = str(s.get("title") or s.get("tool") or f"步骤{i}")
        tool = str(s.get("tool") or "")
        risky = "（需确认）" if s.get("is_risky") else ""
        lines.append(f"{i}. {title} - {tool}{risky}".strip())
    return "\n".join(lines) if lines else "（空计划）"


def _extract_tool_schema(tool: Any) -> dict[str, Any]:
    """尽力从 LangChain Tool 提取 input schema（参考 ga_mcp 的简洁写法）。"""
    args_schema = getattr(tool, "args_schema", None)
    schema = args_schema if isinstance(args_schema, dict) else {}
    if not schema and hasattr(args_schema, "model_json_schema"):
        try:
            schema = args_schema.model_json_schema()
        except Exception:
            schema = {}
    return schema


def _schema_brief(schema: dict[str, Any]) -> dict[str, Any]:
    """将 schema 压缩成适合 LLM 阅读的摘要（避免 token 爆炸）。"""
    if not isinstance(schema, dict) or not schema:
        return {}
    props = schema.get("properties")
    required = schema.get("required")
    brief: dict[str, Any] = {}
    if isinstance(props, dict):
        brief["properties"] = list(props.keys())[:50]
    if isinstance(required, list):
        brief["required"] = required[:50]
    # 只保留最关键的顶层描述
    if isinstance(schema.get("description"), str):
        brief["description"] = schema["description"][:400]
    return brief


def _tool_to_spec(tool: Any) -> dict[str, Any]:
    code = getattr(tool, "name", None)
    desc = getattr(tool, "description", "") or ""
    schema = _extract_tool_schema(tool)
    return {
        "code": code,
        "name": code,
        "desc": desc,
        # 给 LLM 用：字段/required 摘要（默认）
        "input_schema": _schema_brief(schema),
        # 给前端/调试用：完整 schema（可能较大）
        "input_schema_full": schema,
    }


def _ui_step_result_brief(output: dict[str, Any]) -> str:
    """把单步输出压缩成适合 UI 展示的一句话。"""
    idx = int(output.get("idx", -1))
    title = str(output.get("title") or output.get("tool") or "")
    tool = str(output.get("tool") or "")
    if output.get("skipped"):
        return f"Step {idx+1} skipped: {title} ({tool})"
    if output.get("cancelled"):
        return f"Step {idx+1} cancelled: {title} ({tool})"
    if output.get("ok") is True:
        dur = output.get("duration_ms")
        # 尽量从常见返回结构里提炼一句
        result = output.get("result")
        msg = None
        if isinstance(result, dict):
            msg = result.get("message") or result.get("msg")
        return f"Step {idx+1} succeeded: {title} ({tool})"
    if output.get("ok") is False:
        dur = output.get("duration_ms")
        suffix = f"({dur}ms)" if isinstance(dur, int) else ""
        return f"Step {idx+1} failed: {title} ({tool}) {suffix} - {output.get('error')}"
    return f"Step {idx+1} update: {title} ({tool})"


def _format_step_outputs_log(outputs: list[dict[str, Any]] | None, *, max_lines: int = 50) -> str | None:
    """将 step_outputs 格式化为适合展示在 mcp_workflow.result 的简要日志。"""
    if not outputs:
        return None

    def _short(text: Any, n: int = 220) -> str:
        s = ("" if text is None else str(text)).strip()
        if len(s) <= n:
            return s
        return s[: n - 1] + "…"

    lines: list[str] = []
    for o in outputs:
        if not isinstance(o, dict):
            continue
        idx = int(o.get("idx", -1))
        title = str(o.get("title") or o.get("tool") or f"Step {idx+1}")
        tool = str(o.get("tool") or "")
        if o.get("skipped"):
            lines.append(f"{idx+1}) ⏭ Skipped: {title}".strip())
            continue
        if o.get("cancelled"):
            lines.append(f"{idx+1}) ❌ Cancelled: {title}".strip())
            continue
        if o.get("ok") is False:
            err = _short(o.get("error"))
            detail = f" - {err}" if err else ""
            lines.append(f"{idx+1}) ❌ Failed: {title}{detail}".strip())
            continue

        lines.append(f"{idx+1}) • {title}".strip())

    if not lines:
        return None

    if max_lines > 0 and len(lines) > max_lines:
        hidden = len(lines) - max_lines
        lines = [f"（已截断 {hidden} 行）"] + lines[-max_lines:]
    return "\n".join(lines)


# ============ 子图节点（v2）===========

async def start_shortcut_ui(state: dict[str, Any]) -> dict[str, Any]:
    """主图节点：在进入 shortcut 子图前，先把 mcp_workflow 写入 state.ui（interrupt 快照兜底）。"""
    # Logic to hide "Thinking Completed" card from Intent Router
    intent_ui_id = state.get("intent_ui_id")
    intent_anchor_id = state.get("intent_anchor_id")
    writer = get_stream_writer()
    
    if intent_ui_id and intent_anchor_id and writer:
        # We need to find the anchor message. Since state here is a dict from main graph, 
        # messages are in state["messages"].
        intent_anchor_msg = find_ai_message_by_id(state, intent_anchor_id)
        
        if intent_anchor_msg:
             hide_msg = push_ui_message(
                 "intent_router",
                 {"status": "done", "hidden": True},
                 id=intent_ui_id,
                 message=intent_anchor_msg,
                 merge=True
             )
             writer(hide_msg)

    anchor = AIMessage(id=str(uuid.uuid4()), content="")
    ui_msg = push_ui_message(
        "mcp_workflow",
        {"status": "loading", "title": "Background Operation", "message": "Preparing background operation..."},
        message=anchor,
    )
    return {
        "messages": [anchor],
        "ui": [ui_msg],
        "shortcut_anchor_id": anchor.id,
        "shortcut_ui_id": ui_msg["id"],
        "intent_ui_id": state.get("intent_ui_id"),
        "intent_anchor_id": state.get("intent_anchor_id"),
    }


async def shortcut_init(state: ShortcutState) -> dict[str, Any]:
    """初始化：创建锚点/UI，拉取 MCP tools 列表。"""
    writer = get_stream_writer()
    user_text = _last_user_text(state)
    cached_tools = state.get("tools") or []
    cached_at = state.get("tools_fetched_at")
    now_ts = time.time()
    cache_ttl = 300
    can_reuse_tools = bool(cached_tools) and isinstance(cached_at, (int, float)) and now_ts - float(cached_at) < cache_ttl

    # 优先复用主图 `start_shortcut_ui` 已写入的 anchor/ui_id（避免 interrupt 时卡片消失 & 避免重复卡片）
    anchor = _get_anchor_msg(state)
    existing_anchor_id = state.get("shortcut_anchor_id")
    existing_ui_id = state.get("shortcut_ui_id")
    if not existing_anchor_id or not existing_ui_id:
        anchor = AIMessage(id=str(uuid.uuid4()), content="")
        ui_msg = push_ui_message(
            "mcp_workflow",
            {"status": "loading", "title": "Background Operation", "message": "Fetching available tools..."},
            message=anchor,
        )
        return_payload: dict[str, Any] = {
            "messages": [anchor],
            "ui": [ui_msg],
            "shortcut_anchor_id": anchor.id,
            "shortcut_ui_id": ui_msg["id"],
        }
        if writer is not None:
            writer({"messages": [anchor]})
            try:
                flush = getattr(writer, "flush", None)
                if callable(flush):
                    flush()
            except Exception:
                pass
    else:
        ui_msg = push_ui_message(
            "mcp_workflow",
            {"status": "loading", "title": "Background Operation", "message": "Fetching available tools..."},
            id=existing_ui_id,
            message=anchor,
            merge=True,
        )
        return_payload = {"ui": [ui_msg]}
        if writer is not None:
            writer(ui_msg)
            try:
                flush = getattr(writer, "flush", None)
                if callable(flush):
                    flush()
            except Exception:
                pass

    tenant_id = state.get("tenant_id")
    site_id = state.get("site_id")
    
    # 确保 MCP token 有效
    token, token_updates = await ensure_mcp_token(state, context="Shortcut")
    if token_updates:
        # 将 token 更新合并到返回的 state 中
        return_payload.update(token_updates)
    
    tools: list[dict[str, Any]] = []
    tools_fetched_at = cached_at if can_reuse_tools else None
    if can_reuse_tools:
        tools = list(cached_tools)
    else:
        try:
            # Shortcut v2 仅允许使用 site-setting-basic 的 MCP tools
            # （ShortcutState 不包含 intent 字段，因此这里必须显式传入）
            mcp_tools = await get_mcp_tools(tenant_id=tenant_id, site_id=site_id, intent="shortcut", token=token)
        except Exception as e:
            ui_err = push_ui_message(
                "mcp_workflow",
                {"status": "error", "title": "Background Operation", "message": f"获取工具失败：{e}"},
                id=state.get("shortcut_ui_id") or ui_msg["id"],
                message=anchor,
                merge=True,
            )
            if writer is not None:
                writer(ui_err)
                try:
                    flush = getattr(writer, "flush", None)
                    if callable(flush):
                        flush()
                except Exception:
                    pass
            return {
                "ui": [ui_err],
                "user_text": user_text,
                "tools": [],
                "tools_fetched_at": None,
                "error": f"get_tools_failed: {e}",
            }

        for t in mcp_tools or []:
            tools.append(_tool_to_spec(t))
        tools_fetched_at = now_ts

    ui_ready = push_ui_message(
        "mcp_workflow",
        {"status": "running", "title": "Background Operation", "message": f"Fetched {len(tools)} tools, processing request..."},
        id=state.get("shortcut_ui_id") or ui_msg["id"],
        message=anchor,
        merge=True,
    )
    if writer is not None:
        writer(ui_ready)
        try:
            flush = getattr(writer, "flush", None)
            if callable(flush):
                flush()
        except Exception:
            pass

    return {
        **return_payload,
        "ui": [ui_ready],
        "user_text": user_text,
        "tools": tools,
        "tools_fetched_at": tools_fetched_at,
        "plan_steps": None,
        "current_step_idx": 0,
        "current_step": None,
        "step_outputs": [],
        "pending_decision": None,
        "cancelled": False,
        "error": None,
    }


async def shortcut_plan(state: ShortcutState) -> dict[str, Any]:
    """生成 plan_steps（多步），并标记 is_risky。如果检测到能力询问，则生成能力说明。"""
    tools = state.get("tools") or []
    user_text = _last_user_text(state)
    conversation_history = _format_conversation_history(state)

    # ============ LLM 意图分类和能力说明生成============
    is_capability_inquiry = False
    capability_response = ""
    
    # 构建工具摘要和 schema 供 LLM 参考
    tool_summaries = []
    tool_lines = []
    for tool in tools:
        code = str(tool.get("code") or tool.get("name") or "")
        desc = str(tool.get("desc") or tool.get("description") or "")
        if code:
            tool_summaries.append(f"- {code}: {desc}")
        schema = tool.get("input_schema") or {}
        input_schema_full = tool.get("input_schema_full") or {}
        if code:
            tool_lines.append(
                f"- {code}: {desc}\n"
                f"  input_schema: {json.dumps(schema, ensure_ascii=False)}\n"
                f"  input_schema_full: {json.dumps(input_schema_full, ensure_ascii=False)}"
            )
    tools_info = "\n".join(tool_summaries) if tool_summaries else "No available tools"
    tools_info_full = "\n".join(tool_lines) if tool_lines else "- (No available tools)"

    result = IntentClassificationResult(intent="action_request")
    try:
        unified_prompt = f"""You are a background operation assistant. Please analyze the user's intent and generate an appropriate response.

Conversation History (Latest {8}):
{conversation_history}

Current User Question: {user_text}

Available Tools List:
{tools_info}

Available Tools (with schema):
{tools_info_full}

Please determine the user's intent:
1. capability_inquiry: The user is asking what the system can do, what features are supported, what operations are available, etc. (e.g., "What can you do?", "What features do you have?", "What support?")
2. action_request: The user is requesting to perform a specific operation or task, including explicit action verbs (e.g., check, get, update, save, set, modify, delete, query) + specific objects (e.g., "Check current site info", "Update site settings", "Get config", "Set timezone")

Criteria:
- If the question contains words asking about capabilities like "What can you do", "supported features" -> capability_inquiry
- If the question contains actions like "Help me", "Check", "Get", "Update" + object -> action_request

If capability_inquiry:
- Please generate a user-friendly capability description (in markdown format), including:
  1. A short welcome message
  2. A categorized list of main capabilities (e.g., Site Settings, Config Management, Data Query)
  3. Provide 2-3 example questions to guide the user
- Do NOT list technical details (like parameter schemas), but verify what operations can be performed in business language.

If action_request:
- Leave capability_response empty.
- Generate a multi-step tool execution plan (steps), and mark missing parameters.
- If parameters are missing, output 'param_prompt' to ask the user (concise and friendly English, MUST explicitly state missing parameter names, markdown allowed, NO code blocks).

Plan Output Requirements:
1. steps must have at least 1 step.
2. tool must be from available tool codes.
3. args_json should extract parameter values from user request as much as possible (JSON string).
4. **IMPORTANT: Parameter Completeness Check**
   - For each step, check if the tool's required parameters are provided in args_json.
   - If a required parameter is missing in args_json, or is null/empty string/empty object {{}}:
     * Set needs_params to true
     * List all missing required parameter names in missing_params array
   - For object-type required parameters (e.g., system_basic_inspect), if the object is empty {{}} or has no valid fields, mark as missing.
   - If all required parameters valid, set needs_params to false, missing_params to empty array.
5. Parameter Extraction Rules:
   - If user explicitly stated values (e.g., "Main product is phones"), extract into args_json.
   - If user only mentioned parameter names but no values (e.g., "I want to modify main product"), leave empty in args_json but mark needs_params: true.
6. When any step has needs_params: true, generate a user-facing prompt in 'param_prompt':
   - Explain what parameters are needed in concise, friendly English.
   - Must explicit name the missing parameters.
   - Markdown allowed, no code blocks.
   - If no missing params, leave param_prompt empty.
"""

        structured_llm = llm_nostream.with_structured_output(schema=IntentClassificationResult )
        result: IntentClassificationResult = await structured_llm.ainvoke(
            [
                {"role": "system", "content": "Only output structured JSON matching the schema, no extra text."},
                {"role": "user", "content": unified_prompt},
            ],config={"callbacks": []}
        )
        
        is_capability_inquiry = result.intent == "capability_inquiry"
        capability_response = result.capability_response.strip() if result.capability_response else ""
        
        logger.info(f"[Shortcut] Intent classification: user_text={user_text!r}, intent={result.intent}, is_capability_inquiry={is_capability_inquiry}")
        
        # 去除可能存在的 markdown 代码块标记
        if capability_response:
            capability_response = re.sub(r"^```(markdown)?\s*", "", capability_response, flags=re.IGNORECASE | re.MULTILINE).strip()
            capability_response = re.sub(r"\s*```$", "", capability_response, flags=re.MULTILINE).strip()
            logger.info(f"[Shortcut] Generated capability_response (first 200 chars): {capability_response[:200]}...")
            
    except Exception as e:
        logger.error(f"[Shortcut] Intent classification and response generation failed: {e}")
        is_capability_inquiry = False
        capability_response = ""

    # 如果是能力询问，返回能力说明
    if is_capability_inquiry:
        _push_workflow_ui(
            state,
            {"status": "loading", "title": "Background Operation", "message": "检测到能力询问，正在整理可用操作…"},
            merge=True,
        )

        # 如果 LLM 没有生成回复，使用降级方案
        if not capability_response:
            capability_response = f"我可以帮您执行以下Background Operation：\n\n{tools_info}\n\n您可以告诉我例如\"更新站点设置\"或\"获取配置信息\"。"

        # 创建一个完成的 AI 消息
        response_msg = AIMessage(content=capability_response)

        # 更新 UI 为完成状态
        _push_workflow_ui(
            state,
            {
                "status": "done",
                "title": "Background Operation",
                "message": "已回复您的问题。",
            },
            merge=True,
        )

        return {
            "messages": [response_msg],
            "is_capability_inquiry": True,
        }

    # 如果是操作请求，继续生成执行计划
    _push_workflow_ui(
        state,
        {"status": "running", "title": "Background Operation", "message": "Generating execution plan..."},
        merge=True,
    )

    steps_raw = result.steps if isinstance(result.steps, list) else []
    param_prompt = result.param_prompt.strip() if isinstance(result.param_prompt, str) else ""
    steps: list[dict[str, Any]] = []
    tool_set = {str(t.get("code")) for t in tools if t.get("code")}

    if isinstance(steps_raw, list):
        for s in steps_raw:
            tool = str(getattr(s, "tool", "") or "").strip()
            if not tool or (tool_set and tool not in tool_set):
                continue
            title = str(getattr(s, "title", "") or tool).strip()
            args_json = getattr(s, "args_json", "")
            args: dict[str, Any] = {}
            if isinstance(args_json, str) and args_json.strip():
                try:
                    parsed = json.loads(args_json)
                    args = parsed if isinstance(parsed, dict) else {}
                except Exception:
                    parsed = _extract_json_object(args_json)
                    args = parsed if isinstance(parsed, dict) else {}
            needs_params = bool(getattr(s, "needs_params", False))
            missing_params = getattr(s, "missing_params", None)
            missing_params = list(missing_params) if isinstance(missing_params, list) else []
            desc = ""
            for t in tools:
                if str(t.get("code")) == tool:
                    desc = str(t.get("desc") or "")
                    break
            steps.append(
                {
                    "title": title,
                    "tool": tool,
                    "args": args,
                    "is_risky": _risk_of_tool(tool, desc),
                    "needs_params": needs_params,
                    "missing_params": missing_params,
                }
            )

    if not steps:
        # fallback：单步，取第一个工具（尽量可执行）
        fallback_tool = str(tools[0].get("code")) if tools else ""
        steps = [{"title": "执行Background Operation", "tool": fallback_tool, "args": {}, "is_risky": _risk_of_tool(fallback_tool, tools[0].get("desc") if tools else None)}] if fallback_tool else []
        _push_workflow_ui(
            state,
            {
                "status": "error" if not steps else "running",
                "title": "Background Operation",
                "message": "计划解析失败，已降级为单步执行。" if steps else "无法生成计划：工具列表为空。",
            },
            merge=True,
        )

    brief = _format_plan_brief(steps)
    
    # 检查是否有步骤缺少必需参数（使用 LLM 标记的结果）
    has_missing_params = False
    for step in steps:
        needs_params = step.get("needs_params", False)
        missing_params = step.get("missing_params") or []
        if needs_params and missing_params:
            tool_code = str(step.get("tool") or "")
            logger.info(f"[Shortcut] Step '{tool_code}' missing required params (LLM marked): {missing_params}")
            has_missing_params = True
            break
    
    # 如果缺少参数，生成提示消息（由计划 LLM 直接输出）
    if has_missing_params:
        if not param_prompt:
            # 降级：最小可用提示，仍清晰列出缺失参数名
            lines = ["Additional information is required to continue:"]
            for step in steps:
                needs_params = step.get("needs_params", False)
                missing_params = step.get("missing_params") or []
                if not (needs_params and missing_params):
                    continue
                title = str(step.get("title") or step.get("tool") or "")
                lines.append(f"- {title}: {', '.join([str(p) for p in missing_params])}")
            param_prompt = "\n".join(lines)

        if param_prompt:
            logger.info("[Shortcut] Missing params detected, generating prompt and setting needs_params=True")
            _push_workflow_ui(
                state,
                {
                    "status": "done",
                    "title": "Background Operation: Additional information required",
                    "message": param_prompt,
                },
                merge=True,
            )
            
            # 创建提示消息返回给用户
            response_msg = AIMessage(content=param_prompt)
            
            result = {
                "messages": [response_msg],
                "plan_steps": steps,
                "current_step_idx": 0,
                "current_step": None,
                "pending_decision": None,
                "is_capability_inquiry": False,
                "needs_params": True,  # 标记需要用户补充参数
            }
            logger.info(f"[Shortcut] Returning with needs_params=True, result keys: {list(result.keys())}")
            return result
    
    _push_workflow_ui(
        state,
        {
            "status": "running", 
            "title": "Background Operation", 
            "message": f"Plan generated:\n{brief}",
            "steps": steps,
            "active_step": 1,
        },
        merge=True,
    )

    return {
        "plan_steps": steps,
        "current_step_idx": 0,
        "current_step": None,
        "pending_decision": None,
        "is_capability_inquiry": False,
        "needs_params": False,
    }


async def shortcut_prepare_step(state: ShortcutState) -> dict[str, Any]:
    """设置 current_step，并更新进度 UI。"""
    steps = state.get("plan_steps") or []
    idx = int(state.get("current_step_idx") or 0)
    if idx < 0:
        idx = 0
    if idx >= len(steps):
        return {"current_step": None}

    step = steps[idx]
    title = str(step.get("title") or step.get("tool") or f"步骤{idx+1}")
    tool = str(step.get("tool") or "")
    _push_workflow_ui(
        state,
        {
            "status": "running",
            "title": "Background Operation",
            "message": f"Preparing step {idx+1}/{len(steps)}: {title}\nTool: {tool}",
            "active_step": idx + 1,
        },
        merge=True,
    )
    return {"current_step": step, "pending_decision": None}


async def shortcut_confirm_step(state: ShortcutState) -> dict[str, Any]:
    """仅对风险步骤进行确认（approve/skip/cancel）。"""
    step = state.get("current_step") or {}
    if not isinstance(step, dict) or not step:
        return {}
    if not step.get("is_risky"):
        return {"pending_decision": {"action": "approve"}}

    idx = int(state.get("current_step_idx") or 0)
    steps = state.get("plan_steps") or []
    title = str(step.get("title") or step.get("tool") or f"步骤{idx+1}")

    has_multiple_steps = len(steps) > 1
    confirm_actions = "Approve / Skip / Cancel" if has_multiple_steps else "Approve / Cancel"
    _push_workflow_ui(
        state,
        {
            "status": "confirm",
            "title": "Background Operation: Confirmation Required",
            "message": f"This step may modify data: Step {idx+1}/{len(steps)} [{title}].\nPlease confirm in the card below: {confirm_actions}",
            "active_step": idx + 1,
        },
        merge=True,
    )

    decision = interrupt(
        {
            "question": f"This step may modify data: Step {idx+1}/{len(steps)} [{title}]. Please select action:",
            "options": (
                [
                    {"label": "Approve & Execute", "value": "approve"},
                    {"label": "Skip Step", "value": "skip"},
                    {"label": "Cancel All", "value": "cancel"},
                ]
                if has_multiple_steps
                else [
                    {"label": "Approve & Execute", "value": "approve"},
                    {"label": "Cancel", "value": "cancel"},
                ]
            ),
        }
    )
    action = _parse_decision(decision)
    return {"pending_decision": {"action": action}}


async def shortcut_execute_step(state: ShortcutState) -> dict[str, Any]:
    """执行当前 step（或 skip/cancel），记录输出并推进 idx。"""
    steps = state.get("plan_steps") or []
    idx = int(state.get("current_step_idx") or 0)
    outputs = list(state.get("step_outputs") or [])

    if idx >= len(steps):
        return {}

    step = state.get("current_step") or steps[idx]
    if not isinstance(step, dict) or not step:
        return {"error": "invalid_step"}

    action = ((state.get("pending_decision") or {}).get("action") or "approve").lower()
    title = str(step.get("title") or step.get("tool") or f"Step {idx+1}")
    tool = str(step.get("tool") or "")
    args = step.get("args") if isinstance(step.get("args"), dict) else {}

    if action == "cancel":
        out = {"idx": idx, "title": title, "tool": tool, "cancelled": True}
        outputs.append(out)
        result_log = _format_step_outputs_log(outputs)
        _push_workflow_ui(
            state,
            {
                "status": "cancelled",
                "title": "Background Operation",
                "message": _ui_step_result_brief(out),
                "result": result_log,
                "last_step": {k: out.get(k) for k in ["idx", "title", "tool", "cancelled"]},
                "step_outputs": outputs,
            },
            merge=True,
        )
        return {"cancelled": True, "step_outputs": outputs}

    if action == "skip":
        out = {"idx": idx, "title": title, "tool": tool, "skipped": True}
        outputs.append(out)
        result_log = _format_step_outputs_log(outputs)
        _push_workflow_ui(
            state,
            {
                "status": "running",
                "title": "Background Operation",
                "message": _ui_step_result_brief(out),
                "result": result_log,
                "last_step": {k: out.get(k) for k in ["idx", "title", "tool", "skipped"]},
                "step_outputs": outputs,
            },
            merge=True,
        )
        return {"step_outputs": outputs, "current_step_idx": idx + 1, "current_step": None, "pending_decision": None}

    # approve 执行
    _push_workflow_ui(
        state,
        {"status": "running", "title": "Background Operation", "message": f"Executing step {idx+1}/{len(steps)}: {title}..." },
        merge=True,
    )

    tenant_id = state.get("tenant_id")
    site_id = state.get("site_id")
    
    # 确保 MCP token 有效（如果过期则自动刷新）
    token, token_updates = await ensure_mcp_token(state, context="Shortcut")
    
    start = time.time()
    try:
        logger.info(f"[Shortcut][MCP] call tool={tool} input={json.dumps(args, ensure_ascii=False)}")
        result = await call_mcp_tool(
            tool_name=tool,
            tool_input=args,
            tenant_id=tenant_id,
            site_id=site_id,
            intent="shortcut",
            token=token,
        )
        dur_ms = int((time.time() - start) * 1000)
        
        # 如果有 token 更新，合并到返回的 state 中
        return_updates: dict[str, Any] = {}
        if token_updates:
            return_updates.update(token_updates)
        
        # 统一判断 MCP 错误返回（isError / structuredContent.errorCode），不区分具体错误码
        mcp_is_err, mcp_err_msg = is_mcp_error_result(result)
        if mcp_is_err:
            result_obj = result if isinstance(result, dict) else {"error": mcp_err_msg}
            success = False
            error_msg = mcp_err_msg
        else:
            # 解析 result：支持列表格式 [{"id": "...", "text": "{...}", "type": "text"}]
            result_obj = result
            if isinstance(result, list) and len(result) > 0:
                first_item = result[0]
                if isinstance(first_item, dict) and "text" in first_item:
                    text_content = first_item["text"]
                    if isinstance(text_content, str):
                        try:
                            result_obj = json.loads(text_content)
                        except (json.JSONDecodeError, TypeError):
                            result_obj = text_content
            elif isinstance(result, str):
                try:
                    result_obj = json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    result_obj = result
            # 检查 success 字段判断是否成功
            success = True
            error_msg = None
            if isinstance(result_obj, dict):
                success = result_obj.get("success", True)  # 默认 True 以保持向后兼容
                error_msg = result_obj.get("error") or result_obj.get("message") or ""
        out = {
            "idx": idx,
            "title": title,
            "tool": tool,
            "args": args,
            "ok": success,
            "error": error_msg if not success else None,
            "result": result_obj,
            "duration_ms": dur_ms,
        }
        
        outputs.append(out)
        result_log = _format_step_outputs_log(outputs)
        
        # 每步执行完成后立即反馈给前端（只放摘要，避免 result 太大）
        _push_workflow_ui(
            state,
            {
                "status": "running" if success else "error",
                "title": "Background Operation",
                "message": _ui_step_result_brief(out),
                "result": result_log,
                "last_step": {
                    "idx": idx,
                    "title": title,
                    "tool": tool,
                    "ok": success,
                    "duration_ms": dur_ms,
                    "message": (result_obj.get("message") if isinstance(result_obj, dict) else None),
                },
                "step_outputs": outputs,
            },
            merge=True,
        )
        return {
            **return_updates,
            "step_outputs": outputs,
            "current_step_idx": idx + 1,
            "current_step": None,
            "pending_decision": None,
        }
    except Exception as e:
        dur_ms = int((time.time() - start) * 1000)
        out = {"idx": idx, "title": title, "tool": tool, "args": args, "ok": False, "error": str(e), "duration_ms": dur_ms}
        outputs.append(out)
        result_log = _format_step_outputs_log(outputs)
        _push_workflow_ui(
            state,
            {
                "status": "error",
                "title": "Background Operation",
                "message": _ui_step_result_brief(out),
                "result": result_log,
                "last_step": {
                    "idx": idx,
                    "title": title,
                    "tool": tool,
                    "ok": False,
                    "duration_ms": dur_ms,
                    "error": str(e),
                },
                "step_outputs": outputs,
            },
            merge=True,
        )
        return {"error": f"execute_failed: {e}", "step_outputs": outputs}



async def shortcut_finalize(state: ShortcutState) -> dict[str, Any]:
    """汇总展示。"""
    # 如果是能力询问，已经返回了消息，直接结束
    if state.get("is_capability_inquiry"):
        return {}
    
    # 如果需要用户补充参数，已经返回了提示消息，直接结束
    if state.get("needs_params"):
        return {}
    
    cancelled = bool(state.get("cancelled"))
    err = state.get("error")
    outputs = state.get("step_outputs") or []
    steps = state.get("plan_steps") or []
    user_text = _last_user_text(state)

    ok_count = len([o for o in outputs if isinstance(o, dict) and o.get("ok")])
    skip_count = len([o for o in outputs if isinstance(o, dict) and o.get("skipped")])
    total = len(steps) if steps else len(outputs)

    if err:
        status = "error"
        msg = f"Execution failed: {err}\nCompleted {ok_count}/{total}, skipped {skip_count}."
    elif cancelled:
        status = "cancelled"
        msg = f"Cancelled.\nCompleted {ok_count}/{total}, skipped {skip_count}."
    else:
        status = "done"
        msg = f"Background operation completed ({len(steps)} steps)."

    result_log = _format_step_outputs_log(outputs)
    ui_done = _push_workflow_ui(
        state,
        {
            "status": "done",
            "title": "Background Operation",
            "message": f"Background operation completed ({len(steps)} steps).",
            "result": result_log,
            "active_step": len(steps) + 1,
            # 让前端有机会展示详情（即便目前不渲染，也可用于日志/调试）
            "step_outputs": outputs,
        },
        merge=True,
    )

    # 生成用户友好的回复并添加到 messages
    response_content = None
    if not cancelled and not err and outputs:
        # 提取所有成功步骤的结果
        successful_outputs = [o for o in outputs if isinstance(o, dict) and o.get("ok")]
        if successful_outputs:
            try:
                # 构建结果摘要供 LLM 参考
                results_summary = []
                for out in successful_outputs:
                    result = out.get("result")
                    title = out.get("title") or out.get("tool") or ""
                    if isinstance(result, dict):
                        # 提取关键信息
                        summary = {
                            "step": title,
                            "tool": out.get("tool"),
                            "data": result,
                        }
                        results_summary.append(summary)

                # 使用 LLM 生成用户友好的回复（流式：llm_nano SSE）
                response_prompt = f"""You are a background operation assistant. The user's request has been completed. Please generate a friendly reply based on the execution results.

User Request: {user_text}

Execution Results:
{json.dumps(results_summary, ensure_ascii=False, indent=2)}

Please reply in markdown/text format, including:
1. Briefly describe the completed operations.
2. Clearly display key information (e.g., site info, settings, etc.).
3. Group multiple results if applicable.

IMPORTANT: Do not output markdown code blocks wrapping the entire reply (do not start or end with ```). Just output the content.

Reply:"""

                # 先写入一个 anchor message，后续用 chunk 流式推送
                writer = get_stream_writer()
                stream_anchor = AIMessage(id=str(uuid.uuid4()), content="")
                if writer is not None:
                    writer({"messages": [stream_anchor]})
                    try:
                        flush = getattr(writer, "flush", None)
                        if callable(flush):
                            flush()
                    except Exception:
                        pass

                parts: list[str] = []
                async for chunk in llm_nano.astream(response_prompt):
                    # chunk 可能是 MessageChunk，也可能是 str；尽量兼容
                    piece = getattr(chunk, "content", chunk)
                    if not isinstance(piece, str) or not piece:
                        continue
                    parts.append(piece)
                    # 关键：chunk 走 messages 流（SSE）
                    push_message(
                        AIMessageChunk(id=stream_anchor.id, content=piece),
                        state_key="messages",
                    )

                raw_content = "".join(parts).strip()
                # 兜底清理：如果模型仍输出了外层代码块，尽量剥掉（不影响流式已展示，只影响最终落盘）
                response_content = re.sub(
                    r"^```(markdown)?\s*", "", raw_content, flags=re.IGNORECASE | re.MULTILINE
                ).strip()
                response_content = re.sub(r"\s*```$", "", response_content, flags=re.MULTILINE).strip()

                # 用同一个 id 返回最终内容，尽量避免前端/存储出现“空锚点”
                stream_anchor.content = response_content
                return {
                    "ui": [ui_done],
                    "messages": [stream_anchor],
                }
            except Exception as e:
                logger.error(f"[Shortcut] Finalize response generation failed: {e}")
                # 降级：直接格式化结果
                response_parts = ["✅ Completed following operations:\n"]
                for out in successful_outputs:
                    title = out.get("title") or out.get("tool") or ""
                    result = out.get("result")
                    if isinstance(result, dict):
                        response_parts.append(f"### {title}\n")
                        response_parts.append(f"```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```\n")
                response_content = "\n".join(response_parts)

    # 如果没有生成回复，使用默认消息
    if not response_content:
        if cancelled:
            response_content = f"Operation cancelled. Completed {ok_count}/{total}, Skipped {skip_count}."
        elif err:
            response_content = f"Execution failed: {err}\nCompleted {ok_count}/{total}, Skipped {skip_count}."
        else:
            response_content = f"Operation completed. Completed {ok_count}/{total}, Skipped {skip_count}."

    # 创建 AI 消息
    response_msg = AIMessage(content=response_content)

    return {
        "ui": [ui_done],
        "messages": [response_msg],
    }
