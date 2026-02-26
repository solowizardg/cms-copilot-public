"""从 LangGraph 运行配置中提取并构建请求头（run_id、thread_id、站点信息等）。"""

from typing import Any, Dict

from langgraph.config import get_config


def get_extra_headers() -> Dict[str, Any]:
    """从 LangGraph 运行配置中提取 run_id、thread_id 及站点相关 header 信息。"""
    config = get_config()
    run_id = config['metadata']['run_id']
    thread_id = config['metadata']['thread_id']

    user_config = config["configurable"].get("langgraph_auth_user")
    site_id=user_config.get("site_id") if user_config.get("site_id") else ""
    tenant_id=user_config.get("tenant_id") if user_config.get("tenant_id") else ""
    site_url=user_config.get("site_url") if user_config.get("site_url") else ""
    property_id=user_config.get("property_id") if user_config.get("property_id") else ""

    extra_headers = {
        "run_id": run_id,
        "thread_id": thread_id,
        "site_id": site_id,
        "tenant_id": tenant_id,
        "site_url": site_url,
        "property_id": property_id,
    }
    return extra_headers
