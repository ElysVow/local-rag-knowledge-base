/* 本地大模型知识库 · 前端逻辑 */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const els = {
    dropzone: $("dropzone"),
    fileInput: $("file-input"),
    btnSamples: $("btn-samples"),
    uploadStatus: $("upload-status"),
    docList: $("doc-list"),
    docEmpty: $("doc-empty"),
    docCount: $("doc-count"),
    topk: $("topk"),
    topkVal: $("topk-val"),
    threshold: $("threshold"),
    thrVal: $("thr-val"),
    cfgModel: $("cfg-model"),
    cfgEmbed: $("cfg-embed"),
    btnClear: $("btn-clear"),
    status: $("status"),
    statusText: $("status-text"),
    messages: $("messages"),
    question: $("question"),
    send: $("send"),
  };

  let busy = false;

  /* ---------- 工具 ---------- */
  async function api(path, options = {}) {
    const resp = await fetch(path, options);
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data.error || `请求失败 (${resp.status})`);
    return data;
  }

  function setStatus(state, text) {
    els.status.className = "status " + state;
    els.statusText.textContent = text;
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  /* ---------- 文档列表 ---------- */
  function renderDocs(documents) {
    els.docList.innerHTML = "";
    els.docCount.textContent = documents.length;
    els.docEmpty.style.display = documents.length ? "none" : "block";
    for (const doc of documents) {
      const li = el("li", "doc-item");
      const name = el("span", "doc-name", doc.doc_name);
      name.title = doc.doc_name;
      const chunks = el("span", "doc-chunks", `${doc.chunks} 段`);
      const del = el("button", "doc-del", "✕");
      del.title = "从知识库删除";
      del.addEventListener("click", async () => {
        if (!confirm(`确定从知识库中删除《${doc.doc_name}》？`)) return;
        try {
          await api(`/api/documents/${encodeURIComponent(doc.doc_id)}`, { method: "DELETE" });
          refreshDocs();
        } catch (err) { setUpload(err.message, "err"); }
      });
      li.append(name, chunks, del);
      els.docList.appendChild(li);
    }
  }

  async function refreshDocs() {
    try {
      const data = await api("/api/documents");
      renderDocs(data.documents);
    } catch { /* 服务未就绪时静默 */ }
  }

  /* ---------- 上传 ---------- */
  function setUpload(text, cls = "") {
    els.uploadStatus.textContent = text;
    els.uploadStatus.className = "upload-status" + (cls ? " " + cls : "");
  }

  async function uploadFile(file) {
    if (!file) return;
    if (busy) return;
    busy = true;
    els.send.disabled = true;
    setUpload(`正在入库 ${file.name} …（首次运行需加载向量模型，请耐心等待）`);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const data = await api("/api/upload", { method: "POST", body: fd });
      setUpload(`已入库《${data.filename}》，共 ${data.chunks} 个片段`, "ok");
      renderDocs(data.documents);
    } catch (err) {
      setUpload(err.message, "err");
    } finally {
      busy = false;
      els.send.disabled = false;
    }
  }

  els.dropzone.addEventListener("click", () => els.fileInput.click());
  els.fileInput.addEventListener("change", () => {
    uploadFile(els.fileInput.files[0]);
    els.fileInput.value = "";
  });
  ["dragenter", "dragover"].forEach((evt) =>
    els.dropzone.addEventListener(evt, (e) => { e.preventDefault(); els.dropzone.classList.add("drag"); })
  );
  ["dragleave", "drop"].forEach((evt) =>
    els.dropzone.addEventListener(evt, (e) => { e.preventDefault(); els.dropzone.classList.remove("drag"); })
  );
  els.dropzone.addEventListener("drop", (e) => uploadFile(e.dataTransfer.files[0]));

  els.btnSamples.addEventListener("click", async () => {
    if (busy) return;
    busy = true;
    els.btnSamples.disabled = true;
    setUpload("正在载入示例文档 …");
    try {
      const data = await api("/api/load-samples", { method: "POST" });
      const names = data.loaded.map((d) => d.filename).join("、");
      setUpload(`已载入：${names}`, "ok");
      renderDocs(data.documents);
    } catch (err) {
      setUpload(err.message, "err");
    } finally {
      busy = false;
      els.btnSamples.disabled = false;
    }
  });

  els.btnClear.addEventListener("click", async () => {
    if (!confirm("确定清空整个知识库？此操作不可撤销。")) return;
    try {
      await api("/api/clear", { method: "POST" });
      renderDocs([]);
      setUpload("知识库已清空", "ok");
    } catch (err) { setUpload(err.message, "err"); }
  });

  /* ---------- 问答 ---------- */
  function appendMessage(role, htmlNode) {
    const wrap = el("div", "msg " + role);
    const body = el("div", "msg-body");
    if (htmlNode) body.appendChild(htmlNode);
    wrap.appendChild(body);
    els.messages.appendChild(wrap);
    els.messages.scrollTop = els.messages.scrollHeight;
    return wrap;
  }

  function addSources(sources) {
    if (!sources || !sources.length) return null;
    const box = el("div", "sources");
    const toggle = el("button", "src-toggle", `查看引用来源（${sources.length} 条）`);
    let open = false;
    toggle.addEventListener("click", () => {
      open = !open;
      cards.forEach((c) => (c.style.display = open ? "" : "none"));
      toggle.textContent = open ? "收起引用来源" : `查看引用来源（${sources.length} 条）`;
    });
    box.appendChild(toggle);
    const cards = sources.map((s, i) => {
      const card = el("div", "src-card");
      const head = el("div", "src-head");
      head.append(
        el("span", "src-name", `${i + 1}. ${s.doc_name} · 第 ${s.chunk_index + 1} 段`),
        el("span", "src-score", `相似度 ${s.score.toFixed(3)}`)
      );
      const pre = el("pre", "", s.text);
      card.append(head, pre);
      card.style.display = "none";
      box.appendChild(card);
      return card;
    });
    return box;
  }

  async function ask(question) {
    const userMsg = appendMessage("user", document.createTextNode(question));
    const aiMsg = appendMessage("ai", null);
    const typing = el("div", "typing");
    typing.append(el("span"), el("span"), el("span"));
    aiMsg.querySelector(".msg-body").appendChild(typing);
    setStatus("busy", "思考中…");

    try {
      const data = await api("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          top_k: Number(els.topk.value),
          threshold: Number(els.threshold.value),
        }),
      });

      const body = aiMsg.querySelector(".msg-body");
      body.textContent = "";
      body.appendChild(document.createTextNode(data.answer));

      const meta = el("div", "msg-meta");
      const tag = el("span", "tag " + (data.mode === "llm" ? "llm" : "retrieval"), data.mode === "llm" ? "大模型回答" : "仅检索兜底");
      meta.append(tag, el("span", "", `模型 ${data.model} · ${data.latency_ms}ms`));
      aiMsg.appendChild(meta);

      const sources = addSources(data.sources);
      if (sources) aiMsg.appendChild(sources);
      setStatus("online", "就绪");
    } catch (err) {
      const body = aiMsg.querySelector(".msg-body");
      body.textContent = "";
      body.appendChild(document.createTextNode("出错了：" + err.message));
      setStatus("offline", "错误");
    }
  }

  function submit() {
    const q = els.question.value.trim();
    if (!q || busy) return;
    els.question.value = "";
    els.question.style.height = "auto";
    ask(q);
  }

  els.send.addEventListener("click", submit);
  els.question.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
  });
  els.question.addEventListener("input", () => {
    els.question.style.height = "auto";
    els.question.style.height = Math.min(els.question.scrollHeight, 140) + "px";
  });

  /* ---------- 设置 ---------- */
  els.topk.addEventListener("input", () => (els.topkVal.textContent = els.topk.value));
  els.threshold.addEventListener("input", () => (els.thrVal.textContent = Number(els.threshold.value).toFixed(2)));

  /* ---------- 初始化 ---------- */
  async function init() {
    try {
      const [health, cfg] = await Promise.all([api("/api/health"), api("/api/config")]);
      els.cfgModel.textContent = health.llm_model;
      els.cfgEmbed.textContent = cfg.embedding_model;
      els.topk.value = cfg.top_k; els.topkVal.textContent = cfg.top_k;
      els.threshold.value = cfg.score_threshold; els.thrVal.textContent = Number(cfg.score_threshold).toFixed(2);
      const online = health.ollama && health.ollama_models.includes(health.llm_model);
      if (online) setStatus("online", "Ollama 已连接");
      else if (health.ollama) setStatus("offline", "模型未就绪（在 Ollama 中拉取 " + health.llm_model + "）");
      else setStatus("offline", "Ollama 未连接，当前为仅检索模式");
      refreshDocs();
    } catch {
      setStatus("offline", "服务未就绪");
    }
  }

  init();
})();
