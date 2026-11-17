# 本地大模型知识库（Local RAG Knowledge Base）

> **历史原型说明**：这是早期 Flask + FAISS 实现，保留作为学习与对照。
> 功能更完整、界面更现代的版本请见 [LocalDocQA](https://github.com/ElysVow/LocalDocQA)。

> 基于 **Llama3 / Qwen 等本地大模型** + RAG（检索增强生成）的文档问答系统。
> 文档全部保存在本地，问答全程离线，网页版界面开箱即用。

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Ollama](https://img.shields.io/badge/LLM-Ollama%20%28Llama3%20%2F%20Qwen%29-orange)

---

## 📖 项目简介

把 **PDF、Word、Markdown、TXT** 等文档丢进知识库，就能用自然语言提问，系统会：

1. 从知识库中**检索**最相关的文档片段（向量相似度）；
2. 把片段交给本地大模型（Ollama 运行 Llama3 / Qwen 等）**生成**带引用来源的回答；
3. 网页界面展示回答 + 引用片段，可一键查看原文出处。

数据不出本机、无需 API Key、无使用成本，适合个人知识管理、企业私有文档问答等场景。

## ✨ 功能特性

- 🧩 **纯本地 RAG 管线**：加载 → 切分 → 向量化 → 检索 → 生成，全部在本机完成
- 🖥️ **网页版聊天界面**：文档拖拽上传、实时问答、引用来源展示、参数可调
- 📄 **多格式支持**：`.txt` `.md` `.markdown` `.pdf` `.docx`
- 🔍 **语义检索**：基于 `bge-small-zh-v1.5` 中英双语向量模型 + FAISS 余弦相似度
- 🤖 **模型可切换**：支持 Ollama 上的任意模型（qwen2.5 / llama3.1 / deepseek-r1 等）
- 🛟 **无模型兜底模式**：没装大模型也能跑通检索，装上 Ollama 后无缝升级
- 💾 **索引持久化**：重启服务后知识库自动恢复，无需重新入库
- 🌐 **中英双语**：向量模型与系统提示词均兼容中英文内容

## 🏗️ 架构与工作原理

```
┌─────────────────────────────── 用户浏览器 ───────────────────────────────┐
│                          网页聊天界面（HTML/JS）                            │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │ HTTP (Flask)
┌──────────────────────────────────▼───────────────────────────────────────┐
│                              Web 服务 (app.py)                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│   │ 文档加载  │→ │ 文本切分  │→ │  向量化   │→ │ FAISS 检索│→ │  LLM 生成 │  │
│   │ loader   │  │ chunker  │  │embedding │  │  store   │  │  llm     │  │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└───────────────┬───────────────────────────────┬──────────────────────────┘
                │                               │
        data/uploads（原始文档）         data/index（向量索引+元数据）
                │                               │
        文档入库时写入                        Ollama 本地大模型
                                        (qwen2.5 / llama3.1 / ...)
```

**问答流程（RAG）**：

```
用户提问 ──► 问题向量化 ──► FAISS 语义检索 Top-K 片段
                              │
                              ▼
                拼接为上下文（标注来源编号 [1][2]...）
                              │
                              ▼
              Ollama 本地大模型生成回答（仅依据上下文）
                              │
                              ▼
        回答 + 引用来源片段 → 展示在网页界面
```

## 🧰 技术栈

| 模块 | 技术选型 | 说明 |
|---|---|---|
| 后端 | Python 3.10+ / Flask | 轻量 Web 服务 |
| 向量化 | sentence-transformers + `BAAI/bge-small-zh-v1.5` | 中英双语，CPU 可跑，约 100MB |
| 向量检索 | FAISS（`IndexFlatIP`） | 余弦相似度，本地持久化 |
| 大模型 | Ollama（qwen2.5:7b 默认） | 支持 Llama3 / Qwen / DeepSeek 等 |
| 文档解析 | pypdf / python-docx | PDF 与 Word |
| 前端 | 原生 HTML / CSS / JS | 无构建步骤，零依赖 |

## 🚀 快速开始

### 1. 环境要求

- **Python 3.10+**
- **[Ollama](https://ollama.com/download)**（大模型运行时）

### 2. 安装 Ollama 并拉取模型

```bash
# Windows / macOS / Linux 通用（也可直接到 ollama.com 下载安装包）
ollama pull qwen2.5:7b        # 中文效果好，通用推荐（约 4.5GB）
# 可选其它模型：
# ollama pull qwen2.5:3b      # 低配机器推荐
# ollama pull llama3.1:8b     # 英文效果好
# ollama pull deepseek-r1:7b  # 推理能力较强
```

> Windows 用户也可以直接双击 `scripts/setup_ollama.bat`。
>
> 💡 **国内网络提示**：向量模型默认从 Hugging Face 下载（约 100MB），国内可能超时。
> 执行下面的命令切换到 hf-mirror 镜像即可（Ollama 模型本身不走此通道）：
>
> ```bash
> # Windows (PowerShell)
> $env:HF_ENDPOINT = "https://hf-mirror.com"
> # macOS / Linux
> export HF_ENDPOINT=https://hf-mirror.com
> ```

### 3. 安装 Python 依赖

```bash
git clone https://github.com/ElysVow/local-rag-knowledge-base.git
cd local-rag-knowledge-base

# 建议使用虚拟环境（可选但推荐）
python -m venv venv
# Windows: venv\Scripts\activate    macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
```

### 4. 启动

```bash
python app.py
# 或 Windows 用户双击 scripts\start.bat
```

浏览器打开 **http://127.0.0.1:8000** 即可使用。

### 5. 快速体验

1. 点击左侧 **“载入示例文档”**，一键导入 3 份演示文档；
2. 在下方输入框提问，例如：
   - “星云智能科技有限公司成立于哪一年？”
   - “系统支持哪些文档格式？”
   - “这个项目需要联网吗？”
3. 回答下方点击 **“查看引用来源”**，可以看到每条回答对应的原文片段与相似度。

## 🖥️ 网页使用说明

| 功能 | 操作 |
|---|---|
| 上传文档 | 拖拽文件到左侧上传区，或点击选择（支持 txt/md/pdf/docx，≤50MB） |
| 删除文档 | 悬停文档列表项，点击 ✕ |
| 载入示例 | 点击“载入示例文档” |
| 清空知识库 | 点击“清空知识库”（不可撤销） |
| 调节检索 | 左侧 Top-K 与相似度阈值滑块，实时生效 |
| 查看引用 | 回答下方点击“查看引用来源”，展示原文片段与相似度 |

## ⚙️ 配置说明

所有参数可用**环境变量**覆盖，或在 `config.py` 中直接修改：

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `EMBEDDING_MODEL` | `BAAI/bge-small-zh-v1.5` | 向量模型（Hugging Face 名称） |
| `EMBEDDING_DEVICE` | `cpu` | 向量模型设备（有 NVIDIA 显卡可设 `cuda`） |
| `LLM_MODEL` | `qwen2.5:7b` | 问答大模型（Ollama 模型名） |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama 服务地址 |
| `CHUNK_SIZE` | `500` | 文档切分目标字符数 |
| `CHUNK_OVERLAP` | `50` | 切分片段重叠字符数 |
| `TOP_K` | `4` | 每次回答检索的片段数量 |
| `SCORE_THRESHOLD` | `0.30` | 相似度阈值（低于该值不采纳） |
| `HOST` / `PORT` | `127.0.0.1` / `8000` | 服务监听地址与端口 |

示例（Windows PowerShell）：

```powershell
$env:LLM_MODEL = "llama3.1:8b"
python app.py
```

## 📁 项目结构

```
local-rag-knowledge-base/
├── app.py                  # Flask Web 服务入口
├── config.py               # 全局配置（支持环境变量覆盖）
├── rag/                    # 核心 RAG 管线
│   ├── loader.py           #   文档加载（txt/md/pdf/docx → 文本）
│   ├── uploads.py          #   上传文件名清洗与扩展名校验
│   ├── chunker.py          #   文本切分（按段落 + 重叠）
│   ├── embeddings.py       #   向量化（sentence-transformers）
│   ├── store.py            #   向量库（FAISS + 元数据持久化）
│   ├── llm.py              #   Ollama 大模型客户端
│   └── pipeline.py         #   问答管线（检索 + 生成 + 兜底）
├── templates/index.html    # 网页界面
├── static/                 # 前端样式与逻辑
├── docs/sample/            # 示例文档（一键载入体验）
├── scripts/
│   ├── setup_ollama.bat    #   Windows 一键拉取模型
│   └── start.bat           #   Windows 一键启动
├── tests/test_pipeline.py  # 管线冒烟测试
└── data/                   # 运行时数据（已 gitignore）
    ├── uploads/            #   上传的原始文档
    └── index/              #   向量索引 + 元数据
```

## 🔌 API 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 网页界面 |
| GET | `/api/health` | 服务与 Ollama 状态 |
| GET | `/api/config` | 当前配置 |
| GET | `/api/documents` | 已入库文档列表 |
| POST | `/api/upload` | 上传文档并入库（multipart，字段 `file`） |
| POST | `/api/load-samples` | 载入示例文档 |
| DELETE | `/api/documents/<doc_id>` | 删除指定文档 |
| POST | `/api/clear` | 清空知识库 |
| POST | `/api/query` | 提问，JSON：`{"question": "...", "top_k": 4, "threshold": 0.3}` |

## 🧪 测试

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

覆盖：文件名清洗与中文文件名、文本切分、向量库删除（含删除最后一个文档）、
索引持久化恢复。原来的 `tests/test_pipeline.py` 是手动冒烟脚本，仍可用
`python tests/test_pipeline.py` 运行（首次运行需下载向量模型约 100MB）。

## ❓ 常见问题

**提问后显示“仅检索兜底”？**
未连接 Ollama。请先安装并启动 Ollama（`ollama serve`），确认 `ollama list` 中有对应模型。

**首次启动时向量模型下载失败 / 超时？**
国内网络请先设置 `HF_ENDPOINT=https://hf-mirror.com`（见快速开始），再重新启动。

**对电脑配置有要求吗？**
建议 8GB 内存起步；跑 7B 模型建议 16GB。无独立显卡时模型由 CPU 运行，速度较慢，可换 `qwen2.5:3b`。

**换 embedding 模型后报“向量维度不一致”？**
不同向量模型输出维度不同，先“清空知识库”再重新上传即可。

**数据安全吗？**
安全。文档与索引只保存在本地 `data/` 目录，问答全程离线。

**回答引用了无关内容？**
调低 Top-K 或调高相似度阈值；或调整 `CHUNK_SIZE` 改变切分粒度。

## 🗺️ Roadmap

- [ ] 流式输出（打字机效果）
- [ ] 支持多轮对话记忆
- [ ] 更多文档格式（Excel、图片 OCR）
- [ ] 批量文档上传
- [ ] 基于网页/链接的在线抓取入库
- [ ] Docker 一键部署

## 📄 许可证

[MIT](LICENSE)
