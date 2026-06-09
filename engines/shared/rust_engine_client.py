"""
Rust 引擎客户端 — Python 引擎调用 Rust 高性能计算服务

用途: 将 CPU 密集型计算 (向量点积、sigmoid、novelty 等)
      卸载到 Rust 服务，利用 SIMD + 并行加速。

Rust 服务端口:
- resonance-service: 8095 (HTTP/JSON)
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

# 请求超时 (秒)
REQUEST_TIMEOUT = float(os.environ.get("RUST_ENGINE_TIMEOUT", "5.0"))


class RustEngineError(Exception):
    """Rust 引擎调用异常"""
    pass


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
    """调用 Rust resonance-service 的 /compute 端点

    Args:
        user_id: 用户 ID
        anchor_id: 锚点 ID
        reaction_type: 反应类型 (共鸣/无感/反对/未体验/有害)
        opinion_embedding: 观点向量 (768 维)
        anchor_embedding: 锚点向量 (768 维)
        existing_embeddings: 已有观点向量列表
        opinion_text: 观点文本 (可选)
        emotion_word: 情绪词 (可选)

    Returns:
        {
            "value": float,         # 共鸣值
            "components": {         # 各分量
                "resonance_weight": float,
                "depth": float,
                "relevance_raw": float,
                "relevance_sigmoid": float,
                "novelty": float,
                "harmful_penalty": float,
                "unexperienced_penalty": float,
            }
        }

    Raises:
        RustEngineError: 调用失败
    """
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
    """同步版本的 Rust resonance-service 调用

    用于 gRPC 同步上下文。
    """
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
