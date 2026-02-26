"""Report 子图模块（ReAct：AI 规划多步 MCP 工具调用）。"""

from langgraph.graph import END, START, StateGraph

from agent.nodes.report import (
    report_build_evidence,
    report_capability_response,
    report_execute_tool,
    report_generate_insights_start,
    report_generate_insights_run,
    report_init,
    report_finalize,
    report_ask_insights,
)
from agent.state import ReportState


def build_report_subgraph_v1():
    """构建 Report 子图（v1：仅取数+图表）。

    旧逻辑保留做 fallback / 对比。
    """
    builder = StateGraph(ReportState)

    builder.add_node("init", report_init)
    builder.add_node("execute", report_execute_tool)
    builder.add_node("finalize", report_finalize)

    builder.add_edge(START, "init")
    builder.add_edge("init", "execute")
    builder.add_edge("execute", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()


def build_report_subgraph():
    """构建 Report 子图（v2：取数 -> EvidencePack -> 洞察/Todo -> 渲染）。

    流程：
    - init -> (capability_inquiry?) -> capability_response -> END
    - init -> execute -> analyze -> ask_insights -> insights -> finalize -> END
    """
    builder = StateGraph(ReportState)

    builder.add_node("init", report_init)
    builder.add_node("capability_response", report_capability_response)
    builder.add_node("execute", report_execute_tool)
    builder.add_node("analyze", report_build_evidence)
    builder.add_node("ask_insights", report_ask_insights)
    builder.add_node("insights_start", report_generate_insights_start)
    builder.add_node("insights_run", report_generate_insights_run)
    builder.add_node("finalize", report_finalize)

    builder.add_edge(START, "init")
    
    # init 后判断：能力询问 → capability_response，工具为空 → finalize，否则 → execute
    def _after_init(state: ReportState):
        # 洞察恢复模式：跳过 execute/analyze/ask，直接进入洞察或结束
        if state.get("report_resume_mode") == "insights":
            return "insights_start" if state.get("insights_confirmed") else "finalize"
        if state.get("is_capability_inquiry"):
            return "capability_response"
        if state.get("tool_error"):
            return "finalize"
        return "execute"
    
    builder.add_conditional_edges(
        "init",
        _after_init,
        {
            "capability_response": "capability_response",
            "finalize": "finalize",
            "execute": "execute",
            "insights_start": "insights_start",
        },
    )
    
    # 能力询问直接结束
    builder.add_edge("capability_response", END)
    
    # execute 失败（如 planning_failed）时直接 finalize，避免后续节点继续跑导致空数据/覆盖
    def _after_execute(state: ReportState):
        return "finalize" if state.get("tool_error") else "analyze"

    builder.add_conditional_edges(
        "execute",
        _after_execute,
        {"analyze": "analyze", "finalize": "finalize"},
    )
    builder.add_edge("analyze", "ask_insights")

    # ask_insights 后判断：未确认（pending）→ END；确认继续 → insights_start；否则 → finalize
    def _after_ask(state: ReportState):
        if state.get("report_insights_pending") and state.get("insights_confirmed") is None:
            return END
        return "insights_start" if state.get("insights_confirmed") else "finalize"

    builder.add_conditional_edges(
        "ask_insights",
        _after_ask,
        {"insights_start": "insights_start", "finalize": "finalize", END: END},
    )

    builder.add_edge("insights_start", "insights_run")
    builder.add_edge("insights_run", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()

