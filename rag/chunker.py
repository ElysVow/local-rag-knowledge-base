"""文本切分：把长文档切成适合检索与喂给大模型的片段。"""
from __future__ import annotations

from typing import Iterator

from config import CHUNK_OVERLAP, CHUNK_SIZE


def _split_paragraphs(text: str) -> list[str]:
    """按空行切成段落，并合并过短的段落。"""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    merged: list[str] = []
    for p in paragraphs:
        if merged and len(merged[-1]) < CHUNK_SIZE // 2 and len(merged[-1]) + len(p) <= CHUNK_SIZE:
            merged[-1] = merged[-1] + "\n" + p
        else:
            merged.append(p)
    return merged


def _split_long_paragraph(paragraph: str) -> list[str]:
    """把超长段落按目标长度 + 重叠切分。"""
    if len(paragraph) <= CHUNK_SIZE:
        return [paragraph]
    step = CHUNK_SIZE - CHUNK_OVERLAP
    parts = []
    start = 0
    while start < len(paragraph):
        parts.append(paragraph[start:start + CHUNK_SIZE])
        start += step
    return parts


def chunk_text(text: str) -> list[str]:
    """把整篇文档切成带重叠的片段列表。"""
    chunks: list[str] = []
    for paragraph in _split_paragraphs(text):
        chunks.extend(_split_long_paragraph(paragraph))
    # 去重且保持顺序
    seen: set[str] = set()
    unique = []
    for c in chunks:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique or [text]


def chunk_with_index(text: str) -> Iterator[tuple[int, str]]:
    """返回 (片段序号, 片段文本)。"""
    for i, c in enumerate(chunk_text(text)):
        yield i, c
