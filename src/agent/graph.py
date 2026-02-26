"""主图构建模块。

只负责组装各模块，不包含具体业务逻辑。
"""

from langgraph.graph import END, START, StateGraph

from agent.config import get_logger
from agent.nodes.article import handle_article, start_article_ui
from agent.nodes.entry import entry_node
from agent.nodes.introduction import handle_introduction
from agent.nodes.rag import handle_rag, start_rag_ui
from agent.nodes.report import start_report_ui
from agent.nodes.router import route_intent, start_intent_ui
from agent.nodes.seo import handle_seo, start_seo_ui
from agent.nodes.shortcut import start_shortcut_ui
from agent.state import CopilotState
from agent.subgraphs.article import build_article_subgraph
from agent.subgraphs.report import build_report_subgraph
from agent.subgraphs.shortcut import build_shortcut_subgraph

logger = get_logger(__name__)


def build_graph():
    """构建主图，使用条件边连接所有节点。"""
    builder = StateGraph(CopilotState)

    # ============ 添加节点 ============
    builder.add_node("entry", entry_node)
    builder.add_node("router_ui", start_intent_ui)
    builder.add_node("router", route_intent)
    builder.add_node("rag_ui", start_rag_ui)
    builder.add_node("rag", handle_rag)
    builder.add_node("introduction", handle_introduction)
    builder.add_node("seo_ui", start_seo_ui)
    builder.add_node("seo", handle_seo)
    builder.add_node("report_ui", start_report_ui)

    # Article 子图（只负责澄清）
    article_subgraph = build_article_subgraph()
    builder.add_node("article_clarify", article_subgraph)
    # Article Workflow UI 和 Run 放在主图，确保 stream 即时性
    builder.add_node("article_ui", start_article_ui)
    builder.add_node("article_run", handle_article)

    # Shortcut 子图
    shortcut_subgraph = build_shortcut_subgraph()
    builder.add_node("shortcut_ui", start_shortcut_ui)
    builder.add_node("shortcut", shortcut_subgraph)

    # Report 子图
    report_subgraph = build_report_subgraph()
    builder.add_node("report", report_subgraph)

    # ============ 定义边 ============

    # 从 START 进入 entry
    builder.add_edge(START, "entry")

    # entry 后的条件边：根据 resume_target 决定跳转
    def _entry_route(state: CopilotState):
        target = state.get("resume_target") or "router_ui"
        logger.debug("[DEBUG] _entry_route: target = %s", target)
        return target

    builder.add_conditional_edges(
        "entry",
        _entry_route,
        {
            "router_ui": "router_ui",
            "shortcut": "shortcut",
            "shortcut_ui": "shortcut_ui",
            "seo_ui": "seo_ui",
            "article_clarify": "article_clarify",
            "article_ui": "article_ui",
            "article_run": "article_run",
            "report_ui": "report_ui",
            "report": "report",
            "rag": "rag_ui",
            "rag_ui": "rag_ui",
        },
    )

    builder.add_edge("router_ui", "router")

    # router 后的条件边：根据 intent 分流
    def _route(state: CopilotState):
        intent = state.get("intent") or "rag"
        if intent == "article_task":
            return "article_task"
        if intent == "shortcut":
            return "shortcut"
        if intent == "seo_planning":
            return "seo_planning"
        if intent == "site_report":
            return "site_report"
        if intent == "introduction":
            return "introduction"
        return "rag"

    builder.add_conditional_edges(
        "router",
        _route,
        {
            "rag": "rag_ui",
            "article_task": "article_clarify",
            "shortcut": "shortcut_ui",
            "seo_planning": "seo_ui",
            "site_report": "report_ui",
            "introduction": "introduction",
        },
    )

    builder.add_edge("rag_ui", "rag")
    builder.add_edge("rag", END)
    builder.add_edge("introduction", END)
    
    # Article: clarify -> (check pending) -> ui/END
    def _after_article_clarify(state: CopilotState):
        # 如果还在澄清中（pending=True），说明本轮结束，等待用户输入 -> END
        if state.get("article_clarify_pending"):
            return END
        # 如果参数齐了，继续去跑 workflow UI -> RUN
        return "article_ui"

    builder.add_conditional_edges(
        "article_clarify",
        _after_article_clarify,
        {END: END, "article_ui": "article_ui"}
    )
    
    builder.add_edge("article_ui", "article_run")
    builder.add_edge("article_run", END)

    builder.add_edge("seo_ui", "seo")
    builder.add_edge("seo", END)
    builder.add_edge("report_ui", "report")
    builder.add_edge("report", END)
    builder.add_edge("shortcut_ui", "shortcut")
    builder.add_edge("shortcut", END)
    # from langgraph.checkpoint.memory import MemorySaver
    # return builder.compile(checkpointer=MemorySaver())
    return builder.compile()


# 导出编译后的 graph
graph = build_graph()
