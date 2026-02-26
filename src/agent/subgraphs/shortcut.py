"""Shortcut 子图模块（v2：Plan → Execute）。"""

from langgraph.graph import END, START, StateGraph

from agent.config import get_logger
from agent.nodes.shortcut import (
    shortcut_confirm_step,
    shortcut_execute_step,
    shortcut_finalize,
    shortcut_init,
    shortcut_plan,
    shortcut_prepare_step,
)
from agent.state import ShortcutState

logger = get_logger(__name__)


def build_shortcut_subgraph():
    """构建 Shortcut 子图（v2：多步、按风险确认、循环执行）。"""
    builder = StateGraph(ShortcutState)

    builder.add_node("init", shortcut_init)
    builder.add_node("plan", shortcut_plan)
    builder.add_node("prepare_step", shortcut_prepare_step)
    builder.add_node("confirm_step", shortcut_confirm_step)
    builder.add_node("execute_step", shortcut_execute_step)
    builder.add_node("finalize", shortcut_finalize)

    builder.add_edge(START, "init")

    def _after_init(state: ShortcutState):
        if state.get("error"):
            return "finalize"
        return "plan"

    builder.add_conditional_edges("init", _after_init, {"plan": "plan", "finalize": "finalize"})

    def _after_plan(state: ShortcutState):
        if state.get("error") or state.get("cancelled"):
            return "finalize"
        # 如果是能力询问，直接结束
        if state.get("is_capability_inquiry"):
            return "finalize"
        # 如果需要用户补充参数，直接结束（已返回提示消息）
        needs_params = state.get("needs_params")
        if needs_params:
            logger.debug("[Shortcut] _after_plan: needs_params=%s, returning 'finalize'", needs_params)
            return "finalize"
        steps = state.get("plan_steps") or []
        return "finalize" if not steps else "prepare_step"

    builder.add_conditional_edges(
        "plan",
        _after_plan,
        {"prepare_step": "prepare_step", "finalize": "finalize"},
    )

    builder.add_edge("prepare_step", "confirm_step")
    builder.add_edge("confirm_step", "execute_step")

    def _after_execute(state: ShortcutState):
        if state.get("error") or state.get("cancelled"):
            return "finalize"
        steps = state.get("plan_steps") or []
        idx = int(state.get("current_step_idx") or 0)
        if idx >= len(steps):
            return "finalize"
        return "prepare_step"

    builder.add_conditional_edges(
        "execute_step",
        _after_execute,
        {"prepare_step": "prepare_step", "finalize": "finalize"},
    )

    builder.add_edge("finalize", END)

    return builder.compile()
