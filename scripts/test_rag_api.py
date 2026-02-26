"""RAG API 测试脚本（本地调试用）。

用法：
  # 使用默认参数
  python scripts/test_rag_api.py
  
  # 自定义参数
  python scripts/test_rag_api.py --tenant-id tenant_123 --site-id site_123 --query "什么情况"

说明：
- 默认租户 ID: tenant_123
- 默认站点 ID: site_123
- 默认查询: 什么情况
- 默认 URL 为 https://ai-chatbot-dev.cedemo.cn/ai/rag/kb/v1/chatbot-stream
- 可通过环境变量 RAG_API_URL 覆盖
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import httpx

# 允许直接在源码仓库中运行：把 src/ 加进 PYTHONPATH
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="测试 RAG API")
    p.add_argument("--tenant-id", default="tenant_123", help="租户 ID（默认：tenant_123）")
    p.add_argument("--site-id", default="site_123", help="站点 ID（默认：site_123）")
    p.add_argument("--query", default="什么情况", help="查询问题（默认：什么情况）")
    p.add_argument(
        "--url",
        default=os.getenv(
            "RAG_API_URL",
            "https://ai-chatbot-dev.cedemo.cn/ai/rag/kb/v1/chatbot-stream",
        ),
        help="RAG API URL",
    )
    return p.parse_args()


async def _test_rag_api() -> dict:
    args = _parse_args()
    session_id = str(uuid.uuid4())
    datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 准备请求数据
    request_data = {
        "tenant_id": args.tenant_id,
        "site_id": args.site_id,
        "query": args.query,
        "session_id": session_id,
        "datetime": datetime_str,
        "history": [],
        "top_k": 10,
        "top_n": 5,
        "use_compress": False,
        "threshold": 0.55,
    }

    print(f"[测试] URL: {args.url}")
    print(f"[测试] 租户 ID: {args.tenant_id}")
    print(f"[测试] 站点 ID: {args.site_id}")
    print(f"[测试] 查询: {args.query}")
    print(f"[测试] Session ID: {session_id}")
    print(f"[测试] 时间: {datetime_str}")
    print("-" * 80)

    answer_text = ""
    all_events = []

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                args.url,
                headers={
                    "Accept": "text/event-stream",
                    "Content-Type": "application/json",
                },
                json=request_data,
            ) as response:
                print(f"[响应] 状态码: {response.status_code}")
                response.raise_for_status()

                # 解析 SSE 流
                current_event = None
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    # 解析 SSE 格式: event: xxx\ndata: {...}
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)
                            node_name = data.get("node_name")
                            all_events.append({"event": current_event, "data": data})

                            # 显示事件类型
                            if current_event:
                                print(f"\n[事件] {current_event}")

                            # 显示不同节点的事件
                            if current_event == "error":
                                error_msg = data.get("error") or data.get("message") or str(data)
                                print(f"[错误] {error_msg}")
                                # 显示完整的错误数据
                                print(f"[错误详情] {json.dumps(data, ensure_ascii=False, indent=2)}")
                            elif node_name == "workflow":
                                print(f"[工作流] Session ID: {data.get('session_id')}")
                            elif node_name == "analysis_language":
                                print(f"[语言检测] {data.get('detected_language')}")
                            elif node_name == "retrieval_rerank":
                                sources = data.get("sources", [])
                                print(f"[检索重排] 找到 {len(sources)} 个相关文档片段")
                                for i, source in enumerate(sources[:3], 1):  # 只显示前3个
                                    score = source.get("score", 0)
                                    content_preview = source.get("content", "")[:100]
                                    print(f"  [{i}] 相似度: {score:.4f} | 内容预览: {content_preview}...")
                            elif node_name == "generate_answer":
                                answer = data.get("answer", "")
                                if answer:
                                    answer_text = answer
                                    print(f"\n[答案] {answer}")
                            elif node_name == "usage_token":
                                usages = data.get("usages", [])
                                print("\n[Token 使用]")
                                for usage in usages:
                                    print(
                                        f"  模型: {usage.get('model_name')} | "
                                        f"输入: {usage.get('input_tokens')} | "
                                        f"输出: {usage.get('output_tokens')} | "
                                        f"总计: {usage.get('total_tokens')}"
                                    )
                            elif node_name == "final":
                                print("[完成] 流程结束")
                                # final 事件可能包含完整信息
                                if "answer" in data:
                                    answer_text = data.get("answer", "")
                                    print(f"[最终答案] {answer_text}")
                            else:
                                # 显示未识别的事件类型
                                print(f"[未知节点] {node_name or 'N/A'}")
                                print(f"  数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                        except json.JSONDecodeError as e:
                            print(f"[警告] JSON 解析失败: {e}")
                            print(f"  事件类型: {current_event}")
                            print(f"  原始数据: {data_str[:200]}")

    except httpx.HTTPStatusError as e:
        print(f"[错误] HTTP 状态错误: {e.response.status_code}")
        print(f"  响应内容: {e.response.text[:500]}")
        return {"error": str(e), "status_code": e.response.status_code}
    except httpx.RequestError as e:
        print(f"[错误] 请求错误: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"[错误] 未知错误: {type(e).__name__}: {e}")
        return {"error": str(e)}

    print("-" * 80)
    
    # 检查是否有错误事件
    has_error = any(event.get("event") == "error" for event in all_events)
    
    result = {
        "success": bool(answer_text) and not has_error,
        "answer": answer_text,
        "session_id": session_id,
        "events_count": len(all_events),
        "has_error": has_error,
        "all_events": all_events,
    }
    print(f"\n[结果] 成功: {result['success']}")
    if has_error:
        print("[结果] 检测到错误事件")
    if answer_text:
        print(f"[结果] 答案: {answer_text[:200]}{'...' if len(answer_text) > 200 else ''}")
    else:
        print("[结果] 未获取到答案")
    print(f"[结果] 事件数: {result['events_count']}")
    
    # 显示所有事件的摘要
    if all_events:
        print("\n[事件摘要]")
        for i, event in enumerate(all_events, 1):
            event_type = event.get("event", "unknown")
            node_name = event.get("data", {}).get("node_name", "N/A")
            print(f"  [{i}] {event_type} - {node_name}")

    return result


if __name__ == "__main__":
    try:
        result = asyncio.run(_test_rag_api())
        if result.get("error"):
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[中断] 用户取消")
        sys.exit(130)
    except Exception as exc:
        print(f"[错误] {type(exc).__name__}: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

