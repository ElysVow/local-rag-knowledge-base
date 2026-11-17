"""向量库：基于 FAISS 的余弦相似度检索，带本地持久化（索引 + 元数据）。"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import numpy as np


class VectorStore:
    def __init__(self, index_dir: str | Path):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "index.faiss"
        self.meta_path = self.index_dir / "meta.json"
        self.index: Any = None  # faiss.IndexFlatIP
        self.meta: list[dict] = []
        self._load()

    # ---------- 持久化 ----------
    def _load(self):
        if self.index_path.exists() and self.meta_path.exists():
            try:
                import faiss

                self.index = faiss.read_index(str(self.index_path))
                self.meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
                print(f"[store] 已恢复向量库：{self.count} 个片段")
            except Exception as exc:
                print(f"[store] 恢复失败，将重建空索引：{exc}")
                self.index = None
                self.meta = []
        if self.index is None:
            self._new_index(0)

    def _new_index(self, dim: int):
        import faiss

        # 向量已归一化，内积 == 余弦相似度
        self.index = faiss.IndexFlatIP(max(dim, 1))

    def _save(self):
        import faiss

        faiss.write_index(self.index, str(self.index_path))
        self.meta_path.write_text(
            json.dumps(self.meta, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    # ---------- 写入 ----------
    def add_chunks(self, doc_id: str, doc_name: str, chunks: list[str], embeddings: np.ndarray) -> int:
        """批量添加一个文档的片段。返回本次添加的片段数。"""
        if embeddings.shape[0] == 0:
            return 0
        import faiss

        if self.count == 0 and embeddings.shape[1] != self.index.d:
            # 空索引首次写入时按实际维度重建（例如换 embedding 模型后）
            self._new_index(embeddings.shape[1])
        elif self.count > 0 and embeddings.shape[1] != self.index.d:
            raise ValueError(
                f"向量维度不一致：索引 {self.index.d} vs 新向量 {embeddings.shape[1]}，"
                "请先清空知识库或使用相同 embedding 模型"
            )

        now = time.strftime("%Y-%m-%d %H:%M:%S")
        start = self.count
        for i, chunk in enumerate(chunks):
            self.meta.append(
                {
                    "id": f"{doc_id}:{start + i}",
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "chunk_index": i,
                    "text": chunk,
                    "created_at": now,
                }
            )
        self.index.add(embeddings)
        self._save()
        return len(chunks)

    # ---------- 检索 ----------
    def search(self, query_emb: np.ndarray, top_k: int = 4, threshold: float = 0.30) -> list[dict]:
        """返回按相似度降序的片段列表：[{meta..., 'score': float}]。"""
        if self.count == 0 or query_emb.shape[0] == 0:
            return []
        scores, indices = self.index.search(query_emb, min(top_k, self.count))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.meta):
                continue
            if float(score) < threshold:
                break  # 已按相似度降序，后面只会更低
            item = dict(self.meta[idx])
            item["score"] = float(score)
            results.append(item)
        return results

    # ---------- 管理 ----------
    def clear(self):
        self._new_index(0 if self.index is None else self.index.d)
        self.meta = []
        self._save()

    def remove_document(self, doc_id: str) -> int:
        """删除某个文档的全部片段（重建索引）。返回删除的片段数。"""
        keep_meta = [m for m in self.meta if m.get("doc_id") != doc_id]
        removed = len(self.meta) - len(keep_meta)
        if removed == 0:
            return 0
        keep_embeddings = []
        # meta 与索引行一一对应，重建索引
        import faiss

        dim = self.index.d
        new_index = faiss.IndexFlatIP(dim)
        rows = {i for i, m in enumerate(self.meta) if m.get("doc_id") == doc_id}
        kept_rows = [i for i in range(self.count) if i not in rows]
        if dim > 0 and kept_rows:
            vectors = np.vstack([self.index.reconstruct(int(i)) for i in kept_rows])
            if vectors.shape[0]:
                new_index.add(vectors)
        self.index = new_index
        self.meta = keep_meta
        self._save()
        return removed

    def documents(self) -> list[dict]:
        """按文档聚合统计。"""
        docs: dict[str, dict] = {}
        for m in self.meta:
            doc = docs.setdefault(
                m["doc_id"],
                {"doc_id": m["doc_id"], "doc_name": m["doc_name"], "chunks": 0, "created_at": m["created_at"]},
            )
            doc["chunks"] += 1
        return sorted(docs.values(), key=lambda d: d["created_at"], reverse=True)

    @property
    def count(self) -> int:
        return len(self.meta)


def new_doc_id() -> str:
    return uuid.uuid4().hex[:12]
