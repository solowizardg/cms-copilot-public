from __future__ import annotations

import asyncio
import os
import sys
from agent.tools.auth import ensure_mcp_token
from pathlib import Path

# 允许直接在源码仓库中运行：把 src/ 加进 PYTHONPATH
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from agent.tools.lowcode_app import list_apps  # noqa: E402


async def _main():
    """主函数：获取并打印应用列表"""
    os.environ["MCP_LOWCODE_APP_URL"] = "/api/mcp/lowcode-app"
    os.environ["GATEWAY_URL"] = "https://gateway-dev.cedemo.cn"
    state = {
        "site_id": "019a104d-98e9-7298-8be1-af1926bbc085",
        "tenant_id": "337059212",
        "site_url": "https://site-dev.cedemo.cn",
    }
    token, token_updates = await ensure_mcp_token(state, context="LowcodeApp")
    app_list_response = await list_apps(page=1, page_size=20, keyword="", 
    site_id="019a104d-98e9-7298-8be1-af1926bbc085", tenant_id="337059212", token=token)
    
    # 打印解析得到的模型
    print("\n=== 解析得到的应用列表响应模型 ===")
    print(f"成功: {app_list_response.success}")
    print(f"消息: {app_list_response.message}")
    print("\n数据统计:")
    print(f"  总应用数: {app_list_response.data.total}")
    print(f"  当前页: {app_list_response.data.page}")
    print(f"  每页大小: {app_list_response.data.page_size}")
    print(f"  总页数: {app_list_response.data.total_pages}")
    print("\n应用列表 (前5个):")
    for app in app_list_response.data.list[:5]:
        print(f"  - ID: {app.id}, 名称: {app.name}, Slug: {app.slug}")
    print("\n完整模型对象:")
    print(app_list_response.model_dump_json(indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()
