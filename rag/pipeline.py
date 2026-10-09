"""RAG 问答管线：检索 + 构造上下文 + 大模型生成，并支持无模型兜底。"""
from __future__ import annotations

import time
from typing import Optional

from config import (
    LLM_MODEL,
    OLLAMA_BASE_URL,
    SCORE_THRESHOLD,
    SYSTEM_PROMPT,
    TOP_K,
)
from rag.embeddings import Embedder
from rag.llm import OllamaClient
from rag.store import VectorStore


def _format_context(hits: list[dict]) -> str:
    lines = []
    for i, hit in enumerate(hits, start=1):
        lines.append(f"[{i}] 来自《{hit['doc_name']}》第 {hit['chunk_index'] + 1} 段：\n{hit['text']}")
    return "\n\n".join(lines)


class RAGPipeline:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        llm: Optional[OllamaClient] = None,
    ):
        self.embedder = embedder
        self.store = store
        self.llm = llm or OllamaClient(OLLAMA_BASE_URL, LLM_MODEL)

    def ask(self, question: str, top_k: Optional[int] = None, threshold: Optional[float] = None) -> dict:
        """回答一个问题，返回：
        {
          "answer": str,
          "mode": "llm" | "retrieval-only" | "no-hit",
          "sources": [{doc_name, chunk_index, text, score}],
          "model": str,
          "latency_ms": int,
        }
        """
        start = time.time()
        top_k = top_k or TOP_K
        threshold = SCORE_THRESHOLD if threshold is None else threshold
        question = (question or "").strip()

        if not question:
            return {
                "answer": "请输入问题。",
                "mode": "no-hit",
                "sources": [],
                "model": self.llm.model,
                "latency_ms": 0,
            }

        query_emb = self.embedder.encode([question])
        hits = self.store.search(query_emb, top_k=top_k, threshold=threshold)

        if not hits:
            answer = "知识库中没有找到与问题相关的内容。请先上传相关文档，或换一种问法。"
            return {
                "answer": answer,
                "mode": "no-hit",
                "sources": [],
                "model": self.llm.model,
                "latency_ms": int((time.time() - start) * 1000),
            }

        context = _format_context(hits)
        user_prompt = (
            f"参考资料：\n{context}\n\n"
            f"用户问题：{question}\n\n"
            "请基于参考资料回答问题。"
        )

        answer = self.llm.generate(SYSTEM_PROMPT, user_prompt) if self.llm.available() else None

        if answer is None:
            # 无模型兜底：直接给出检索到的原文摘要，保证流程可用
            parts = [f"（未连接大模型，以下为检索到的相关原文片段 {len(hits)} 条）"]
            for i, hit in enumerate(hits, start=1):
                snippet = hit["text"] if len(hit["text"]) <= 300 else hit["text"][:300] + "……"
                parts.append(f"[{i}] {snippet}")
            answer = "\n\n".join(parts)
            mode = "retrieval-only"
        else:
            mode = "llm"

        sources = [
            {
                "doc_name": h["doc_name"],
                "doc_id": h["doc_id"],
                "chunk_index": h["chunk_index"],
                "text": h["text"],
                "score": round(h["score"], 4),
            }
            for h in hits
        ]

        return {
            "answer": answer,
            "mode": mode,
            "sources": sources,
            "model": self.llm.model,
            "latency_ms": int((time.time() - start) * 1000),
        }
