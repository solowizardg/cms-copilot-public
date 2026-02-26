"""Entry 节点模块。

入口节点：检查是否需要恢复 shortcut 流程。
"""
from typing import Any

import uuid

from langchain_core.messages import AIMessage
from langgraph.graph.ui import push_ui_message

from agent.config import get_logger
from agent.state import CopilotState
from agent.utils.helpers import latest_user_message
from agent.utils.website_header import get_extra_headers

logger = get_logger(__name__)

async def entry_node(state: CopilotState) -> dict[str, Any]:
    """入口节点：检查是否是恢复消息或直接指定意图。

    返回 resume_target 标记，后续条件边根据此值决定跳转。
    """
    options = state.get("options")
    confirmed = state.get("confirmed")
    # 优先从最新消息的 additional_kwargs 中提取 direct_intent（前端隐式传递）
    # 也可以从 state 中获取（如果由其他节点写入）
    direct_intent = state.get("direct_intent")
    
    # 关键修复：前端 SEOPlannerCard 使用 role="assistant" 发送带有 direct_intent 的消息
    # 因此不能只看 latest_user_message (它会过滤掉 AI 消息)，必须检查最后一条触发消息
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        kwargs = None
        if isinstance(last_msg, dict):
            kwargs = last_msg.get("additional_kwargs")
        else:
            kwargs = getattr(last_msg, "additional_kwargs", None)

        if isinstance(kwargs, dict):
            msg_intent = kwargs.get("direct_intent")
            if msg_intent:
                direct_intent = msg_intent

    resume_target = state.get("resume_target")
    article_clarify_pending = state.get("article_clarify_pending")
    report_insights_pending = state.get("report_insights_pending")
    report_confirm_ui_id = state.get("report_confirm_insights_ui_id")
    insights_confirmed = state.get("insights_confirmed")

    # 统一口径：前端/调用方仅传"意图标签"（而不是节点名）
    allowed_intents = {"rag", "shortcut", "article_task", "seo_planning", "site_report"}
    
    # 提前获取认证信息（无论走哪个分支都需要）
    extra_headers = get_extra_headers()
    logger.info(f"entry_node: extra_headers: {extra_headers}")
    auth_infos = {
        "tenant_id": extra_headers['tenant_id'],
        "site_id": extra_headers['site_id'],
    }

    # 1. 特殊情况：SEO publish 触发的新一轮 article 任务，清理旧澄清状态并强制走新流程
    if direct_intent == "article_task":
        return {
            "resume_target": "router_ui",
            "intent": None,
            "direct_intent": direct_intent,
            "article_clarify_pending": None,
            "article_missing": None,
            "article_clarify_question": None,
            "article_clarify_ui_id": None,
            "article_clarify_anchor_id": None,
            "article_clarify_summary_ui_id": None,
            "article_clarify_summary_anchor_id": None,
            **auth_infos,
        }

    # 2. 优先处理 Pending 状态（中断恢复）- 只有明确处于"等待用户输入"的流程才允许恢复
    # 如果 options 存在且 confirmed 还是 None，说明 Shortcut 在等待确认
    if options is not None and confirmed is None:
        logger.debug("[DEBUG] entry_node: resuming shortcut flow (pending confirmation)")
        return {
            "resume_target": "shortcut",
            **auth_infos,
        }

    # 如果处在"文章参数澄清"流程中：跳回 article_clarify 子图继续
    if article_clarify_pending:
        logger.debug("[DEBUG] entry_node: resuming article clarify flow (pending parameters)")
        return {
            "resume_target": "article_clarify",
            **auth_infos,
        }

    # 如果处在"Report 洞察确认"流程中：等待前端 submit 带回 confirmed，然后恢复到 report 子图继续洞察
    pending_report_confirm = bool(report_insights_pending) or (
        bool(report_confirm_ui_id) and insights_confirmed is None
    )
    if pending_report_confirm:
        # 更稳：从后往前找最近一次带 payload 的提交消息（避免最后一条是 UI anchor/空消息）
        messages = state.get("messages", []) or []
        confirmed = None
        for m in reversed(messages):
            kwargs = None
            if isinstance(m, dict):
                kwargs = m.get("additional_kwargs")
            else:
                kwargs = getattr(m, "additional_kwargs", None)
            if isinstance(kwargs, dict) and "report_insights_confirmed" in kwargs:
                confirmed = kwargs.get("report_insights_confirmed")
                break

        if confirmed is not None:
            logger.info("[entry_node] resume report insights via submit (confirmed=%s)", confirmed)
            # 创建新的洞察阶段 UI anchor，确保洞察“生成中/结果”按顺序出现在对话底部
            insights_anchor = AIMessage(id=str(uuid.uuid4()), content="")

            # 先推送“洞察生成中”的进度卡（confirmed=True 时）
            progress_ui_id = f"report_progress_insights:{insights_anchor.id}"
            progress_ui = None
            if bool(confirmed):
                progress_ui = push_ui_message(
                    "report_progress_insights",
                    {
                        "status": "loading",
                        "step": "generating_insights",
                        "steps": ["Generate Insights", "Completed"],
                        "active_step": 1,
                        "message": "Generating insights report...",
                    },
                    id=progress_ui_id,
                    message=insights_anchor,
                    merge=True,
                )
            return {
                "messages": [insights_anchor],
                "ui": [progress_ui] if progress_ui is not None else [],
                "resume_target": "report",
                "report_resume_mode": "insights",
                "report_insights_pending": False,
                "insights_confirmed": bool(confirmed),
                "report_anchor_id": insights_anchor.id,
                "report_progress_insights_ui_id": progress_ui_id,
                "report_insights_ui_id": f"report_insights:{insights_anchor.id}",
                **auth_infos,
            }

    # 3. 处理显式指定意图 (Direct Intent)
    # 验证有效性，如果有效则传递给 Router 作为"强提示"（Hint），但不直接跳过 Router
    # 这样能保证所有非中断流程都经过统一的意图识别节点
    validated_direct_intent = None
    if isinstance(direct_intent, str) and direct_intent:
        if direct_intent in allowed_intents or direct_intent == "introduction":
            validated_direct_intent = direct_intent
        else:
            logger.debug(
                f"[DEBUG] entry_node: invalid direct_intent '{direct_intent}', ignoring"
            )

    # 4. 默认：新的一轮对话 -> 进入 Router UI -> Router (LLM)
    # 只要没有 Pending 任务，就视为新对话
    logger.debug(f"[DEBUG] entry_node: routing to router_ui (direct_intent={validated_direct_intent})")
    return {
        "resume_target": "router_ui",
        "intent": None,        # 强制清除旧意图，确保触发 LLM
        "direct_intent": validated_direct_intent, # 传递给 Router 作为参考
        # "article_clarify_pending": None, # 安全起见也可清除
        **auth_infos,
    }
