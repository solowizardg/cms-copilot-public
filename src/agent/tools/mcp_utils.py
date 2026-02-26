"""MCP Tool Utilities - Shared logic for MCP clients."""
from __future__ import annotations

import json
import os
from typing import Any

from agent.config import get_logger

logger = get_logger(__name__)

# UTF-8 BOM patch state
_BOM_PATCH_APPLIED = False


def get_mcp_structured_content(raw_result: Any) -> dict | None:
    """Extract structuredContent from raw tool result."""
    if raw_result is None:
        return None
    if isinstance(raw_result, dict):
        return raw_result.get("structuredContent") or raw_result.get("structured_content")
    return getattr(raw_result, "structuredContent", None) or getattr(
        raw_result, "structured_content", None
    )


def get_mcp_is_error(raw_result: Any) -> bool:
    """Check if raw result is marked as error (isError/is_error)."""
    if raw_result is None:
        return False
    if isinstance(raw_result, dict):
        return raw_result.get("isError", raw_result.get("is_error", False)) is True
    return getattr(raw_result, "isError", False) or getattr(raw_result, "is_error", False)


def extract_mcp_error_message(raw_result: Any, structured: dict | None = None, default_msg: str = "MCP 工具返回错误，请稍后重试。") -> str:
    """Extract error message from structuredContent or content."""
    logger = get_logger(__name__)
    
    if is_mcp_debug_enabled():
        logger.debug(f"[MCP][extract_error] raw_result type={type(raw_result).__name__}")
    
    # 优先检查：如果是我们的错误字典格式（来自 call_mcp_tool 的异常捕获）
    if isinstance(raw_result, dict) and "error" in raw_result:
        error_val = raw_result.get("error", "")
        if error_val and isinstance(error_val, str):
            if is_mcp_debug_enabled():
                logger.debug(f"[MCP][extract_error] 从 error 字段提取: {error_val}")
            return error_val
    
    if structured is None:
        structured = get_mcp_structured_content(raw_result)

    if is_mcp_debug_enabled():
        logger.debug(f"[MCP][extract_error] structured={structured}")

    if isinstance(structured, dict):
        msg = structured.get("message", "")
        if msg:
            result = msg if isinstance(msg, str) else str(msg)
            if is_mcp_debug_enabled():
                logger.debug(f"[MCP][extract_error] 从 structured.message 提取: {result}")
            return result
    
    if raw_result is None:
        if is_mcp_debug_enabled():
            logger.debug(f"[MCP][extract_error] raw_result 为 None, 返回默认消息")
        return default_msg
        
    content = (
        raw_result.get("content")
        if isinstance(raw_result, dict)
        else getattr(raw_result, "content", None)
    )
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict) and "text" in first:
            text = first.get("text", "")
            result = text if isinstance(text, str) else str(text)
            if is_mcp_debug_enabled():
                logger.debug(f"[MCP][extract_error] 从 content[0].text 提取: {result}")
            return result
        if isinstance(first, str):
            if is_mcp_debug_enabled():
                logger.debug(f"[MCP][extract_error] 从 content[0] 提取: {first}")
            return first
    
    if is_mcp_debug_enabled():
        logger.debug(f"[MCP][extract_error] 无法提取错误消息，返回默认消息")
    return default_msg


def is_mcp_debug_enabled() -> bool:
    """Check if MCP debug logging is enabled."""
    return os.getenv("MCP_DEBUG", "1") in {
        "1",
        "true",
        "True",
        "yes",
        "YES",
        "on",
        "ON",
    }


def patch_mcp_streamable_http_bom() -> None:
    """Remove UTF-8 BOM before parsing MCP JSON response to avoid validation errors."""
    global _BOM_PATCH_APPLIED
    if _BOM_PATCH_APPLIED:
        return
    try:
        from mcp.client import streamable_http
        from mcp.shared.message import SessionMessage
        from mcp.types import JSONRPCMessage

        transport_class = streamable_http.StreamableHTTPTransport

        async def _handle_json_response_bom_stripped(
            self: Any,
            response: Any,
            read_stream_writer: Any,
            is_initialization: bool = False,
        ) -> None:
            try:
                content = await response.aread()
                had_bom = False
                if isinstance(content, bytes) and content.startswith(b"\xef\xbb\xbf"):
                    content = content[3:]
                    had_bom = True
                    if is_mcp_debug_enabled():
                        logger.debug(f"[MCP][BOM] 移除了 UTF-8 BOM 头")
                
                message = JSONRPCMessage.model_validate_json(content)
                if is_initialization:
                    self._maybe_extract_protocol_version_from_message(message)
                session_message = SessionMessage(message)
                await read_stream_writer.send(session_message)
                
                if is_mcp_debug_enabled() and had_bom:
                    logger.debug(f"[MCP][BOM] 成功解析带 BOM 的响应")
            except Exception as exc:  # pragma: no cover
                streamable_http.logger.exception("Error parsing JSON response")
                logger.error(f"[MCP][BOM] JSON 响应解析失败: {type(exc).__name__}: {exc}", exc_info=True)
                await read_stream_writer.send(exc)

        transport_class._handle_json_response = _handle_json_response_bom_stripped
        _BOM_PATCH_APPLIED = True
        if is_mcp_debug_enabled():
            logger.debug("[MCP] Applied BOM-strip patch for streamable_http JSON responses")
    except Exception as e:  # pragma: no cover
        logger.warning("[MCP] Could not apply BOM patch: %s", e)


def normalize_mcp_json_result(res: Any) -> Any:
    """Attempt to normalize tool output into a JSON-serializable object."""
    def _strip_keys(obj: Any) -> Any:
        if isinstance(obj, dict):
            out: dict[str, Any] = {}
            for k, v in obj.items():
                kk = k.strip() if isinstance(k, str) else str(k)
                vv = _strip_keys(v)
                if kk in {"name", "value"} and isinstance(vv, str):
                    vv = vv.strip()
                out[kk] = vv
            return out
        if isinstance(obj, list):
            return [_strip_keys(x) for x in obj]
        if isinstance(obj, str):
            return obj.strip()
        return obj

    def _try_parse_json_text(text: str) -> Any:
        t = (text or "").strip()
        if not t:
            return t
        try:
            return json.loads(t)
        except Exception:
            pass
        l = t.find("{")
        r = t.rfind("}")
        if 0 <= l < r:
            try:
                return json.loads(t[l : r + 1])
            except Exception:
                return t
        return t

    if isinstance(res, list) and res:
        first = res[0]
        if isinstance(first, dict) and "text" in first and isinstance(first.get("text"), str):
            parsed = _try_parse_json_text(first.get("text") or "")
            return _strip_keys(parsed)
        if isinstance(first, str):
            parsed = _try_parse_json_text(first)
            return _strip_keys(parsed)
        return _strip_keys(res)

    if isinstance(res, dict):
        return _strip_keys(res)

    if isinstance(res, str):
        parsed = _try_parse_json_text(res)
        return _strip_keys(parsed)

    if isinstance(res, (int, float, bool)) or res is None:
        return res

    return str(res)


def ensure_langchain_globals() -> None:
    """Ensure langchain global flags are set to avoid errors in legacy versions."""
    try:
        import langchain  # type: ignore

        if not hasattr(langchain, "debug"):
            langchain.debug = False  # type: ignore[attr-defined]
        if not hasattr(langchain, "verbose"):
            langchain.verbose = False  # type: ignore[attr-defined]
    except Exception:
        return None
