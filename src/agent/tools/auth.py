"""授权工具模块。

提供获取访问令牌的功能。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

from agent.config import (
    AUTHORIZATION_API_URL,
    AUTHORIZATION_CLIENT_ID,
    AUTHORIZATION_CLIENT_SECRET,
    get_logger,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class TokenResponse:
    """Token 响应数据模型。"""

    token_type: str
    expires_in: int  # 单位：秒
    access_token: str


async def get_mcp_token(
    *,
    site_id: str,
    tenant_id: str,
    site_url: str,
    client_id: str = AUTHORIZATION_CLIENT_ID,
    client_secret: str = AUTHORIZATION_CLIENT_SECRET,
    grant_type: str = "client_credentials",
    aud: str = "site:mcp",
    authorization_api_url: str | None = None,
    timeout_s: float = 30.0,
) -> TokenResponse:
    """获取访问令牌。

    Args:
        client_id: 客户端 ID
        client_secret: 客户端密钥
        site_id: 站点 ID
        tenant_id: 租户 ID
        site_url: 站点 URL
        grant_type: 授权类型，默认为 "client_credentials"
        aud: 受众，默认为 "site:mcp"
        authorization_api_url: 授权 API URL，如果为 None 则使用配置中的值
        timeout_s: 请求超时时间（秒），默认 30 秒

    Returns:
        TokenResponse: 包含 token_type、expires_in 和 access_token 的响应对象

    Raises:
        httpx.HTTPStatusError: 当 HTTP 请求失败时
        ValueError: 当响应数据格式不正确时
    """
    url = authorization_api_url or AUTHORIZATION_API_URL
    if not url:
        raise ValueError("AUTHORIZATION_API_URL 未配置")

    payload = {
        "grant_type": grant_type,
        "client_id": client_id,
        "client_secret": client_secret,
        "site_id": site_id,
        "tenant_id": tenant_id,
        "site_url": site_url,
        "aud": aud,
    }

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        response = await client.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()

        data: dict[str, Any] = response.json()

        # 验证必需的字段
        if "access_token" not in data:
            raise ValueError(f"响应中缺少 access_token 字段: {data}")

        return TokenResponse(
            token_type=data.get("token_type", "Bearer"),
            expires_in=int(data.get("expires_in", 0)),
            access_token=str(data["access_token"]),
        )


async def ensure_mcp_token(
    state: dict[str, Any], *, context: str = "MCP"
) -> tuple[str | None, dict[str, Any]]:
    """确保 MCP token 有效，如果过期则重新获取。
    
    Args:
        state: 状态字典，需要包含 site_id、tenant_id、site_url 字段
        context: 上下文标识，用于日志记录（如 "Shortcut"、"Article"）
    
    Returns:
        (token, state_updates): token 字符串和需要更新的 state 字典
    """
    current_time = time.time()
    token = state.get("mcp_token")
    expires_at = state.get("mcp_token_expires_at")
    
    # 检查 token 是否存在且未过期（提前 60 秒刷新，避免边界情况）
    if token and expires_at and current_time < (expires_at - 60):
        return token, {}
    
    # Token 不存在或已过期，需要重新获取
    site_id = state.get("site_id")
    tenant_id = state.get("tenant_id")
    # site_url = state.get("site_url")
    
    if not site_id or not tenant_id:
        logger.warning(
            f"[{context}] Cannot get token: missing required fields "
            f"(site_id={site_id}, tenant_id={tenant_id})"
        )
        return None, {}
    

    try:
        logger.info(
            f"[{context}] Fetching new MCP token for "
            f"site_id={site_id}, tenant_id={tenant_id}"
        )
        token_response = await get_mcp_token(
            site_id=site_id,
            tenant_id=tenant_id,
            site_url="https://site-dev",
        )
        
        # 计算过期时间戳
        expires_at = current_time + token_response.expires_in
        
        logger.info(
            f"[{context}] MCP token fetched successfully, "
            f"expires in {token_response.expires_in}s"
        )
        return token_response.access_token, {
            "mcp_token": token_response.access_token,
            "mcp_token_expires_at": expires_at,
        }
    except Exception as e:
        logger.error(f"[{context}] Failed to get MCP token: {e}")
        return None, {}
