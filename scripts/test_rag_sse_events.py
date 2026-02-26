"""测试 rag_sse_events 函数的脚本。

用法：
  # 使用默认参数
  python scripts/test_rag_sse_events.py
  
  # 自定义参数
  python scripts/test_rag_sse_events.py --tenant-id tenant_123 --site-id site_123 --query "什么情况"

说明：
- 默认租户 ID: tenant_123
- 默认站点 ID: site_123
- 默认查询: 什么情况
- 默认 URL 从环境变量 RAG_API_URL 或 config.py 中获取
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

# 允许直接在源码仓库中运行：把 src/ 加进 PYTHONPATH
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from agent.tools.rag import rag_sse_events
from agent.config import RAG_API_URL


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="测试 rag_sse_events 函数")
    p.add_argument("--tenant-id", default="tenant_123", help="租户 ID（默认：tenant_123）")
    p.add_argument("--site-id", default="site_123", help="站点 ID（默认：site_123）")
    p.add_argument("--query", default="什么情况", help="查询问题（默认：什么情况）")
    p.add_argument("--session-id", default=None, help="Session ID（默认：自动生成 UUID）")
    p.add_argument(
        "--url",
        default=None,
        help="RAG API URL（默认：从环境变量或 config 中获取）",
    )
    p.add_argument("--timeout", type=float, default=60.0, help="超时时间（秒，默认：60.0）")
    return p.parse_args()


async def _test_rag_sse_events() -> dict:
    args = _parse_args()
    session_id = args.session_id or str(uuid.uuid4())
    
    # 确定实际使用的 URL
    actual_url = args.url or os.getenv("RAG_API_URL") or RAG_API_URL

    print(f"[测试] 租户 ID: {args.tenant_id}")
    print(f"[测试] 站点 ID: {args.site_id}")
    print(f"[测试] 查询: {args.query}")
    print(f"[测试] Session ID: {session_id}")
    print(f"[测试] URL: {actual_url}")
    print(f"[测试] 超时: {args.timeout}秒")
    print("-" * 80)

    all_events = []
    answer_parts = []
    detected_language = None
    sources_count = 0
    token_usage = None
    has_error = False

    try:
        async for event in rag_sse_events(
            question=args.query,
            tenant_id=args.tenant_id,
            site_id=args.site_id,
            session_id=session_id,
            rag_api_url=args.url,
            timeout_s=args.timeout,
        ):
            all_events.append(event)

            # 显示事件信息
            print(f"\n[事件 #{len(all_events)}]")
            print(f"  节点名称: {event.node_name}")
            if event.event_name:
                print(f"  事件类型: {event.event_name}")
            print(f"  数据键: {list(event.data.keys())}")

            # 根据不同节点类型显示详细信息
            if event.node_name == "workflow":
                session_id_from_event = event.data.get("session_id")
                print(f"  [工作流] Session ID: {session_id_from_event}")

            elif event.node_name == "analysis_language":
                detected_language = event.data.get("detected_language")
                print(f"  [语言检测] {detected_language}")

            elif event.node_name == "retrieval_rerank":
                sources = event.data.get("sources", [])
                sources_count = len(sources)
                print(f"  [检索重排] 找到 {sources_count} 个相关文档片段")
                for i, source in enumerate(sources[:3], 1):  # 只显示前3个
                    score = source.get("score", 0)
                    content_preview = source.get("content", "")[:100]
                    print(f"    [{i}] 相似度: {score:.4f} | 内容预览: {content_preview}...")

            elif event.node_name == "generate_answer":
                answer = event.data.get("answer", "")
                if answer:
                    answer_parts.append(answer)
                    print(f"  [生成答案] {answer[:200]}{'...' if len(answer) > 200 else ''}")

            elif event.node_name == "final_answer":
                final_answer = event.data.get("answer", "")
                if final_answer:
                    answer_parts.append(final_answer)
                    print(f"  [最终答案] {final_answer[:200]}{'...' if len(final_answer) > 200 else ''}")
                # final_answer 事件可能包含完整信息
                if "usages" in event.data:
                    token_usage = event.data.get("usages", [])
                    print(f"  [Token 使用]")
                    for usage in token_usage:
                        print(
                            f"    模型: {usage.get('model_name')} | "
                            f"输入: {usage.get('input_tokens')} | "
                            f"输出: {usage.get('output_tokens')} | "
                            f"总计: {usage.get('total_tokens')}"
                        )

            elif event.event_name == "error":
                has_error = True
                error_msg = event.data.get("error") or event.data.get("message") or str(event.data)
                print(f"  [错误] {error_msg}")
                print(f"  [错误详情] {json.dumps(event.data, ensure_ascii=False, indent=2)}")

            else:
                # 显示其他未知节点类型的部分数据
                print(f"  [数据预览] {json.dumps(event.data, ensure_ascii=False, indent=2)[:300]}...")

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        print(f"\n{'=' * 80}")
        print(f"[错误] {error_type}: {error_msg}")
        print(f"{'=' * 80}")
        
        # 针对不同类型的错误提供诊断信息
        if "ConnectError" in error_type or "ConnectionError" in error_type:
            print("\n[诊断] 连接错误 - 可能的原因：")
            print(f"  1. 网络连接问题 - 无法连接到 {actual_url}")
            print("  2. 代理配置问题 - 检查 HTTP_PROXY/HTTPS_PROXY 环境变量")
            print("  3. SSL/TLS 证书问题 - 检查证书是否有效")
            print("  4. 防火墙或 VPN 限制")
            print("\n[建议]")
            print("  - 检查网络连接是否正常")
            print("  - 尝试使用 curl 或浏览器访问该 URL")
            print("  - 检查是否需要配置代理：")
            print("    export HTTP_PROXY=http://proxy:port")
            print("    export HTTPS_PROXY=http://proxy:port")
            print(f"  - 验证 URL 是否正确: {actual_url}")
        elif "Timeout" in error_type:
            print("\n[诊断] 超时错误 - 可能的原因：")
            print(f"  1. 服务器响应时间超过 {args.timeout} 秒")
            print("  2. 网络延迟过高")
            print("\n[建议]")
            print(f"  - 尝试增加超时时间: --timeout {args.timeout * 2}")
        elif "HTTPStatusError" in error_type or "HTTPError" in error_type:
            print("\n[诊断] HTTP 状态错误")
            print("\n[建议]")
            print("  - 检查 API 端点是否正确")
            print("  - 验证认证信息（如果需要）")
            print(f"  - 检查服务器状态: {actual_url}")
        
        print("\n[详细错误信息]")
        import traceback
        traceback.print_exc()
        
        return {
            "error": error_msg,
            "error_type": error_type,
            "url": actual_url,
            "session_id": session_id,
        }

    print("-" * 80)

    # 汇总结果
    answer_text = "".join(answer_parts).strip()

    result = {
        "success": bool(answer_text) and not has_error,
        "answer": answer_text,
        "session_id": session_id,
        "detected_language": detected_language,
        "sources_count": sources_count,
        "token_usage": token_usage,
        "events_count": len(all_events),
        "has_error": has_error,
        "events": [
            {
                "node_name": ev.node_name,
                "event_name": ev.event_name,
                "data_keys": list(ev.data.keys()),
            }
            for ev in all_events
        ],
    }

    print(f"\n[结果汇总]")
    print(f"  成功: {result['success']}")
    print(f"  事件总数: {result['events_count']}")
    if has_error:
        print("  ⚠️  检测到错误事件")
    if detected_language:
        print(f"  检测语言: {detected_language}")
    if sources_count > 0:
        print(f"  检索到文档片段: {sources_count} 个")
    if answer_text:
        print(f"  答案: {answer_text[:200]}{'...' if len(answer_text) > 200 else ''}")
    else:
        print("  ⚠️  未获取到答案")

    if token_usage:
        print(f"\n[Token 使用统计]")
        total_input = sum(u.get("input_tokens", 0) for u in token_usage)
        total_output = sum(u.get("output_tokens", 0) for u in token_usage)
        total_tokens = sum(u.get("total_tokens", 0) for u in token_usage)
        print(f"  总输入 Token: {total_input}")
        print(f"  总输出 Token: {total_output}")
        print(f"  总计 Token: {total_tokens}")

    print(f"\n[事件列表]")
    for i, ev_info in enumerate(result["events"], 1):
        event_type = ev_info["event_name"] or "N/A"
        print(f"  [{i}] {ev_info['node_name']} ({event_type})")

    return result


if __name__ == "__main__":
    try:
        result = asyncio.run(_test_rag_sse_events())
        if result.get("error"):
            sys.exit(1)
        elif not result.get("success"):
            print("\n[警告] 测试未完全成功")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[中断] 用户取消")
        sys.exit(130)
    except Exception as exc:
        print(f"[错误] {type(exc).__name__}: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
