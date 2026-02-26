"""配置常量模块。

集中管理所有配置项，支持环境变量覆盖。
"""

import logging
import os

# ============ LangGraph Cloud 配置 ============

ARTICLE_WORKFLOW_URL = os.getenv(
    "ARTICLE_WORKFLOW_URL",
)

ARTICLE_WORKFLOW_API_KEY = os.getenv("ARTICLE_WORKFLOW_API_KEY") or os.getenv(
    "LANGCHAIN_API_KEY",
)

ARTICLE_ASSISTANT_ID = os.getenv("ARTICLE_ASSISTANT_ID", "multiple_graph")


# ============ LLM 配置 ============

LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")
LLM_NANO_MODEL = os.getenv("LLM_NANO_MODEL", "gpt-4.1-nano")


# ============ MCP 配置 ============
# 注：MCP 工具列表现在通过 tools/list 从 MCP Server 动态获取，不再硬编码
MCP_SITE_SETTING_BASIC_URL = os.getenv(
    "MCP_SITE_SETTING_BASIC_URL"
)

GA_MCP_URL = os.getenv(
    "GA_MCP_URL",
    "http://127.0.0.1:8001/mcp",
)

MCP_LOWCODE_APP_URL = os.getenv(
    "MCP_LOWCODE_APP_URL",
    "/api/mcp/lowcode-app",
)


# ============ RAG API 配置 ============
RAG_API_URL = os.getenv(
    "RAG_API_URL",
    "https://ai-chatbot-dev.cedemo.cn/ai/rag/kb/v1/chatbot-stream",
)
RAG_TENANT_ID = os.getenv("RAG_TENANT_ID", "help-center")
RAG_SITE_ID = os.getenv("RAG_SITE_ID", "help-center")


# ============ 网关和授权配置 ============
GATEWAY_URL = os.getenv("GATEWAY_URL")
AUTHORIZATION_API_URL = os.getenv("AUTHORIZATION_API_URL")
AUTHORIZATION_CLIENT_ID = os.getenv("AUTHORIZATION_CLIENT_ID")
AUTHORIZATION_CLIENT_SECRET = os.getenv("AUTHORIZATION_CLIENT_SECRET")


# ============ 日志配置 ============
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
# 可通过环境变量覆盖：LOG_LEVEL=DEBUG
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()


_logging_configured = False


def setup_logging(level: str | None = None) -> None:
    """配置日志系统。

    Args:
        level: 日志级别，如果不提供则使用 LOG_LEVEL 配置
    """
    global _logging_configured
    log_level = (level or LOG_LEVEL).upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger().setLevel(numeric_level)
    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """获取 logger，首次调用时按 LOG_LEVEL 初始化日志配置。"""
    global _logging_configured
    if not _logging_configured:
        setup_logging()
    return logging.getLogger(name)


# ============ Article（前端澄清 UI）配置 ============
def _csv_list(v: str) -> list[str]:
    return [x.strip() for x in (v or "").split(",") if x.strip()]


# Content style（用于前端澄清 UI 的下拉选项，可按需修改）
# 也可用环境变量覆盖：ARTICLE_CONTENT_STYLE_OPTIONS="Professional,活泼,严谨"
ARTICLE_CONTENT_STYLE_OPTIONS: list[str] = _csv_list(
    os.getenv(
        "ARTICLE_CONTENT_STYLE_OPTIONS",
        "Professional, Colloquial, Relaxed, Readability, Reserved, Neutrally",
    )
)
