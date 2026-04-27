"""
共享文本编码器模块

被共鸣机制引擎和锚点生成引擎复用。
支持云端（BGE-base, 768维）和端侧（BGE-small, 512维）两种配置。
"""

import os
from pathlib import Path
from typing import Optional

import numpy as np


class TextEncoder:
    """BGE 文本编码器，支持批量编码和单条编码。"""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-base-zh-v1.5",
        device: str = "cpu",
        cache_dir: Optional[str] = None,
    ):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._cache_dir = cache_dir or str(
            Path.home() / ".cache" / "standby" / "models"
        )
    
    def _load_model(self):
        """延迟加载模型"""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            print(f"加载编码模型: {self.model_name}...")
            self._model = SentenceTransformer(
                self.model_name,
                cache_folder=self._cache_dir,
                device=self.device,
            )
            print(f"模型加载完成 (维度: {self._model.get_sentence_embedding_dimension()})")
        return self._model
    
    @property
    def dimension(self) -> int:
        model = self._load_model()
        return model.get_sentence_embedding_dimension()
    
    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        """批量编码文本为向量"""
        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,  # L2 归一化，方便余弦相似度计算
        )
        return embeddings
    
    def encode_single(self, text: str) -> np.ndarray:
        """编码单条文本"""
        return self.encode([text])[0]
    
    def similarity(self, text_a: str, text_b: str) -> float:
        """计算两条文本的余弦相似度"""
        emb_a = self.encode_single(text_a)
        emb_b = self.encode_single(text_b)
        return float(np.dot(emb_a, emb_b))
    
    def batch_similarity(
        self, queries: list[str], corpus: list[str]
    ) -> np.ndarray:
        """计算 query 列表与 corpus 列表的相似度矩阵"""
        query_embs = self.encode(queries)
        corpus_embs = self.encode(corpus)
        return np.dot(query_embs, corpus_embs.T)


def get_encoder(preset: str = "cloud") -> TextEncoder:
    """获取预设编码器
    
    Args:
        preset: "cloud" (768维, 精度优先) 或 "device" (512维, 轻量)
    """
    if preset == "cloud":
        return TextEncoder(model_name="BAAI/bge-base-zh-v1.5")
    elif preset == "device":
        return TextEncoder(model_name="BAAI/bge-small-zh-v1.5")
    else:
        raise ValueError(f"Unknown preset: {preset}")
