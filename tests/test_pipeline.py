"""管线冒烟测试：文档加载 → 切分 → 向量化 → 入库 → 检索。

运行方式：python tests/test_pipeline.py
说明：首次运行会下载 embedding 模型（约 100MB）。
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
from rag.embeddings import Embedder  # noqa: E402
from rag.loader import load_all  # noqa: E402
from rag.chunker import chunk_text  # noqa: E402
from rag.store import VectorStore, new_doc_id  # noqa: E402

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "docs" / "sample"


def main() -> int:
    failures = 0

    # 1) 加载
    docs = load_all(SAMPLE_DIR)
    assert len(docs) >= 2, f"示例文档加载数量异常: {len(docs)}"
    print(f"[ok] 加载 {len(docs)} 个示例文档")

    # 2) 切分
    chunk_counts = [len(chunk_text(text)) for _, text in docs]
    assert all(c > 0 for c in chunk_counts), f"切分结果异常: {chunk_counts}"
    print(f"[ok] 切分完成，各文档片段数: {chunk_counts}")

    # 3) 向量化 + 入库（使用临时索引目录）
    embedder = Embedder(config.EMBEDDING_MODEL, "cpu")
    tmp = Path(tempfile.mkdtemp(prefix="kb_test_"))
    try:
        store = VectorStore(tmp)
        for name, text in docs:
            chunks = chunk_text(text)
            vectors = embedder.encode(chunks)
            store.add_chunks(new_doc_id(), name, chunks, vectors)
        print(f"[ok] 向量化并入库 {store.count} 个片段")

        # 4) 检索：用文档中的真实事实提问
        query = "星云智能科技有限公司成立于哪一年？"
        emb = embedder.encode([query])
        hits = store.search(emb, top_k=3, threshold=0.1)
        assert hits, "检索结果为空"
        top_text = hits[0]["text"]
        print(f"[ok] 检索命中 {len(hits)} 条，Top-1 相似度 {hits[0]['score']:.3f}")

        # 5) 关键事实验证：Top-1 片段应包含答案
        assert "2019" in top_text, f"Top-1 片段未包含答案，实际: {top_text[:60]}..."
        print("[ok] Top-1 片段包含关键事实 '2019'")

        # 6) 持久化：重新加载应恢复
        store2 = VectorStore(tmp)
        assert store2.count == store.count, "持久化恢复失败"
        print(f"[ok] 索引持久化/恢复正常（{store2.count} 个片段）")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n全部通过 ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
