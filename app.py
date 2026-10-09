"""本地大模型知识库 · Web 服务入口。

启动方式：python app.py
默认地址：http://127.0.0.1:8000
"""
from __future__ import annotations

import threading

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

import config
from rag.chunker import chunk_text
from rag.embeddings import Embedder
from rag.llm import OllamaClient
from rag.loader import load_document
from rag.pipeline import RAGPipeline
from rag.store import VectorStore, new_doc_id

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 单文件最大 50MB

# ---------- 全局对象 ----------
config.DATA_DIR.mkdir(parents=True, exist_ok=True)
config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
config.INDEX_DIR.mkdir(parents=True, exist_ok=True)

embedder = Embedder(config.EMBEDDING_MODEL, config.EMBEDDING_DEVICE)
store = VectorStore(config.INDEX_DIR)
llm = OllamaClient(config.OLLAMA_BASE_URL, config.LLM_MODEL)
pipeline = RAGPipeline(embedder, store, llm)

# 写操作（上传 / 清空 / 删除）需要串行，避免索引错乱
store_lock = threading.Lock()


# ---------- 页面 ----------
@app.get("/")
def index():
    return render_template("index.html")


# ---------- 知识库管理 ----------
@app.get("/api/documents")
def documents():
    return jsonify({"documents": store.documents(), "total_chunks": store.count})


@app.post("/api/upload")
def upload():
    """上传一个文档并入库。"""
    file = request.files.get("file")
    if file is None or not file.filename:
        return jsonify({"error": "未选择文件"}), 400

    filename = secure_filename(file.filename)
    ext = "." + (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        return jsonify({"error": f"不支持的文件类型 {ext}，支持：{sorted(config.ALLOWED_EXTENSIONS)}"}), 400

    save_path = config.UPLOAD_DIR / filename
    file.save(str(save_path))

    try:
        _, text = load_document(save_path)
        chunks = chunk_text(text)
        if not chunks:
            return jsonify({"error": "文档内容为空，无法入库"}), 400

        with store_lock:
            doc_id = new_doc_id()
            vectors = embedder.encode(chunks)
            added = store.add_chunks(doc_id, filename, chunks, vectors)

        return jsonify(
            {
                "doc_id": doc_id,
                "filename": filename,
                "chunks": added,
                "documents": store.documents(),
            }
        )
    except Exception as exc:
        return jsonify({"error": f"入库失败：{exc}"}), 500


@app.post("/api/load-samples")
def load_samples():
    """一键载入 docs/sample 下的示例文档，方便快速体验。"""
    from rag.loader import load_all

    loaded = []
    for name, text in load_all(config.BASE_DIR / "docs" / "sample"):
        chunks = chunk_text(text)
        with store_lock:
            doc_id = new_doc_id()
            vectors = embedder.encode(chunks)
            added = store.add_chunks(doc_id, name, chunks, vectors)
        loaded.append({"doc_id": doc_id, "filename": name, "chunks": added})
    return jsonify({"loaded": loaded, "documents": store.documents()})


@app.delete("/api/documents/<doc_id>")
def remove_document(doc_id: str):
    with store_lock:
        removed = store.remove_document(doc_id)
    if removed == 0:
        return jsonify({"error": "文档不存在"}), 404
    return jsonify({"removed_chunks": removed, "documents": store.documents()})


@app.post("/api/clear")
def clear():
    with store_lock:
        store.clear()
    return jsonify({"documents": [], "total_chunks": 0})


# ---------- 问答 ----------
@app.post("/api/query")
def query():
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"error": "问题不能为空"}), 400

    try:
        result = pipeline.ask(
            question,
            top_k=body.get("top_k"),
            threshold=body.get("threshold"),
        )
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": f"问答失败：{exc}"}), 500


# ---------- 状态与配置 ----------
@app.get("/api/health")
def health():
    return jsonify(
        {
            "ollama": llm.available(),
            "ollama_models": llm.models(),
            "llm_model": config.LLM_MODEL,
            "embedding_model": config.EMBEDDING_MODEL,
            "vector_count": store.count,
            "embedding_loaded": embedder.is_loaded,
        }
    )


@app.get("/api/config")
def get_config():
    return jsonify(
        {
            "top_k": config.TOP_K,
            "score_threshold": config.SCORE_THRESHOLD,
            "chunk_size": config.CHUNK_SIZE,
            "chunk_overlap": config.CHUNK_OVERLAP,
            "llm_model": config.LLM_MODEL,
            "embedding_model": config.EMBEDDING_MODEL,
        }
    )


if __name__ == "__main__":
    print(f"本地大模型知识库已启动：http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, threaded=True, debug=False)
