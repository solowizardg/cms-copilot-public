from langchain_core.messages.utils import logger
from langgraph_sdk import Auth

auth = Auth()

@auth.authenticate
async def always_allow(
    headers: dict | None = None,
    authorization: str | None = None,
    body: dict | None = None
):
    # 从headers中获取参数，处理字节格式
    def get_header_value(headers_dict, key):
        if headers_dict:     
            # 尝试字节键名
            byte_key = key.encode('utf-8')
            if byte_key in headers_dict:
                value = headers_dict[byte_key]
                if isinstance(value, bytes):
                    return value.decode('utf-8')
                return value
        return None
    oauth_token = None
    if authorization:
        # 直接从参数获取（格式通常是 "Bearer <token>"）
        if authorization.startswith("Bearer "):
            oauth_token = authorization[7:]  # 移除 "Bearer " 前缀
        elif authorization.startswith("bearer "):
            oauth_token = authorization[7:]  # 处理小写情况
        else:
            oauth_token = authorization  # 如果没有前缀，直接作为 token

    # 获取站点相关信息
    site_id = get_header_value(headers, "x-site-id")
    tenant_id = get_header_value(headers, "x-tenant-id")
    site_url = get_header_value(headers, "x-site-url")
    property_id = get_header_value(headers, "x-property-id")

    if not site_id:
        site_id = "019a104d-98e9-7298-8be1-af1926bbc085"
    if not tenant_id:
        tenant_id = "337059212"
    if not site_url:
        site_url = "https://site-dev.cedemo.cn"
    if not property_id:
        property_id = "properties/337059212"

    identity = "authenticated_user" if oauth_token else "anonymous"

    logger.info(f"auth tenant_id: {tenant_id} - site_id: {site_id} - site_url: {site_url} - property_id: {property_id} -")

    return {
        "identity": identity,
        "is_authenticated": bool(oauth_token),
        "tenant_id": tenant_id,
        "site_id": site_id,
        "site_url": site_url,
        "property_id": property_id,
    }
