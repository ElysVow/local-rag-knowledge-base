"""向量化器：基于 sentence-transformers，把文本编码为归一化的稠密向量。"""
from __future__ import annotations

from typing import Optional

import numpy as np


class Embedder:
    """惰性加载的 embedding 模型，第一次使用时才下载/加载。"""

    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None

    def _ensure_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "缺少 sentence-transformers，请先执行: pip install -r requirements.txt"
            ) from exc
        device = self.device
        if device.startswith("cuda") and not _cuda_available():
            print(f"[embeddings] CUDA 不可用，回退到 CPU 运行 {self.model_name}")
            device = "cpu"
        print(f"[embeddings] 加载模型 {self.model_name} (device={device}) ...")
        try:
            self._model = SentenceTransformer(self.model_name, device=device)
        except Exception as exc:
            raise RuntimeError(
                f"向量模型加载失败：{exc}\n"
                "国内网络请先设置镜像后重试：\n"
                "  Windows: $env:HF_ENDPOINT = \"https://hf-mirror.com\"\n"
                "  macOS/Linux: export HF_ENDPOINT=https://hf-mirror.com"
            ) from exc

    def encode(self, texts: list[str]) -> np.ndarray:
        """返回 L2 归一化的 float32 向量矩阵，形状 (n, dim)。"""
        self._ensure_model()
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return np.asarray(embeddings, dtype=np.float32)

    @property
    def is_loaded(self) -> bool:
        return self._model is not None


def _cuda_available() -> bool:
    try:
        import torch

        return torch.cuda.is_available()
    except Exception:
        return False
