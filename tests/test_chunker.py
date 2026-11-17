from __future__ import annotations

from rag.chunker import chunk_text


def test_long_paragraph_is_split_with_overlap() -> None:
    text = "这是一段用于测试切分的中文内容。" * 80
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert all(len(chunk) <= 500 for chunk in chunks)
    # 相邻片段应保留重叠，而不是简单按固定长度硬切。
    assert chunks[0][-50:] == chunks[1][:50]
