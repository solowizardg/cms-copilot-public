"""节点函数模块。"""

from agent.nodes.article import handle_article, start_article_ui
from agent.nodes.entry import entry_node
from agent.nodes.rag import handle_rag, start_rag_ui
from agent.nodes.report import (
    report_execute_tool,
    report_init,
    report_finalize,
    start_report_ui,
)
from agent.nodes.router import route_intent, start_intent_ui
from agent.nodes.seo import handle_seo, start_seo_ui
from agent.nodes.shortcut import (
    start_shortcut_ui,
    shortcut_confirm_step,
    shortcut_execute_step,
    shortcut_finalize,
    shortcut_init,
    shortcut_plan,
    shortcut_prepare_step,
)

__all__ = [
    "entry_node",
    "start_intent_ui",
    "route_intent",
    "start_rag_ui",
    "handle_rag",
    "start_article_ui",
    "handle_article",
    "start_seo_ui",
    "handle_seo",
    "start_report_ui",
    "report_init",
    "report_execute_tool",
    "report_finalize",
    "start_shortcut_ui",
    "shortcut_init",
    "shortcut_plan",
    "shortcut_prepare_step",
    "shortcut_confirm_step",
    "shortcut_execute_step",
    "shortcut_finalize",
]
