"""VectorStore 删除路径的回归测试。

用内存假 FAISS 索引避免测试环境必须安装 faiss-cpu；测试关注的是
meta / 索引行一致性，尤其是“删掉最后一个片段”时不能对空列表做 vstack。
"""
from __future__ import annotations

import sys
import types

import numpy as np
import pytest


class FakeIndex:
    def __init__(self, dim: int):
        self.d = int(dim)
        self.vectors = np.zeros((0, self.d), dtype=np.float32)

    def add(self, vectors: np.ndarray) -> None:
        vectors = np.asarray(vectors, dtype=np.float32)
        self.vectors = np.vstack([self.vectors, vectors]) if len(self.vectors) else vectors

    def reconstruct(self, row: int) -> np.ndarray:
        return self.vectors[row].copy()

    def search(self, queries: np.ndarray, k: int):
        scores = np.zeros((len(queries), k), dtype=np.float32)
        indices = np.full((len(queries), k), -1, dtype=np.int64)
        return scores, indices


@pytest.fixture
def fake_faiss(monkeypatch):
    module = types.ModuleType("faiss")
    module.IndexFlatIP = FakeIndex
    module.write_index = lambda index, path: None
    module.read_index = lambda path: (_ for _ in ()).throw(RuntimeError("unexpected load"))
    monkeypatch.setitem(sys.modules, "faiss", module)
    return module


@pytest.fixture
def store(tmp_path, fake_faiss):
    from rag.store import VectorStore

    return VectorStore(tmp_path / "index")


def test_remove_one_of_two_documents_keeps_the_other(store) -> None:
    vectors = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    store.add_chunks("doc-a", "A.txt", ["a1", "a2"], vectors)

    other = np.asarray([[0.7, 0.7]], dtype=np.float32)
    store.add_chunks("doc-b", "B.txt", ["b1"], other)

    removed = store.remove_document("doc-a")
    assert removed == 2
    assert store.count == 1
    assert store.documents()[0]["doc_id"] == "doc-b"
    assert store.index.d == 2
    np.testing.assert_allclose(store.index.reconstruct(0), [0.7, 0.7])


def test_remove_last_document_does_not_crash(store) -> None:
    store.add_chunks(
        "only-doc",
        "唯一文档.txt",
        ["唯一片段"],
        np.asarray([[1.0, 2.0]], dtype=np.float32),
    )

    removed = store.remove_document("only-doc")
    assert removed == 1
    assert store.count == 0
    assert store.documents() == []
    assert store.search(np.asarray([[1.0, 2.0]], dtype=np.float32), top_k=2) == []
    assert store.remove_document("only-doc") == 0
