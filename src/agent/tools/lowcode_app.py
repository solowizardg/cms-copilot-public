"""低代码应用工具模块。

提供低代码应用列表获取等功能。
"""

from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel

from .site_mcp import call_mcp_tool

# ============ Pydantic 模型定义 ============


class App(BaseModel):
    """应用模型"""

    id: int
    name: str
    slug: str
    description: str
    icon: str
    status: str
    type: str
    version: str
    site_id: str
    default_model_id: int | None = None
    created_at: datetime
    updated_at: datetime


class AppListData(BaseModel):
    """应用列表数据模型"""

    list: list[App]
    total: int
    page: int
    page_size: int
    total_pages: int


class AppListResponse(BaseModel):
    """应用列表响应模型"""

    success: bool
    message: str
    data: AppListData


# ============ 工具函数 ============


async def list_apps(
    site_id: str,
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    tenant_id: str | None = None,
    token: str | None = None,
) -> AppListResponse:
    """获取应用列表。

    Args:
        page: 页码，从 1 开始
        page_size: 每页大小
        keyword: 搜索关键词
        tenant_id: 租户 ID
        site_id: 站点 ID

    Returns:
        应用列表响应模型
    """
    result = await call_mcp_tool(
        site_id=site_id,
        tool_name="list_apps",
        tool_input={"page": page, "page_size": page_size, "keyword": keyword},
        tenant_id=tenant_id,
        intent="article_task",
        token=token,
    )

    # 解析 MCP 返回的数据
    if result and isinstance(result, list) and len(result) > 0:
        # 获取 text 字段中的 JSON 字符串
        text_content = result[0].get("text", "")
        if text_content:
            # 解析 JSON 并序列化为模型
            json_data = json.loads(text_content)
            return AppListResponse(**json_data)

    # 如果解析失败，返回错误响应
    return AppListResponse(
        success=False,
        message="解析 MCP 返回数据失败",
        data=AppListData(list=[], total=0, page=page, page_size=page_size, total_pages=0),
    )
