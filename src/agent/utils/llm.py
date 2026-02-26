"""LLM 实例模块。

提供预配置的 LLM 实例；内部复用共享的 httpx 连接池以提升性能。
"""

from __future__ import annotations

from typing import Any

import httpx
from langchain_openai import ChatOpenAI

from agent.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_NANO_MODEL

# 进程内共享的 httpx 客户端（惰性初始化）
_httpx_sync: httpx.Client | None = None
_httpx_async: httpx.AsyncClient | None = None


def _get_shared_httpx_clients() -> tuple[httpx.Client, httpx.AsyncClient]:
    """创建或返回进程内共享的 httpx 客户端，复用连接池。"""
    global _httpx_sync, _httpx_async
    if _httpx_sync is None:
        limits = httpx.Limits(
            max_connections=50,
            max_keepalive_connections=20,
            keepalive_expiry=60,
        )
        timeout = httpx.Timeout(30.0, connect=5.0)
        _httpx_sync = httpx.Client(
            http2=True,
            limits=limits,
            timeout=timeout,
        )
        _httpx_async = httpx.AsyncClient(
            http2=True,
            limits=limits,
            timeout=timeout,
        )
    return _httpx_sync, _httpx_async


def _require_chat_openai() -> Any:
    if ChatOpenAI is None:
        raise ImportError(
            "LLM 依赖未安装或版本不兼容：无法导入 `langchain_openai.ChatOpenAI`。"
        )
    return ChatOpenAI


def _make_llm(model: str, *, disable_streaming: bool = False) -> Any:
    Chat = _require_chat_openai()
    http_client, http_async_client = _get_shared_httpx_clients()
    return Chat(
        model=model,
        temperature=0,
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        disable_streaming=disable_streaming,
        http_client=http_client,
        http_async_client=http_async_client,
    )


# 注意：不要在 import 时就强制初始化 LLM（会导致依赖/环境问题直接炸 import）
_llm: Any | None = None
_llm_nostream: Any | None = None
_llm_nano: Any | None = None
_llm_nano_nostream: Any | None = None


def get_llm() -> Any:
    """返回主模型 LLM 实例（支持流式），惰性初始化。"""
    global _llm
    if _llm is None:
        _llm = _make_llm(LLM_MODEL, disable_streaming=False)
    return _llm


def get_llm_nostream() -> Any:
    """返回主模型 LLM 实例（关闭流式），惰性初始化。"""
    global _llm_nostream
    if _llm_nostream is None:
        _llm_nostream = _make_llm(LLM_MODEL, disable_streaming=True)
    return _llm_nostream


def get_llm_nano() -> Any:
    """返回 Nano 模型 LLM 实例（支持流式），惰性初始化。"""
    global _llm_nano
    if _llm_nano is None:
        _llm_nano = _make_llm(LLM_NANO_MODEL, disable_streaming=False)
    return _llm_nano


def get_llm_nano_nostream() -> Any:
    """返回 Nano 模型 LLM 实例（关闭流式），惰性初始化。"""
    global _llm_nano_nostream
    if _llm_nano_nostream is None:
        _llm_nano_nostream = _make_llm(LLM_NANO_MODEL, disable_streaming=True)
    return _llm_nano_nostream


# 向后兼容：保留原变量名（按需惰性初始化）
class _LazyLLM:
    def __init__(self, getter):
        self._getter = getter

    def __getattr__(self, item):
        return getattr(self._getter(), item)

    def __call__(self, *args, **kwargs):
        return self._getter()(*args, **kwargs)


llm:ChatOpenAI = _LazyLLM(get_llm)
llm_nostream:ChatOpenAI = _LazyLLM(get_llm_nostream)
llm_nano:ChatOpenAI = _LazyLLM(get_llm_nano)
llm_nano_nostream:ChatOpenAI = _LazyLLM(get_llm_nano_nostream)
