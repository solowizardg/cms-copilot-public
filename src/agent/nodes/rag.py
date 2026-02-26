"""RAG 节点模块。

处理知识库查询请求。
"""

import asyncio
import uuid

import httpx
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer
from langgraph.graph.message import push_message
from langgraph.graph.ui import push_ui_message

from agent.config import RAG_API_URL, RAG_SITE_ID, RAG_TENANT_ID, get_logger
from agent.state import CopilotState
from agent.tools.rag import rag_sse_events
from agent.utils.helpers import find_ai_message_by_id, latest_user_message, message_text

logger = get_logger(__name__)


async def start_rag_ui(state: CopilotState, config: RunnableConfig | None = None) -> dict:
    """Prepare for RAG, ensuring we have a session ID, but do NOT create a separate card."""
    # From config get thread_id as session_id (reuse same session thread_id)
    session_id = None
    if config:
        configurable = config.get("configurable") or {}
        session_id = configurable.get("thread_id")
    session_id = str(session_id) if session_id else str(uuid.uuid4())

    # We do NOT push a new UI message here. Use the existing intent_router card.
    # We return the necessary IDs for state, but no new UI operations.
    return {
        "rag_session_id": session_id,
    }


async def handle_rag(state: CopilotState, config: RunnableConfig | None = None) -> CopilotState:
    """处理 RAG 知识库查询。"""
    # 提取用户问题
    user_msg = latest_user_message(state)
    question = message_text(user_msg).strip()
    
    # 如果问题为空，返回错误提示
    if not question:
        answer_text = "抱歉，未检测到您的问题，请重新输入。"
        state["messages"].append(AIMessage(content=answer_text))
        return state

    # 从 state 或环境变量获取参数（优先使用前端传入）
    tenant_id = state.get("tenant_id") or RAG_TENANT_ID
    site_id = state.get("site_id") or RAG_SITE_ID
    
    # 从 config 获取 thread_id 作为 session_id（复用同一会话的 thread_id）
    session_id = state.get("rag_session_id")
    if not session_id:
        # 兜底：没有先经过 start_rag_ui 时，仍能工作
        if config:
            configurable = config.get("configurable") or {}
            session_id = configurable.get("thread_id")
        session_id = str(session_id) if session_id else str(uuid.uuid4())
        state["rag_session_id"] = session_id
    
    # 调用 RAG API（流式答案）
    answer_parts: list[str] = []
    ev_count = 0
    writer = get_stream_writer()

    # Reuse the IntentRouter UI card
    intent_ui_id = state.get("intent_ui_id")
    intent_anchor_id = state.get("intent_anchor_id")
    intent_anchor_msg = find_ai_message_by_id(state, intent_anchor_id)

    def _update_intent_ui(props_patch: dict) -> None:
        """Helper to update the intent_router card."""
        if intent_ui_id and intent_anchor_msg is not None:
            push_ui_message(
                "intent_router",
                props_patch,
                id=intent_ui_id,
                message=intent_anchor_msg,
                merge=True,
            )

    # Indicate start of RAG
    _update_intent_ui({
        "rag_status": "running",
        "rag_message": "Initializing...",
    })

    stream_anchor = AIMessage(id=str(uuid.uuid4()), content="")
    state["messages"].append(stream_anchor)
    if writer is not None:
        writer({"messages": [stream_anchor]})

    try:
        async for ev in rag_sse_events(
            question=question,
            tenant_id=str(tenant_id or ""),
            site_id=str(site_id or ""),
            session_id=session_id,
            rag_api_url=RAG_API_URL,
        ):
            ev_count += 1
            # Ignore initializing steps as requested
            if ev.node_name in ["workflow", "analysis_language", "detect_language", "initialize"]:
                continue

            if ev.node_name == "generate_answer":
                answer = ev.data.get("answer")
                if isinstance(answer, str) and answer:
                    answer_parts.append(answer)
                    # Update status to show we are generating
                    _update_intent_ui({
                         "rag_status": "running",
                         "rag_message": "Processing: generate_answer"
                    })
                    
                    # Push chunk
                    push_message(
                        AIMessageChunk(id=stream_anchor.id, content=answer),
                        state_key="messages",
                    )
                    await asyncio.sleep(0)

            elif ev.node_name == "final_answer":
                _update_intent_ui({
                     "rag_status": "done", # or keep running until very end?
                     "rag_message": "Processing: final_answer"
                })
                break
                
    except (httpx.ConnectError, httpx.ConnectTimeout):
        friendly = "RAG 服务连接失败，请检查 RAG_API_URL 配置或网络是否可达。"
        _update_intent_ui({"rag_status": "error", "rag_message": friendly})
        stream_anchor.content = friendly
        push_message(stream_anchor, state_key="messages")
        return state
    except Exception as exc:
        _update_intent_ui({
            "rag_status": "error",
            "rag_message": str(exc),
        })
        raise

    # 如果没有获取到答案，使用默认提示
    if not answer_parts:
        logger.warning(f"[RAG] 未收到有效答案片段，共处理 {ev_count} 个 SSE 事件")
        answer_text = "抱歉，未能从知识库获取到相关答案。"
        stream_anchor.content = answer_text
        _update_intent_ui({
            "rag_status": "done",
            "rag_message": "未找到相关答案。",
        })
        return state

    answer_text = "".join(answer_parts)
    stream_anchor.content = answer_text
    
    # Final completion update
    _update_intent_ui({
        "rag_status": "done",
        "rag_message": "Relevant context retrieved",
        "hidden": True,
    })
    # Clear intent UI ids so downstream nodes won't re-show the card
    state["intent_ui_id"] = None
    state["intent_anchor_id"] = None
    
    return state

                                                                                                                                                                                                           
