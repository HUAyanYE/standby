"""
Rust 引擎客户端 — Python 引擎调用 Rust 高性能计算服务

用途: 将 CPU 密集型计算 (向量点积、sigmoid、novelty 等)
      卸载到 Rust 服务，利用 SIMD + 并行加速。

Rust 服务端口:
- resonance-service: 8095 (HTTP/JSON)
- governance-service: 8096 (HTTP/JSON)
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Rust 服务地址 (从环境变量读取)
RESONANCE_SERVICE_URL = os.environ.get(
    "RUST_RESONANCE_URL", "http://localhost:8095"
)
GOVERNANCE_SERVICE_URL = os.environ.get(
    "RUST_GOVERNANCE_URL", "http://localhost:8096"
)

# 请求超时 (秒)
REQUEST_TIMEOUT = float(os.environ.get("RUST_ENGINE_TIMEOUT", "5.0"))


class RustEngineError(Exception):
    """Rust 引擎调用异常"""
    pass


# ============================================================
# Resonance Service 客户端
# ============================================================

async def call_resonance_compute(
    user_id: str,
    anchor_id: str,
    reaction_type: str,
    opinion_embedding: list[float],
    anchor_embedding: list[float],
    existing_embeddings: list[list[float]],
    opinion_text: Optional[str] = None,
    emotion_word: Optional[str] = None,
) -> dict:
    """调用 Rust resonance-service 的 /compute 端点"""
    url = f"{RESONANCE_SERVICE_URL}/compute"

    payload = {
        "user_id": user_id,
        "anchor_id": anchor_id,
        "reaction_type": reaction_type,
        "opinion_embedding": opinion_embedding,
        "anchor_embedding": anchor_embedding,
        "existing_embeddings": existing_embeddings,
    }

    if opinion_text:
        payload["opinion_text"] = opinion_text
    if emotion_word:
        payload["emotion_word"] = emotion_word

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
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
    except Exception as e:
        if isinstance(e, RustEngineError):
            raise
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
) -> dict:
    """同步版本的 Rust resonance-service 调用"""
    url = f"{RESONANCE_SERVICE_URL}/compute"

    payload = {
        "user_id": user_id,
        "anchor_id": anchor_id,
        "reaction_type": reaction_type,
        "opinion_embedding": opinion_embedding,
        "anchor_embedding": anchor_embedding,
        "existing_embeddings": existing_embeddings,
    }

    if opinion_text:
        payload["opinion_text"] = opinion_text
    if emotion_word:
        payload["emotion_word"] = emotion_word

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
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
    except Exception as e:
        if isinstance(e, RustEngineError):
            raise
        raise RustEngineError(f"Rust 服务调用异常: {e}")


# ============================================================
# Governance Service 客户端
# ============================================================

async def call_governance_evaluate(
    anchor_id: str,
    resonance: int,
    neutral: int,
    opposition: int,
    unexperienced: int,
    harmful: int,
    marker_credits: list[float],
    base_threshold: float = 0.15,
    min_samples: int = 10,
    current_ts: float = 0.0,
) -> dict:
    """调用 Rust governance-service 的 /evaluate 端点"""
    url = f"{GOVERNANCE_SERVICE_URL}/evaluate"

    payload = {
        "anchor_id": anchor_id,
        "resonance": resonance,
        "neutral": neutral,
        "opposition": opposition,
        "unexperienced": unexperienced,
        "harmful": harmful,
        "marker_credits": marker_credits,
        "base_threshold": base_threshold,
        "min_samples": min_samples,
        "current_ts": current_ts,
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(url, json=payload)

            if response.status_code != 200:
                raise RustEngineError(
                    f"Rust 治理服务返回 {response.status_code}: {response.text}"
                )

            data = response.json()

            if "error" in data:
                raise RustEngineError(f"Rust 治理服务错误: {data['error']}")

            return data

    except httpx.TimeoutException:
        raise RustEngineError(f"Rust 治理服务超时 ({REQUEST_TIMEOUT}s)")
    except httpx.ConnectError:
        raise RustEngineError(f"无法连接 Rust 治理服务: {url}")
    except Exception as e:
        if isinstance(e, RustEngineError):
            raise
        raise RustEngineError(f"Rust 治理服务调用异常: {e}")


def call_governance_evaluate_sync(
    anchor_id: str,
    resonance: int,
    neutral: int,
    opposition: int,
    unexperienced: int,
    harmful: int,
    marker_credits: list[float],
    base_threshold: float = 0.15,
    min_samples: int = 10,
    current_ts: float = 0.0,
) -> dict:
    """同步版本的 Rust governance-service 调用"""
    url = f"{GOVERNANCE_SERVICE_URL}/evaluate"

    payload = {
        "anchor_id": anchor_id,
        "resonance": resonance,
        "neutral": neutral,
        "opposition": opposition,
        "unexperienced": unexperienced,
        "harmful": harmful,
        "marker_credits": marker_credits,
        "base_threshold": base_threshold,
        "min_samples": min_samples,
        "current_ts": current_ts,
    }

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(url, json=payload)

            if response.status_code != 200:
                raise RustEngineError(
                    f"Rust 治理服务返回 {response.status_code}: {response.text}"
                )

            data = response.json()

            if "error" in data:
                raise RustEngineError(f"Rust 治理服务错误: {data['error']}")

            return data

    except httpx.TimeoutException:
        raise RustEngineError(f"Rust 治理服务超时 ({REQUEST_TIMEOUT}s)")
    except httpx.ConnectError:
        raise RustEngineError(f"无法连接 Rust 治理服务: {url}")
    except Exception as e:
        if isinstance(e, RustEngineError):
            raise
        raise RustEngineError(f"Rust 治理服务调用异常: {e}")


async def call_governance_detect_anomaly(
    timestamps: list[float],
    marker_ids: list[str],
    reactions_by_type: dict[str, tuple[int, int]],
    time_window_seconds: float = 300.0,
    threshold: int = 10,
    unexperienced_threshold: float = 0.4,
    min_samples: int = 10,
) -> dict:
    """调用 Rust governance-service 的 /detect-anomaly 端点"""
    url = f"{GOVERNANCE_SERVICE_URL}/detect-anomaly"

    payload = {
        "timestamps": timestamps,
        "marker_ids": marker_ids,
        "reactions_by_type": reactions_by_type,
        "time_window_seconds": time_window_seconds,
        "threshold": threshold,
        "unexperienced_threshold": unexperienced_threshold,
        "min_samples": min_samples,
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(url, json=payload)

            if response.status_code != 200:
                raise RustEngineError(
                    f"Rust 治理服务返回 {response.status_code}: {response.text}"
                )

            data = response.json()

            if "error" in data:
                raise RustEngineError(f"Rust 治理服务错误: {data['error']}")

            return data

    except httpx.TimeoutException:
        raise RustEngineError(f"Rust 治理服务超时 ({REQUEST_TIMEOUT}s)")
    except httpx.ConnectError:
        raise RustEngineError(f"无法连接 Rust 治理服务: {url}")
    except Exception as e:
        if isinstance(e, RustEngineError):
            raise
        raise RustEngineError(f"Rust 治理服务调用异常: {e}")
