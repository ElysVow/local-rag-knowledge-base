"""全局配置：所有可调参数集中在这里，也可通过环境变量覆盖。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
INDEX_DIR = DATA_DIR / "index"

# ---------- 向量化（Embedding） ----------
# 默认使用中英双语小模型 bge-small-zh-v1.5（约 100MB，CPU 即可跑）
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
# 设备：cpu / cuda；没有 NVIDIA 显卡时请保持 cpu
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

# ---------- 文档切分 ----------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))      # 每个片段目标字符数
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))  # 片段间重叠字符数

# ---------- 检索 ----------
TOP_K = int(os.getenv("TOP_K", "4"))           # 默认返回 Top-K 个片段
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.30"))  # 相似度阈值（余弦相似度）

# ---------- 大模型（Ollama） ----------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")   # 可换成 llama3.1:8b / qwen2.5:14b 等

# ---------- Web 服务 ----------
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

# 允许上传的文档类型
ALLOWED_EXTENSIONS = {".txt", ".md", ".markdown", ".pdf", ".docx"}

# 用于构造问答提示词的模板（上下文 + 问题）
SYSTEM_PROMPT = (
    "你是一个严谨的文档问答助手。请只依据下面提供的参考资料回答用户的问题；"
    "资料中没有的信息，请明确说明“根据现有知识库无法回答”，不要编造。"
    "回答使用简体中文，条理清晰，并在引用资料处标注来源编号，如 [1]、[2]。"
)
