"""
Rust 引擎客户端 — Python 引擎调用 Rust 高性能计算服务

用途: 将 CPU 密集型计算 (向量点积、sigmoid、novelty 等)
      卸载到 Rust 服务，利用 SIMD + 并行加速。

Rust 服务端口:
- resonance-service: 8095 (HTTP/JSON)
- governance-service: 8096 (HTTP/JSON)
"""

import asyncio
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

RESONANCE_SERVICE_URL = os.environ.get(
    "RUST_RESONANCE_URL", "http://localhost:8095"
)
GOVERNANCE_SERVICE_URL = os.environ.get(
    "RUST_GOVERNANCE_URL", "http://localhost:8096"
)

REQUEST_TIMEOUT = float(os.environ.get("RUST_ENGINE_TIMEOUT", "5.0"))


class RustEngineError(Exception):
    pass


# 长生命周期客户端 (复用连接池)
_async_client: Optional[httpx.AsyncClient] = None
_sync_client: Optional[httpx.Client] = None


def _get_async_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None or _async_client.is_closed:
        _async_client = httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _async_client


def _get_sync_client() -> httpx.Client:
    global _sync_client
    if _sync_client is None or _sync_client.is_closed:
        _sync_client = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _sync_client


async def close_clients():
    global _async_client, _sync_client
    if _async_client and not _async_client.is_closed:
        await _async_client.aclose()
        _async_client = None
    if _sync_client and not _sync_client.is_closed:
        _sync_client.close()
        _sync_client = None


async def call_resonance_compute(
    user_id: str,
    anchor_id: str,
    reaction_type: str,
    opinion_embedding: list[float],
    anchor_embedding: list[float],
    existing_embeddings: list[list[float]],
    opinion_text: Optional[str] = None,
    emotion_word: Optional[str] = None,
    harmful_ratio: float = 0.0,
    unexperienced_ratio: float = 0.0,
) -> dict:
    url = f"{RESONANCE_SERVICE_URL}/compute"
    payload = {
        "user_id": user_id,
        "anchor_id": anchor_id,
        "reaction_type": reaction_type,
        "opinion_embedding": opinion_embedding,
        "anchor_embedding": anchor_embedding,
        "existing_embeddings": existing_embeddings,
        "harmful_ratio": harmful_ratio,
        "unexperienced_ratio": unexperienced_ratio,
    }
    if opinion_text:
        payload["opinion_text"] = opinion_text
    if emotion_word:
        payload["emotion_word"] = emotion_word

    try:
        client = _get_async_client()
        response = await client.post(url, json=payload)

        if response.status_code != 200:
            raise RustEngineError(
                f"Rust 服务返回 {response.status_code}: {response.text}"
            )

        data = response.json()
        if "error" in data:
            raise RustEngineError(f"Rust 服务错误: {data['error']}")
        return data

    except httpx.TimeoutException:
        raise RustEngineError(f"Rust 服务超时 ({REQUEST_TIMEOUT}s)")
    except httpx.ConnectError:
        raise RustEngineError(f"无法连接 Rust 服务: {url}")
    except RustEngineError:
        raise
    except Exception as e:
        raise RustEngineError(f"Rust 服务调用异常: {e}")


def call_resonance_compute_sync(
    user_id: str,
    anchor_id: str,
    reaction_type: str,
    opinion_embedding: list[float],
    anchor_embedding: list[float],
    existing_embeddings: list[list[float]],
    opinion_text: Optional[str] = None,
    emotion_word: Optional[str] = None,
    harmful_ratio: float = 0.0,
    unexperienced_ratio: float = 0.0,
) -> dict:
    url = f"{RESONANCE_SERVICE_URL}/compute"
    payload = {
        "user_id": user_id,
        "anchor_id": anchor_id,
        "reaction_type": reaction_type,
        "opinion_embedding": opinion_embedding,
        "anchor_embedding": anchor_embedding,
        "existing_embeddings": existing_embeddings,
        "harmful_ratio": harmful_ratio,
        "unexperienced_ratio": unexperienced_ratio,
    }
    if opinion_text:
        payload["opinion_text"] = opinion_text
    if emotion_word:
        payload["emotion_word"] = emotion_word

    try:
        client = _get_sync_client()
        response = client.post(url, json=payload)

        if response.status_code != 200:
            raise RustEngineError(
                f"Rust 服务返回 {response.status_code}: {response.text}"
            )

        data = response.json()
        if "error" in data:
            raise RustEngineError(f"Rust 服务错误: {data['error']}")
        return data

    except httpx.TimeoutException:
        raise RustEngineError(f"Rust 服务超时 ({REQUEST_TIMEOUT}s)")
    except httpx.ConnectError:
        raise RustEngineError(f"无法连接 Rust 服务: {url}")
    except RustEngineError:
        raise
    except Exception as e:
        raise RustEngineError(f"Rust 服务调用异常: {e}")


async def call_governance_evaluate(
    content_id: str,
    content_type: str,
    reaction_summary: dict,
    marker_credits: Optional[dict] = None,
) -> dict:
    url = f"{GOVERNANCE_SERVICE_URL}/evaluate"
    payload = {
        "content_id": content_id,
        "content_type": content_type,
        "reaction_summary": reaction_summary,
    }
    if marker_credits:
        payload["marker_credits"] = marker_credits

    try:
        client = _get_async_client()
        response = await client.post(url, json=payload)

        if response.status_code != 200:
            raise RustEngineError(
                f"Rust governance 服务返回 {response.status_code}: {response.text}"
            )

        data = response.json()
        if "error" in data:
            raise RustEngineError(f"Rust governance 服务错误: {data['error']}")
        return data

    except httpx.TimeoutException:
        raise RustEngineError(f"Rust governance 服务超时 ({REQUEST_TIMEOUT}s)")
    except httpx.ConnectError:
        raise RustEngineError(f"无法连接 Rust governance 服务: {url}")
    except RustEngineError:
        raise
    except Exception as e:
        raise RustEngineError(f"Rust governance 服务调用异常: {e}")


def call_governance_evaluate_sync(
    content_id: str,
    content_type: str,
    reaction_summary: dict,
    marker_credits: Optional[dict] = None,
) -> dict:
    url = f"{GOVERNANCE_SERVICE_URL}/evaluate"
    payload = {
        "content_id": content_id,
        "content_type": content_type,
        "reaction_summary": reaction_summary,
    }
    if marker_credits:
        payload["marker_credits"] = marker_credits

    try:
        client = _get_sync_client()
        response = client.post(url, json=payload)

        if response.status_code != 200:
            raise RustEngineError(
                f"Rust governance 服务返回 {response.status_code}: {response.text}"
            )

        data = response.json()
        if "error" in data:
            raise RustEngineError(f"Rust governance 服务错误: {data['error']}")
        return data

    except httpx.TimeoutException:
        raise RustEngineError(f"Rust governance 服务超时 ({REQUEST_TIMEOUT}s)")
    except httpx.ConnectError:
        raise RustEngineError(f"无法连接 Rust governance 服务: {url}")
    except RustEngineError:
        raise
    except Exception as e:
        raise RustEngineError(f"Rust governance 服务调用异常: {e}")
