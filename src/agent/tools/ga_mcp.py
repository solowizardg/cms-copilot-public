"""GA MCP 工具封装（仅用于 Report）。

约束：
- Report 只能使用 GA MCP：GA_MCP_URL
- Shortcut 只能使用 site-setting-basic（见 `src/agent/tools/mcp.py`）
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from agent.config import GA_MCP_URL, LLM_API_KEY, get_logger
from agent.tools.mcp_utils import (
    ensure_langchain_globals,
    extract_mcp_error_message,
    get_mcp_is_error,
    get_mcp_structured_content,
    normalize_mcp_json_result,
)

logger = get_logger(__name__)

# 与 analytics_mcp 服务端一致，供调用方判断 token 刷新失败并引导重新 OAuth
ERROR_CODE_TOKEN_REFRESH_FAILED = "TOKEN_REFRESH_FAILED"


def is_token_expired_error(error_message: str) -> bool:
    """检查错误消息是否表示 token 过期。
    
    匹配模式：
    - "invalid_grant" + ("token has been expired or revoked" 或 "token" + "expired" 或 "token" + "revoked")
    
    示例错误：
    - "503 Getting metadata from plugin failed with error: ('invalid_grant: Token has been expired or revoked.'"
    """
    error_msg_lower = error_message.lower()
    return (
        "invalid_grant" in error_msg_lower and 
        ("token has been expired or revoked" in error_msg_lower or 
         "token" in error_msg_lower and "expired" in error_msg_lower or
         "token" in error_msg_lower and "revoked" in error_msg_lower)
    )


def check_ga_tool_error(raw_result: Any) -> tuple[bool, str, bool]:
    """统一判断 GA MCP 工具返回是否为错误（含 token 过期与一般错误）。

    返回 (is_error, message, is_auth_error)：
    - 无错误：(False, "", False)
    - token 刷新失败（需重新 OAuth）：(True, message, True)
    - 其它错误：(True, message, False)
    调用方可根据 is_auth_error 决定展示「重新授权」或「一般错误」提示。
    """
    if raw_result is None:
        return False, "", False
    
    # 优先检查：call_ga_tool 返回的错误字典格式
    if isinstance(raw_result, dict):
        # 检查 errorCode（来自我们在 call_ga_tool 中添加的字段）
        error_code = raw_result.get("errorCode")
        if error_code == ERROR_CODE_TOKEN_REFRESH_FAILED:
            msg = raw_result.get("error") or "Google 账号授权已过期"
            logger.warning(f"[GA_MCP][check_error] 检测到 TOKEN_REFRESH_FAILED: {msg}")
            return True, msg, True
        
        # 检查 isError 标志
        if raw_result.get("isError") or raw_result.get("is_error"):
            msg = raw_result.get("error") or extract_mcp_error_message(raw_result)
            logger.warning(f"[GA_MCP][check_error] 检测到错误: {msg}")
            return True, msg, False
    
    # 原有逻辑：检查 MCP 原始响应格式（如果没有被 ToolException 拦截）
    structured = get_mcp_structured_content(raw_result)
    error_code = isinstance(structured, dict) and structured.get("errorCode") or None
    if error_code == ERROR_CODE_TOKEN_REFRESH_FAILED:
        msg = extract_mcp_error_message(raw_result, structured)
        logger.warning(f"[GA_MCP][check_error] 检测到 TOKEN_REFRESH_FAILED (原始响应): {msg}")
        return True, msg or "Google 账号授权已过期", True
    if isinstance(structured, dict) and error_code:
        msg = extract_mcp_error_message(raw_result, structured)
        logger.warning(f"[GA_MCP][check_error] 检测到错误码 (原始响应): {error_code}, {msg}")
        return True, msg, False
    if get_mcp_is_error(raw_result):
        msg = extract_mcp_error_message(raw_result, structured)
        logger.warning(f"[GA_MCP][check_error] 检测到 isError (原始响应): {msg}")
        return True, msg, False
    
    return False, "", False


def _ga_headers(site_id: str , tenant_id: str | None) -> dict[str, str]:
    headers: dict[str, str] = {
        "Accept": "application/json, text/event-stream",
        "X-Site-Id": site_id,
        "Authorization": f"Bearer {LLM_API_KEY}",
        "X-Mcp-Servers": "ga",
    }
    if tenant_id:
        headers["X-Tenant-Id"] = tenant_id
    return headers


@dataclass(frozen=True)
class GAToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


async def list_ga_tool_specs(
    *, site_id: str , tenant_id: str | None = None
) -> list[GAToolSpec]:
    """列出 GA MCP tools（用于 UI 展示）。"""
    ensure_langchain_globals()
    client = MultiServerMCPClient(
        {
            "ga-report": {
                "url": GA_MCP_URL,
                "transport": "streamable_http",
                "headers": _ga_headers(site_id, tenant_id),
            }
        }
    )
    async with client.session("ga-report") as session:
        tools = await load_mcp_tools(session)
        specs: list[GAToolSpec] = []
        for t in tools:
            try:
                args_schema = getattr(t, "args_schema", None)
                # args_schema 可能是 dict 或 Pydantic model
                if isinstance(args_schema, dict):
                    schema = args_schema
                elif args_schema is not None and hasattr(args_schema, "model_json_schema"):
                    schema = args_schema.model_json_schema()
                else:
                    schema = {}
            except Exception as e:
                logger.info(f"[GA_MCP] Failed to extract schema for {t.name}: {e}")
                schema = {}
            specs.append(
                GAToolSpec(
                    name=t.name,
                    description=t.description or "",
                    input_schema=schema,
                )
            )
        return specs


async def call_ga_tool(
    *,
    tool_name: str,
    tool_input: dict[str, Any],
    site_id: str ,
    tenant_id: str | None = None,
) -> Any:
    """调用 GA MCP 工具（每次调用建立一次会话，确保正确释放资源）。
    
    如果 MCP 返回错误（isError=True），会捕获 ToolException 并转换为字典格式：
    {"success": False, "error": "错误消息", "isError": True, "errorCode": "..."}
    
    调用方应使用 check_ga_tool_error() 判断返回值是否为错误。
    """
    logger.info(f"[GA_MCP][call_ga_tool] 调用工具: {tool_name}, site_id={site_id}")
    
    ensure_langchain_globals()
    client = MultiServerMCPClient(
        {
            "ga-report": {
                "url": GA_MCP_URL,
                "transport": "streamable_http",
                "headers": _ga_headers(site_id, tenant_id),
            }
        }
    )
    
    try:
        async with client.session("ga-report") as session:
            tools = await load_mcp_tools(session)
            target = next((t for t in tools if t.name == tool_name), None)
            if target is None:
                error_msg = f"GA MCP 未找到工具: {tool_name}"
                logger.error(f"[GA_MCP][call_ga_tool] {error_msg}")
                raise RuntimeError(error_msg)
            
            logger.info(f"[GA_MCP][call_ga_tool] 正在调用工具...")
            try:
                result = await target.ainvoke(tool_input)
                logger.info(f"[GA_MCP][call_ga_tool] 工具调用完成")
                return result
                
            except Exception as tool_error:
                # langchain_mcp_adapters 会在 MCP 返回 isError=True 时抛出 ToolException
                from langchain_core.tools.base import ToolException
                
                if isinstance(tool_error, ToolException):
                    error_msg = str(tool_error)
                    logger.error(f"[GA_MCP][call_ga_tool] MCP 工具返回错误")
                    logger.error(f"[GA_MCP][call_ga_tool] 错误消息: {error_msg}")
                    logger.error(f"[GA_MCP][call_ga_tool] 工具名: {tool_name}")
                    logger.error(f"[GA_MCP][call_ga_tool] 输入参数: {json.dumps(tool_input, ensure_ascii=False, indent=2)}")
                    
                    # 构造错误字典
                    error_dict = {
                        "success": False,
                        "error": error_msg,
                        "tool_name": tool_name,
                        "isError": True
                    }
                    
                    # 检查错误消息内容判断是否为 token 刷新失败
                    if is_token_expired_error(error_msg):
                        error_dict["errorCode"] = ERROR_CODE_TOKEN_REFRESH_FAILED
                        logger.warning(f"[GA_MCP][call_ga_tool] 检测到 TOKEN_REFRESH_FAILED: {error_msg}")
                    
                    return error_dict
                else:
                    # 其他异常（如网络错误、超时等）
                    logger.error(f"[GA_MCP][call_ga_tool] 工具调用异常: {type(tool_error).__name__}: {tool_error}", exc_info=True)
                    return {
                        "success": False,
                        "error": f"工具调用异常: {str(tool_error)}",
                        "tool_name": tool_name
                    }
                    
    except Exception as e:
        logger.error(f"[GA_MCP][call_ga_tool] 调用失败: {type(e).__name__}: {e}", exc_info=True)
        return {"success": False, "error": f"GA MCP 调用失败: {str(e)}"}


async def with_ga_tools(
    *,
    site_id: str,
    tenant_id: str | None = None,
    fn,
) -> Any:
    """在同一个 MCP session 内加载 tools 并执行回调。

    适用于 ReAct：一次用户请求内连续调用多个工具，避免重复建连。
    """
    ensure_langchain_globals()
    client = MultiServerMCPClient(
        {
            "ga-report": {
                "url": GA_MCP_URL,
                "transport": "streamable_http",
                "headers": _ga_headers(site_id, tenant_id),
            }
        }
    )
    async with client.session("ga-report") as session:
        tools = await load_mcp_tools(session)
        tools_by_name = {t.name: t for t in tools}
        return await fn(tools_by_name)


# Alias for compatibility
normalize_ga_tool_result = normalize_mcp_json_result


