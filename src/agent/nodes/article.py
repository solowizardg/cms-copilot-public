"""Article 节点模块。

处理文章生成工作流。
"""

import json
import re
import uuid
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.config import get_stream_writer
from langgraph.graph.ui import AnyUIMessage, push_ui_message
from pydantic import BaseModel, Field

from agent.config import ARTICLE_CONTENT_STYLE_OPTIONS, get_logger
from agent.state import CopilotState
from agent.tools.article import call_cloud_article_workflow
from agent.tools.auth import ensure_mcp_token
from agent.tools.lowcode_app import list_apps
from agent.utils.helpers import find_ai_message_by_id, latest_user_message, message_text
from agent.utils.llm import llm_nostream

logger = get_logger(__name__)


class ArticleClarifyResult(BaseModel):
    """LLM 输出：文章参数抽取 + 澄清问题。"""

    model_config = {"extra": "forbid"}

    topic: str | None = Field(
        default=None, description="Article topic/title (English, be specific)"
    )
    content_format: str | None = Field(
        default=None, description="Content format/column (e.g., News Center/Blog)"
    )
    target_audience: str | None = Field(default=None, description="Target audience (English)")
    tone: str | None = Field(
        default=None, description="Tone/Style (e.g., Professional/Friendly)"
    )
    writing_requirements: str | None = Field(
        default=None,
        description="Writing requirements/guidelines extracted from user input (e.g., word count, SEO keywords, style guidelines). Optional field.",
    )
    missing: list[str] = Field(
        default_factory=list,
        description="List of missing field names, only allow: topic/content_format/target_audience/tone",
    )
    question_to_user: str = Field(
        ...,
        description=(
            "Clarification question for user when parameters are missing (English, multi-line, include recommended reply template); "
            "empty string if not missing."
        ),
    )


async def _llm_extract_and_question(
    user_text: str, collected: dict[str, str | None]
) -> ArticleClarifyResult:
    """依赖大模型从自然语言中抽取参数，并生成缺参澄清问题。"""
    prompt = f"""You are a "Parameter Filler" for a CMS article generation assistant.

Goal: Extract 4 necessary parameters for article generation from user input:
- topic
- content_format
- target_audience
- tone

You will receive:
1) User input for this turn: user_text
2) Historically collected parameters: collected (may be empty)

Requirements:
1) If user_text or collected explicitly provides certain parameters, fill in the corresponding fields.
2) For uncertain/missing parameters, add the field name to the 'missing' list.
3) When 'missing' is not empty, generate 'question_to_user':
   - English
   - Briefly explain what information is missing.
   - Then provide a recommended reply template (key: value format) for the user to fill in all at once.
4) When 'missing' is empty, 'question_to_user' should be an empty string.
5) 'missing' can only contain: topic/content_format/target_audience/tone (do not output other values).

user_text:
{user_text}

collected (historically collected, empty if none):
{json.dumps(collected, ensure_ascii=False)}
"""

    structured = llm_nostream.with_structured_output(ArticleClarifyResult)
    return await structured.ainvoke(
        [
            {
                "role": "system",
                "content": "Only output structured results conforming to the schema, do not output extra text.",
            },
            {"role": "user", "content": prompt},
        ],config={"callbacks": []}
    )


async def article_clarify_parse(state: CopilotState) -> dict[str, Any]:
    """文章澄清：解析用户补充内容（依赖大模型），更新已收集字段与缺失项。

    这个节点不负责推 UI；只负责把状态更新好，让后续 UI 节点渲染时能“自动带入”已填写内容。
    """
    # Generative UI 推荐使用 submit 继续对话：直接从最新用户消息解析
    user_msg = latest_user_message(state)
    user_text = message_text(user_msg)

    # -------------------------------------------------------
    # Show "Thinking" card (IntentRouter style) BEFORE LLM
    # -------------------------------------------------------
    
    # Try to reuse existing IntentRouter card (from Router flow)
    intent_ui_id = state.get("intent_ui_id")
    intent_anchor_id = state.get("intent_anchor_id")
    intent_anchor_msg = find_ai_message_by_id(state, intent_anchor_id)

    # Detect direct_intent from latest real message (skip UI anchor AIMessage)
    direct_intent = None
    messages = state.get("messages", []) or []
    for m in reversed(messages):
        kwargs = None
        if isinstance(m, dict):
            kwargs = m.get("additional_kwargs")
        else:
            kwargs = getattr(m, "additional_kwargs", None)
        if isinstance(kwargs, dict) and kwargs.get("direct_intent"):
            direct_intent = kwargs.get("direct_intent")
            break
    is_direct_article_task = direct_intent == "article_task"
    
    thinking_ui_id = None
    thinking_anchor = None
    is_new_card = False
    
    if intent_ui_id and intent_anchor_msg:
        thinking_ui_id = intent_ui_id
        thinking_anchor = intent_anchor_msg
    else:
        # Create new if not exists (Direct flow)
        thinking_ui_id = str(uuid.uuid4())
        thinking_anchor = AIMessage(id=str(uuid.uuid4()), content="")
        is_new_card = True

    writer = get_stream_writer()

    # Push the Thinking Card (Show)
    ui_payload = {
        "status": "thinking",
        "main_title": "Analyzing article requirements...",
        "rag_message": "Checking parameters...",
        "rag_status": "running",
    }
    if is_direct_article_task:
        ui_payload["hidden"] = False

    ui_msg = push_ui_message(
        "intent_router",
        ui_payload,
        id=thinking_ui_id,
        message=thinking_anchor,
        merge=True,  # Always merge to support updates
    )
    if writer:
        writer(ui_msg)
    # -------------------------------------------------------


    # 兼容前端用 submit 发送 JSON（更稳定）：先做一次合并，再交给 LLM 做最终抽取/补齐
    submit_payload: dict[str, Any] | None = None
    
    # Priority 0: Check additional_kwargs from the VERY LAST message 
    # (Front-end might send 'assistant' role to force markdown rendering, so user_msg filter might miss it)
    if state.get("messages") and len(state["messages"]) > 0:
        last_msg = state["messages"][-1]
        payload_kwargs = last_msg.additional_kwargs.get("submitted_payload")
        if payload_kwargs and isinstance(payload_kwargs, dict):
            submit_payload = payload_kwargs

    if isinstance(user_text, str):
        s = user_text.strip()
        # 1. 尝试直接解析 JSON（兼容旧版纯 JSON 发送）
        if s.startswith("{") and s.endswith("}"):
            try:
                obj = json.loads(s)
                if isinstance(obj, dict):
                    submit_payload = obj
            except Exception:
                pass

        # 2. 尝试解析 "隐写" 在 HTML 注释里的 JSON（新版 UI：文本+隐藏JSON）
        #    例如: "... <!-- {"topic": "..."} -->"
        if not submit_payload:
            match = re.search(r"<!--\s*(\{.*?\})\s*-->", s, re.DOTALL)
            if match:
                try:
                    obj = json.loads(match.group(1))
                    if isinstance(obj, dict):
                        submit_payload = obj
                except Exception:
                    pass

    # 合并历史已收集的参数（支持多轮补齐）
    collected = {
        "topic": (state.get("article_topic") or "").strip(),
        "content_format": (state.get("article_content_format") or "").strip(),
        "target_audience": (state.get("article_target_audience") or "").strip(),
        "tone": (state.get("article_tone") or "").strip(),
        "app_id": (str(state.get("article_app_id") or "")).strip(),
        "app_name": (state.get("article_app_name") or "").strip(),
        "model_id": (str(state.get("article_model_id") or "")).strip(),
    }

    # 如果 submit 传了结构化字段，先覆盖到 collected（空字符串不覆盖）
    if submit_payload:
        for k in ("topic", "content_format", "target_audience", "tone"):
            v = submit_payload.get(k)
            if isinstance(v, str) and v.strip():
                collected[k] = v.strip()
        app_id = submit_payload.get("app_id")
        if app_id is not None and str(app_id).strip():
            collected["app_id"] = str(app_id).strip()
        app_name = submit_payload.get("app_name")
        if isinstance(app_name, str) and app_name.strip():
            collected["app_name"] = app_name.strip()
        model_id = submit_payload.get("model_id")
        if model_id is not None and str(model_id).strip():
            collected["model_id"] = str(model_id).strip()
        # 处理 writing_requirements（可选字段）
        writing_requirements = submit_payload.get("writing_requirements")
        if isinstance(writing_requirements, str):
            collected["writing_requirements"] = writing_requirements.strip()

    # 依赖 LLM 抽取/判断缺参/生成澄清问题
    # 把 user_text 也传给 LLM：如果是 JSON，就传格式化后的 JSON，模型更容易理解
    user_text_for_llm = (
        json.dumps(submit_payload, ensure_ascii=False) if submit_payload else user_text
    )
    result = await _llm_extract_and_question(
        user_text=user_text_for_llm, collected=collected
    )

    # 合并 LLM 提取结果
    merged = {
        "topic": (result.topic or collected.get("topic") or "").strip(),
        "content_format": (
            result.content_format or collected.get("content_format") or ""
        ).strip(),
        "target_audience": (
            result.target_audience or collected.get("target_audience") or ""
        ).strip(),
        "tone": (result.tone or collected.get("tone") or "").strip(),
        "app_id": (collected.get("app_id") or "").strip(),
        "app_name": (collected.get("app_name") or "").strip(),
        "model_id": (collected.get("model_id") or "").strip(),
        "writing_requirements": (
            result.writing_requirements or collected.get("writing_requirements") or ""
        ).strip(),
    }
    # 关键：不要完全相信模型的 missing（它可能“误判缺失”）。
    # 以合并后的真实字段值是否为空为准，确保用户已填写时能进入下一步。
    required_keys = ["app_id", "topic", "content_format", "target_audience", "tone"]
    missing = [k for k in required_keys if not merged.get(k)]
    is_complete = len(missing) == 0

    if not is_complete:
        display_labels = {
            "app_id": "App Name",
            "topic": "Topic",
            "content_format": "Content Format",
            "target_audience": "Target Audience",
            "tone": "Tone",
        }
        question = result.question_to_user or ""
        if "app_id" in missing:
            app_tip = "Please select an App Name first."
            question = f"{question}\n{app_tip}" if question else app_tip
        if not question:
            question = "Please provide missing information: " + ", ".join(
                display_labels.get(k, k) for k in missing
            )
        # 如果这是第一次进入澄清流程，则初始化 UI anchor / ui_id，便于后续 UI 节点 merge 更新
        ui_id = state.get("article_clarify_ui_id")
        anchor_id = state.get("article_clarify_anchor_id")
        out_messages: list[Any] = []
        if not ui_id:
            ui_id = str(uuid.uuid4())
        if not anchor_id:
            anchor_msg = AIMessage(id=str(uuid.uuid4()), content="")
            out_messages.append(anchor_msg)
            anchor_id = anchor_msg.id
            
        # If we created a new Thinking card, persist it in state so we can reuse/refer to it?
        # Actually, if it's hidden now, maybe we don't strictly need to persist it for future turns.
        # But to ensure it renders correctly in history, adding the anchor is good.
        if is_new_card and thinking_anchor:
             out_messages.append(thinking_anchor)

        return {
            "messages": out_messages,
            "intent_ui_id": thinking_ui_id,  # Persist for next UI step to close
            "intent_anchor_id": thinking_anchor.id if thinking_anchor else None,
            "article_clarify_pending": True,
            "article_topic": merged.get("topic") or None,
            "article_content_format": merged.get("content_format") or None,
            "article_target_audience": merged.get("target_audience") or None,
            "article_tone": merged.get("tone") or None,
            "article_app_id": merged.get("app_id") or None,
            "article_app_name": merged.get("app_name") or None,
            "article_model_id": merged.get("model_id") or None,
            "article_writing_requirements": merged.get("writing_requirements") or None,
            "article_missing": missing,
            "article_clarify_question": question,
            "article_clarify_ui_id": ui_id,
            "article_clarify_anchor_id": anchor_id,
        }

    out_messages: list[Any] = []
    return {
        "messages": out_messages,
        "intent_ui_id": thinking_ui_id,
        "intent_anchor_id": thinking_anchor.id if thinking_anchor else None,
        "article_clarify_pending": False,
        "article_topic": merged["topic"],
        "article_content_format": merged["content_format"],
        "article_target_audience": merged["target_audience"],
        "article_tone": merged["tone"],
        "article_app_id": merged["app_id"],
        "article_app_name": merged["app_name"] or None,
        "article_model_id": merged["model_id"] or None,
        "article_writing_requirements": merged.get("writing_requirements") or None,
        "article_missing": [],
        "article_clarify_question": "",
    }


async def article_clarify_ui(state: CopilotState) -> dict[str, Any]:
    """文章澄清：专门负责渲染/推送澄清 UI（含预填 + Content style 下拉）。

    每次用户补充信息后，都会先经过 `article_clarify_parse` 更新 state，
    如果仍缺参，就会回到这里再次展示 UI，并自动带入已填写的答案。
    """
    ui_id = state.get("article_clarify_ui_id")
    anchor_id = state.get("article_clarify_anchor_id")
    anchor_msg = find_ai_message_by_id(state, anchor_id)
    if ui_id is None or anchor_msg is None:
        # 理论上 parse 节点已经初始化过；这里兜底防御
        ui_id = ui_id or str(uuid.uuid4())
        anchor_msg = anchor_msg or AIMessage(id=str(uuid.uuid4()), content="")

    missing = state.get("article_missing") or []
    question = state.get("article_clarify_question") or ""

    # 确保 MCP token 有效（如果过期则自动刷新）
    token, token_updates = await ensure_mcp_token(state, context="Article")

    app_options: list[dict[str, str]] = []
    try:
        apps_resp = await list_apps(
            site_id=state.get("site_id"),
            page=1,
            page_size=50,
            tenant_id=state.get("tenant_id"),
            token=token,
        )
        if apps_resp.success:
            app_options = [
                {
                    "id": str(app.id),
                    "name": app.name,
                    "model_id": str(app.default_model_id)
                    if app.default_model_id is not None
                    else "",
                }
                for app in apps_resp.data.list
            ]
    except Exception:
        app_options = []

    app_id = (str(state.get("article_app_id") or "")).strip()
    app_name = (state.get("article_app_name") or "").strip()
    model_id = (str(state.get("article_model_id") or "")).strip()
    if app_id and not app_name and app_options:
        for opt in app_options:
            if opt.get("id") == app_id:
                app_name = opt.get("name") or ""
                if not model_id:
                    model_id = opt.get("model_id") or ""
                break

    # question 由前端 ArticleClarifyCard 展示；若未收到则用 missing 生成兜底提示
    ui_props = {
        "status": "need_info",
        "missing": missing,
        "question": question,
        "topic": state.get("article_topic") or "",
        "content_format": state.get("article_content_format") or "",
        "target_audience": state.get("article_target_audience") or "",
        # Content style：这里复用 tone 字段承载（后续 workflow 也用 tone）
        "tone": state.get("article_tone") or "",
        "tone_options": ARTICLE_CONTENT_STYLE_OPTIONS,
        "app_id": app_id,
        "app_name": app_name,
        "app_options": app_options,
        "model_id": model_id,
        "writing_requirements": state.get("article_writing_requirements") or "",
    }

    # Hide Thinking Card if exists
    intent_ui_id = state.get("intent_ui_id")
    intent_anchor_id = state.get("intent_anchor_id")
    intent_anchor_msg = find_ai_message_by_id(state, intent_anchor_id)
    if intent_ui_id and intent_anchor_msg:
        hide_msg = push_ui_message(
             "intent_router",
             {"status": "done", "hidden": True},
             id=intent_ui_id,
             message=intent_anchor_msg,
             merge=True
        )
        writer = get_stream_writer()
        if writer:
             writer(hide_msg)

    # 推送 UI（merge 更新）
    try:
        ui_msg = push_ui_message(
            "article_clarify",
            ui_props,
            id=ui_id,
            message=anchor_msg,
            merge=True,
        )
        writer = get_stream_writer()
        if writer is not None:
            writer(ui_msg)
    except Exception:
        ui_msg = None

    # 不使用 interrupt：让自定义 UI 组件通过 useStreamContext().submit() 继续对话
    # 这样不会出现默认的 “需要人工处理 / resume” 面板。
    result: dict[str, Any] = {
        "article_clarify_pending": True,
        "article_model_id": model_id or None,
    }

    # 如果有 token 更新，合并到返回的 state 中
    if token_updates:
        result.update(token_updates)

    return result


async def start_article_ui(state: CopilotState) -> dict[str, Any]:
    """先把文章 workflow 的进度卡片显示出来。"""
    user_msg = latest_user_message(state)
    _ = message_text(user_msg)  # 暂时不展示 topic

    ui_anchor_msg = AIMessage(id=str(uuid.uuid4()), content="")

    # 关键：必须先 stream anchor 消息，否则前端收到 UI 消息时找不到 anchor 会报错
    writer = None
    try:
        writer = get_stream_writer()
        if writer is not None:
            writer({"messages": [ui_anchor_msg]})
    except Exception:
        writer = None

    # Hide Thinking Card if exists
    intent_ui_id = state.get("intent_ui_id")
    intent_anchor_id = state.get("intent_anchor_id")
    intent_anchor_msg = find_ai_message_by_id(state, intent_anchor_id)
    if intent_ui_id and intent_anchor_msg:
         hide_msg = push_ui_message(
             "intent_router",
             {"status": "done", "hidden": True},
             id=intent_ui_id,
             message=intent_anchor_msg,
             merge=True
         )
         if writer:
              writer(hide_msg)

    ui_msg_start = push_ui_message(
        "article_workflow",
        {
            "status": "running",
            "run_id": None,
            "thread_id": None,
            "current_node": None,
            "flow_node_list": [],
            "error_message": None,
        },
        message=ui_anchor_msg,
    )

    # 只通过 writer() 发送 UI，不要同时放到返回值的 ui 字段（避免冲突）
    if writer is not None:
        writer(ui_msg_start)

    # 注意：不返回 ui 字段，只通过 writer() 实时 stream
    # 但需要保存 ui_id 和 anchor_id 供后续节点更新 UI
    return {
        "messages": [ui_anchor_msg],
        "article_ui_id": ui_msg_start["id"],
        "article_anchor_id": ui_anchor_msg.id,
    }


async def handle_article(state: CopilotState) -> CopilotState:
    """处理文章生成工作流。"""
    user_msg = latest_user_message(state)
    topic = (state.get("article_topic") or "").strip() or message_text(user_msg)

    ui_msg_id = state.get("article_ui_id")
    ui_anchor_msg = find_ai_message_by_id(state, state.get("article_anchor_id"))
    writer = get_stream_writer()

    if ui_anchor_msg is None or not ui_msg_id:
        ui_anchor_msg = AIMessage(id=str(uuid.uuid4()), content="")
        ui_msg_start = push_ui_message(
            "article_workflow",
            {
                "status": "running",
                "run_id": None,
                "thread_id": None,
                "current_node": None,
                "flow_node_list": [],
                "error_message": None,
            },
            message=ui_anchor_msg,
        )
        ui_msg_id = ui_msg_start["id"]
        state["messages"].append(ui_anchor_msg)
        state["ui"] = list(state.get("ui") or []) + [ui_msg_start]

    flow_node_list: list[dict] = []
    current_node: str | None = None
    run_id: str | None = None
    thread_id: str | None = None
    error_message: str | None = None
    last_ui_msg: AnyUIMessage | None = None

    def _find_flow_progress(obj):
        if isinstance(obj, dict):
            fp = obj.get("flow_progress")
            if isinstance(fp, dict):
                return fp
            for v in obj.values():
                found = _find_flow_progress(v)
                if found is not None:
                    return found
        elif isinstance(obj, list):
            for v in obj:
                found = _find_flow_progress(v)
                if found is not None:
                    return found
        return None

    def _finalize_flow_nodes_for_done(nodes: list[dict]) -> list[dict]:
        finalized: list[dict] = []
        for n in nodes:
            if not isinstance(n, dict):
                continue
            node_status = (n.get("node_status") or "").upper()
            if node_status in {"FAILED", "ERROR"}:
                new_status = node_status
            else:
                new_status = "SUCCESS"
            nn = dict(n)
            nn["node_status"] = new_status
            finalized.append(nn)

        if not any(
            (x.get("node_code") == "__completed__")
            for x in finalized
            if isinstance(x, dict)
        ):
            finalized.append(
                {
                    "node_code": "__completed__",
                    "node_name": "Workflow completed",
                    "node_status": "SUCCESS",
                    "node_message": "Workflow has been completed.",
                }
            )
        return finalized

    def _merge_ui(status: str):
        nonlocal last_ui_msg, current_node, flow_node_list
        payload_flow_nodes = flow_node_list
        payload_current_node = current_node
        if status == "done":
            payload_flow_nodes = _finalize_flow_nodes_for_done(flow_node_list)
            payload_current_node = "__completed__"
            flow_node_list = payload_flow_nodes
            current_node = payload_current_node

        ui_payload = {
            "status": status,
            "run_id": run_id,
            "thread_id": thread_id,
            "current_node": payload_current_node,
            "flow_node_list": payload_flow_nodes,
            "error_message": error_message,
        }

        # If done, populate result details
        if status == "done":
            ui_payload["result_topic"] = state.get("article_topic")
            # todo: result_url logic? For now assume topic is link or no link needed yet
            # ui_payload["result_url"] = ...
            ui_payload["setup"] = {
                "app_name": state.get("article_app_name") or state.get("article_app_id"),
                "tone": state.get("article_tone"),
                "format": state.get("article_content_format"),
            }

        ui_msg = push_ui_message(
            "article_workflow",
            ui_payload,
            id=ui_msg_id,
            message=ui_anchor_msg,
            merge=True,
        )
        last_ui_msg = ui_msg
        if writer is not None:
            writer(ui_msg)

    try:
        # todo: X-Site-Url X-Site-Host 都是不应该传递的参数
        # @柯要林 @黎凌后续修复
        # @date: 2026-02-03
        workflow_headers = {
            "X-Site-Id": str(state.get("site_id")),
            "X-Tenant-Id": str(state.get("tenant_id")),
            "X-Site-Url": str(state.get("site_url","https://site-dev.cedemo.cn/api")),
            "X-Site-Host": str(state.get("site_url","https://site-dev.cedemo.cn/api")),
        }

        # 构建 human_prompt：合并 topic + writing_requirements（如有）
        writing_requirements = (state.get("article_writing_requirements") or "").strip()
        if writing_requirements:
            human_prompt = f"""## Topic

{topic}

## Writing Requirements

{writing_requirements}"""
        else:
            human_prompt = topic

        input_data: dict = {
            "chat_type": "chat",
            "user_id": 1,
            "app_id": str(state.get("article_app_id")),
            "model_id": str(state.get("article_model_id")),
            "language": "中文",
            "human_prompt": human_prompt,
            "topic": topic,
            "content_format": state.get("article_content_format") or "新闻中心",
            "target_audience": state.get("article_target_audience") or "读者和投资者",
            "tone": state.get("article_tone") or "Professional",
        }

        async def _on_item(item: dict):
            nonlocal run_id, thread_id, current_node, flow_node_list, error_message
            event = item.get("event")
            data = item.get("data") or {}

            if event == "metadata":
                run_id = data.get("run_id") or run_id
                _merge_ui("running")
                return

            if event == "updates":
                fp = _find_flow_progress(data)
                if isinstance(fp, dict):
                    maybe_list = fp.get("flow_node_list")
                    if isinstance(maybe_list, list):
                        flow_node_list = maybe_list
                    cn = fp.get("current_node")
                    if isinstance(cn, str):
                        current_node = cn
                if isinstance(data, dict):
                    for v in data.values():
                        if isinstance(v, dict):
                            thread_id = v.get("thread_id") or thread_id
                            run_id = v.get("run_id") or run_id
                _merge_ui("running")
                return

            if event == "error":
                msg = (
                    data.get("message")
                    or data.get("error")
                    or json.dumps(data, ensure_ascii=False)
                )
                error_message = str(msg)
                _merge_ui("error")

        _ = await call_cloud_article_workflow(
            input_data, on_item=_on_item, headers=workflow_headers
        )

    except Exception as exc:
        error_message = str(exc)
        _merge_ui("error")
        return state

    if error_message:
        return state

    _merge_ui("done")
    if last_ui_msg is not None:
        state["ui"] = list(state.get("ui") or []) + [last_ui_msg]
    
    # 清除文章相关状态，防止下次意图识别后复用旧参数
    cleanup_updates = {
        "article_clarify_pending": None,
        "article_topic": None,
        "article_content_format": None,
        "article_target_audience": None,
        "article_tone": None,
        "article_writing_requirements": None,
        "article_missing": None,
        "article_clarify_question": None,
        "article_app_id": None, # App 选择也重置
        "article_app_name": None,
        "article_model_id": None,
        "article_ui_id": None,
        "article_anchor_id": None,
        "article_clarify_ui_id": None,
        "article_clarify_anchor_id": None,
    }
    return {**state, **cleanup_updates}
