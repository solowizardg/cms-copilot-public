"""RAG 工具模块。

该模块负责：
- 调用 RAG API（SSE / text/event-stream）
- 解析事件流并产出统一事件结构（供 nodes 层消费）
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Literal

import httpx
from langchain_core.tools import tool

from agent.config import RAG_API_URL

RAGNodeName = Literal["workflow", "analysis_language", "generate_answer", "final_answer"]


@dataclass(frozen=True, slots=True)
class RAGEvent:
    """RAG SSE 事件（归一化）。"""

    node_name: str
    data: dict[str, Any]
    event_name: str | None = None


def _default_request_data(
    *,
    question: str,
    tenant_id: str,
    site_id: str,
    session_id: str,
    datetime_str: str | None = None,
    history: list[dict[str, Any]] | None = None,
    top_k: int = 10,
    top_n: int = 5,
    use_compress: bool = False,
    threshold: float = 0.55,
) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "site_id": site_id,
        "query": question,
        "session_id": session_id,
        "datetime": datetime_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "history": history or [],
        "top_k": top_k,
        "top_n": top_n,
        "use_compress": use_compress,
        "threshold": threshold,
    }


async def rag_sse_events(
    *,
    question: str,
    tenant_id: str,
    site_id: str,
    session_id: str,
    rag_api_url: str | None = None,
    timeout_s: float = 60.0,
    request_data: dict[str, Any] | None = None,
) -> AsyncIterator[RAGEvent]:
    """调用 RAG API 并以事件流形式产出 RAGEvent。

    注意：这里仅负责网络 + SSE 解析，不做 UI 推送，也不做文本拼接。
    """
    url = rag_api_url or RAG_API_URL
    payload = request_data or _default_request_data(
        question=question,
        tenant_id=tenant_id,
        site_id=site_id,
        session_id=session_id,
    )

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        async with client.stream(
            "POST",
            url,
            headers={
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
            },
            json=payload,
        ) as response:
            if response.status_code >= 400:
                # 对于流式响应，尽量读一点错误详情（避免阻塞/读太多）
                error_lines: list[str] = []
                try:
                    async for line in response.aiter_lines():
                        error_lines.append(line)
                        if len(error_lines) > 20:
                            break
                except Exception:
                    pass

                error_text = "\n".join(error_lines) if error_lines else "无错误详情"
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}: {error_text[:500]}",
                    request=response.request,
                    response=response,
                )

            event_name: str | None = None
            data_lines: list[str] = []

            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    event_name = line[len("event:") :].strip()
                    continue

                if line.startswith("data:"):
                    data_lines.append(line[len("data:") :].strip())
                    continue

                # 空行：一个事件结束
                if line.strip():
                    continue

                if not data_lines:
                    event_name = None
                    continue

                data_str = "\n".join(data_lines).strip()
                data_lines = []
                if not data_str:
                    event_name = None
                    continue

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    event_name = None
                    continue

                node_name = str(data.get("node_name") or "")
                if not node_name:
                    event_name = None
                    continue

                yield RAGEvent(node_name=node_name, data=data, event_name=event_name)
                event_name = None


async def rag_query_once(
    *,
    question: str,
    tenant_id: str,
    site_id: str,
    session_id: str | None = None,
    rag_api_url: str | None = None,
) -> dict[str, Any]:
    """一次性查询：消费完整 SSE 流并返回最终答案。

    返回结构尽量保持简单，便于作为 Tool 输出：
    - answer: str
    - meta: dict（可选）
    """
    session_id = session_id or str(uuid.uuid4())

    answer_parts: list[str] = []
    detected_language: str | None = None

    async for ev in rag_sse_events(
        question=question,
        tenant_id=tenant_id,
        site_id=site_id,
        session_id=session_id,
        rag_api_url=rag_api_url,
    ):
        if ev.node_name == "analysis_language":
            dl = ev.data.get("detected_language")
            if isinstance(dl, str) and dl:
                detected_language = dl
        elif ev.node_name == "generate_answer":
            chunk = ev.data.get("answer")
            if isinstance(chunk, str) and chunk:
                answer_parts.append(chunk)
        elif ev.node_name == "final_answer":
            # 某些实现会在 final_answer 里再给一次 answer；如有则补齐
            final = ev.data.get("answer")
            if isinstance(final, str) and final and not answer_parts:
                answer_parts.append(final)
            break

    answer_text = "".join(answer_parts).strip()
    if not answer_text:
        answer_text = "抱歉，未能从知识库获取到相关答案。"

    meta: dict[str, Any] = {"session_id": session_id}
    if detected_language:
        meta["detected_language"] = detected_language

    return {"answer": answer_text, "meta": meta}


@tool
async def rag_query(question: str, tenant_id: str, site_id: str):
    """查询站点知识库（非流式 Tool 入口）。

    说明：
    - 图内 RAG（nodes/rag.py）走 rag_sse_events 做流式输出。
    - 这里保留为 LLM tool 调用的便捷接口（返回一次性结果）。
    """
    try:
        return await rag_query_once(
            question=question,
            tenant_id=tenant_id,
            site_id=site_id,
        )
    except Exception:
        # 兜底：避免 tool 调用直接炸穿（同时保留旧 mock 语义）
        return {
            "answer": f"【Mock RAG】站点 {site_id}（租户 {tenant_id}）的知识库回复：\n"
            f"针对问题「{question}」，请参考后台配置文档完成相应操作。",
            "citations": [
                {
                    "title": "CMS 使用说明（Mock）",
                    "url": "https://example.com/docs/cms/mock",
                }
            ],
        }
