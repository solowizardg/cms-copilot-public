"""SEO 规划节点模块。

SEO 周任务规划的节点函数。
调用接口获取周任务列表，不使用 LLM。
"""

import uuid
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.config import get_stream_writer
from langgraph.graph.ui import push_ui_message

from agent.state import CopilotState
from agent.tools.seo import (
    WeeklyTasksResponse,
    fetch_weekly_tasks,
    get_mock_request_body,
)
from agent.utils.helpers import latest_user_message, message_text
from agent.config import get_logger

logger = get_logger(__name__)

# ============ 主图节点 ============


async def start_seo_ui(state: CopilotState) -> dict[str, Any]:
    """创建 SEO 规划的 UI 锚点和初始卡片（loading 状态）。"""
    user_msg = latest_user_message(state)
    user_text = message_text(user_msg)

    # 隐藏 "Thinking Completed" 卡片
    writer = get_stream_writer()
    intent_ui_id = state.get("intent_ui_id")
    intent_anchor_id = state.get("intent_anchor_id")
    
    if intent_ui_id and intent_anchor_id:
        # 需要额外引用 find_ai_message_by_id，将在 import 中添加
        from agent.utils.helpers import find_ai_message_by_id
        intent_anchor_msg = find_ai_message_by_id(state, intent_anchor_id)
        if intent_anchor_msg:
            hide_msg = push_ui_message(
                "intent_router",
                {"status": "done", "hidden": True},
                id=intent_ui_id,
                message=intent_anchor_msg,
                merge=True
            )
            if writer:
                 writer(hide_msg)

    # 创建 AIMessage 锚点
    ui_anchor_msg = AIMessage(id=str(uuid.uuid4()), content="")

    # 创建初始 UI 卡片
    ui_msg_start = push_ui_message(
        "seo_planner",
        {
            "status": "loading",
            "step": "initializing",
            "user_text": user_text,
            "steps": [
                "Fetching weekly task data",
                "Processing task list",
                "Done",
            ],
            "active_step": 1,
            "weekly_tasks": None,
            "error_message": None,
        },
        message=ui_anchor_msg,
    )

    return {
        "messages": [ui_anchor_msg],
        "ui": [ui_msg_start],
        "seo_ui_id": ui_msg_start["id"],
        "seo_anchor_id": ui_anchor_msg.id,
        "intent_ui_id": intent_ui_id,
        "intent_anchor_id": intent_anchor_id,
    }


async def handle_seo(state: CopilotState) -> dict[str, Any]:
    """处理 SEO 规划：调用接口获取周任务列表。"""
    writer = get_stream_writer()

    user_msg = latest_user_message(state)
    user_text = message_text(user_msg)
    site_id = state.get("site_id") or "site-001"
    tenant_id = state.get("tenant_id")
    site_url = state.get("site_url")
    token = state.get("token")

    # 获取 UI 锚点
    ui_id = state.get("seo_ui_id")
    anchor_id = state.get("seo_anchor_id")
    anchor_msg = None
    if anchor_id:
        for m in state.get("messages", []):
            if isinstance(m, AIMessage) and getattr(m, "id", None) == anchor_id:
                anchor_msg = m
                break

    if anchor_msg is None:
        anchor_msg = AIMessage(id=str(uuid.uuid4()), content="")

    def _push_ui(props: dict[str, Any]):
        """推送 UI 更新"""
        ui_msg = push_ui_message(
            "seo_planner",
            props,
            id=ui_id,
            message=anchor_msg,
            merge=True,
        )
        if writer is not None:
            writer(ui_msg)
        return ui_msg

    # Step 1: 获取周任务数据
    _push_ui(
        {
            "status": "loading",
            "step": "fetching_tasks",
            "steps": ["Fetching weekly task data", "Processing task list", "Done"],
            "active_step": 1,
            "weekly_tasks": None,
            "error_message": None,
        }
    )

    try:
        logger.info(f"[SEO][handle_seo] 开始获取周任务，site_id={site_id}, tenant_id={tenant_id}")

        # 使用完整的 Mock 请求体数据
        request_body = get_mock_request_body(
            tenant_id=tenant_id or "t_demo_001",
            site_id=site_id,
            site_url=site_url or "https://demo-xsite.ai",
        )

        # 调用真实接口
        tasks_response = await fetch_weekly_tasks(
            site_id=site_id,
            tenant_id=tenant_id,
            site_url=site_url,
            token=token,
            request_body=request_body,
        )

        logger.info(f"[SEO][handle_seo] 获取到 {len(tasks_response.data.tasks)} 条任务")

        # Step 2: 处理任务列表
        _push_ui(
            {
                "status": "loading",
                "step": "processing",
                "steps": ["Fetching weekly task data", "Processing task list", "Done"],
                "active_step": 2,
                "weekly_tasks": None,
                "error_message": None,
            }
        )

        # 转换为 dict 格式供前端使用
        weekly_tasks_data = {
            "schema_version": tasks_response.data.schema_version,
            "meta": {
                "tenant_id": tasks_response.data.meta.tenant_id,
                "site_id": tasks_response.data.meta.site_id,
                "week_start": tasks_response.data.meta.week_start,
                "timezone": tasks_response.data.meta.timezone,
                "run_id": tasks_response.data.meta.run_id,
            },
            "tasks": [
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "priority": task.priority,
                    "title": task.title,
                    "prompt": task.prompt,
                }
                for task in tasks_response.data.tasks
            ],
        }

        error_message = None

    except Exception as e:
        logger.error(f"[SEO][handle_seo] 获取周任务失败: {e}", exc_info=True)
        weekly_tasks_data = None
        error_message = f"Failed to fetch weekly tasks: {str(e)}"

    # Step 3: 完成
    final_ui_msg = _push_ui(
        {
            "status": "done" if not error_message else "error",
            "step": "completed",
            "steps": ["Fetching weekly task data", "Processing task list", "Done"],
            "active_step": 3,
            "weekly_tasks": weekly_tasks_data,
            "progress": f"{len(weekly_tasks_data['tasks'])} tasks generated" if weekly_tasks_data else None,
            "error_message": error_message,
        }
    )

    return {
        "ui": [final_ui_msg],
    }
