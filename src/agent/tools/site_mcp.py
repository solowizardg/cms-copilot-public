"""MCP Client 模块 — 使用 langchain-mcp-adapters。

基于官方 langchain-mcp-adapters 库连接 MCP Server：
- 自动处理 initialize → notifications/initialized → tools/list
- 自动将 MCP 的 JSON Schema 转换为 LangChain Tool
- 返回的 tools 可直接用于 llm.bind_tools()
"""

from __future__ import annotations

import inspect
import json
import os
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from agent.config import (
    GATEWAY_URL,
    MCP_LOWCODE_APP_URL,
    MCP_SITE_SETTING_BASIC_URL,
    get_logger,
)
from agent.tools.mcp_utils import (
    extract_mcp_error_message,
    get_mcp_is_error,
    get_mcp_structured_content,
    is_mcp_debug_enabled,
    patch_mcp_streamable_http_bom,
)

logger = get_logger(__name__)


def is_mcp_error_result(raw_result: Any) -> tuple[bool, str]:
    """判断 MCP 工具返回是否为错误（isError=True 或 structuredContent 中含 errorCode）。

    仅做通用错误判断，不区分 token 刷新失败等具体错误码。
    返回 (True, message) 表示错误；(False, "") 表示非错误。
    """
    if raw_result is None:
        if is_mcp_debug_enabled():
            logger.debug(f"[MCP][is_error] raw_result 为 None")
        return False, ""
    
    structured = get_mcp_structured_content(raw_result)
    
    if is_mcp_debug_enabled():
        logger.debug(f"[MCP][is_error] raw_result type={type(raw_result).__name__}, has_structured={structured is not None}")
        if isinstance(structured, dict):
            logger.debug(f"[MCP][is_error] structured keys={list(structured.keys())}, errorCode={structured.get('errorCode')}")
    
    if isinstance(structured, dict) and structured.get("errorCode"):
        msg = extract_mcp_error_message(raw_result, structured)
        logger.warning(f"[MCP][is_error] 检测到 errorCode: {structured.get('errorCode')}, message: {msg}")
        return True, msg
    
    if get_mcp_is_error(raw_result):
        msg = extract_mcp_error_message(raw_result, structured)
        logger.warning(f"[MCP][is_error] isError=True, message: {msg}")
        return True, msg
    
    if is_mcp_debug_enabled():
        logger.debug(f"[MCP][is_error] 未检测到错误")
    return False, ""


def _create_mcp_client(
    site_id: str,
    tenant_id: str | None = None,
    intent: str | None = None,
    token: str | None = None,
) -> MultiServerMCPClient:
    """创建 MCP Client 实例。

    Args:
        tenant_id: 租户 ID
        site_id: 站点 ID（UUID）
        intent: 意图
    Returns:
        MultiServerMCPClient 实例
    """
    patch_mcp_streamable_http_bom()
    headers = {"X-Site-Id": site_id}
    logger.info(f"_create_mcp_client  site_id: {site_id} tenant_id: {tenant_id} intent: {intent}")
    if tenant_id:
        headers["X-Tenant-Id"] = tenant_id

    if token:
        headers["Authorization"] = f"Bearer {token}"

    # 重要：根据意图选择 MCP server
    # - shortcut: 只允许 site-setting-basic
    # - article_task: 只允许 lowcode-app
    # - 其他/未知: 默认全部启用（向后兼容）
    normalized_intent = (intent or "").strip().lower() or None
    servers: dict[str, dict[str, Any]] = {}

    def _enable_site_setting_basic() -> None:
        if MCP_SITE_SETTING_BASIC_URL:
            url = f"{GATEWAY_URL}{MCP_SITE_SETTING_BASIC_URL}"
            logger.info(f"MCP_SITE_SETTING_BASIC_URL url: {url}")
            servers["site-setting-basic"] = {
                "url": url,
                "transport": "streamable_http",  # langchain_mcp_adapters 将 http 和 streamable_http 视为同一种 transport
                "headers": headers,
            }

    def _enable_lowcode_app() -> None:
        if MCP_LOWCODE_APP_URL:
            url = f"{GATEWAY_URL}{MCP_LOWCODE_APP_URL}"
            logger.info(f"MCP_LOWCODE_APP_URL url: {url}")
            servers["lowcode-app"] = {
                "url": url,
                "transport": "streamable_http",  # langchain_mcp_adapters 将 http 和 streamable_http 视为同一种 transport
                "headers": headers,
            }

    if normalized_intent == "shortcut":
        _enable_site_setting_basic()
    elif normalized_intent == "article_task":
        _enable_lowcode_app()
    else:
        _enable_site_setting_basic()
        _enable_lowcode_app()

    logger.info(f"[MCP][_create_mcp_client] intent={normalized_intent}, 启用的服务器: {list(servers.keys())}")
    if is_mcp_debug_enabled():
        for server_name, server_config in servers.items():
            logger.info(f"[MCP][_create_mcp_client]   - {server_name}: url={server_config.get('url')}, transport={server_config.get('transport')}")
        logger.info(f"[MCP][_create_mcp_client] headers={headers}")

    try:
        client = MultiServerMCPClient(servers)
        logger.info(f"[MCP][_create_mcp_client] MultiServerMCPClient 创建成功")
        return client
    except Exception as e:
        logger.error(f"[MCP][_create_mcp_client] 创建 MCP client 失败: {type(e).__name__}: {e}", exc_info=True)
        raise


async def get_mcp_tools(
    site_id: str,
    tenant_id: str | None = None,
    intent: str | None = None,
    token: str | None = None,
) -> list[Any]:
    """获取 MCP Server 提供的工具列表（LangChain Tool 格式）。

    Args:
        site_id: 站点 ID
        tenant_id: 租户 ID
        intent: 意图类型
        token: MCP 访问令牌

    Returns:
        LangChain Tool 列表，可直接用于 llm.bind_tools()
    """
    logger.info(f"[MCP][get_mcp_tools] 开始获取工具列表 site_id={site_id}, tenant_id={tenant_id}, intent={intent}, has_token={token is not None}")
    try:
        client = _create_mcp_client(tenant_id=tenant_id, site_id=site_id, intent=intent, token=token)
        logger.info(f"[MCP][get_mcp_tools] MCP client 创建成功")
        
        tools = client.get_tools()
        if inspect.isawaitable(tools):
            tools = await tools

        logger.info(f"[MCP][get_mcp_tools] 成功获取 {len(tools)} 个工具")
        if is_mcp_debug_enabled():
            for tool in tools:
                desc = tool.description[:50] if tool.description else ""
                logger.info(f"[MCP][get_mcp_tools]   - {tool.name}: {desc}...")

        return tools
    except Exception as e:
        logger.error(f"[MCP][get_mcp_tools] 获取工具列表失败: {type(e).__name__}: {e}", exc_info=True)
        raise


async def call_mcp_tool(
    site_id: str,
    tool_name: str,
    tool_input: dict[str, Any],
    tenant_id: str | None = None,
    intent: str | None = None,
    token: str | None = None,
) -> Any:
    """调用 MCP 工具。

    Args:
        tool_name: 工具名称（如 get_basic_detail、save_basic_detail）
        tool_input: 工具输入参数
        tenant_id: 租户 ID
        site_id: 站点 ID

    Returns:
        工具执行结果
    """
    logger.info(f"[MCP][call_mcp_tool] 开始调用 tool={tool_name!r}, site_id={site_id}, tenant_id={tenant_id}, intent={intent}")
    if is_mcp_debug_enabled():
        logger.info(f"[MCP][call_mcp_tool] input={tool_input!r}")

    try:
        client = _create_mcp_client(tenant_id=tenant_id, site_id=site_id, intent=intent, token=token)
        tools = client.get_tools()
        if inspect.isawaitable(tools):
            tools = await tools

        logger.info(f"[MCP][call_mcp_tool] 获取到 {len(tools)} 个工具: {[t.name for t in tools]}")

        # 找到对应的工具
        target_tool = None
        for tool in tools:
            if tool.name == tool_name:
                target_tool = tool
                break

        if not target_tool:
            error_msg = f"未找到工具: {tool_name}, 可用工具: {[t.name for t in tools]}"
            logger.error(f"[MCP][call_mcp_tool] {error_msg}")
            return {"success": False, "error": error_msg}

        # 调用工具
        logger.info(f"[MCP][call_mcp_tool] 正在调用工具 {tool_name}...")
        
        try:
            result = await target_tool.ainvoke(tool_input)
            
            # 详细记录返回结果
            logger.info(f"[MCP][call_mcp_tool] 工具调用完成, result type={type(result).__name__}")
            if is_mcp_debug_enabled():
                logger.info(f"[MCP][call_mcp_tool] 完整返回: {result!r}")
            
            # 检查是否是错误结果
            is_error, error_msg = is_mcp_error_result(result)
            if is_error:
                logger.error(f"[MCP][call_mcp_tool] 工具返回错误: {error_msg}")
            else:
                logger.info(f"[MCP][call_mcp_tool] 工具调用成功")

            return result
            
        except Exception as tool_error:
            # langchain_mcp_adapters 会在 MCP 返回 isError=True 时抛出 ToolException
            from langchain_core.tools.base import ToolException
            
            if isinstance(tool_error, ToolException):
                error_msg = str(tool_error)
                logger.error(f"[MCP][call_mcp_tool] MCP 工具返回错误")
                logger.error(f"[MCP][call_mcp_tool] 错误消息: {error_msg}")
                logger.error(f"[MCP][call_mcp_tool] 工具名: {tool_name}")
                logger.error(f"[MCP][call_mcp_tool] 输入参数: {json.dumps(tool_input, ensure_ascii=False, indent=2)}")
                
                # 返回包含错误信息的字典，这样上层可以显示在页面上
                return {
                    "success": False,
                    "error": error_msg,
                    "tool_name": tool_name,
                    "isError": True
                }
            else:
                # 其他异常
                logger.error(f"[MCP][call_mcp_tool] 工具调用异常: {type(tool_error).__name__}: {tool_error}", exc_info=True)
                return {
                    "success": False,
                    "error": f"工具调用异常: {str(tool_error)}",
                    "tool_name": tool_name
                }

    except Exception as e:
        logger.error(f"[MCP][call_mcp_tool] 调用失败: {type(e).__name__}: {e}", exc_info=True)
        return {"success": False, "error": f"MCP 调用失败: {str(e)}"}


