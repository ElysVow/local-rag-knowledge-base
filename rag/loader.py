"""文档加载器：把不同类型的文件解析成纯文本。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

SUPPORTED = {".txt", ".md", ".markdown", ".pdf", ".docx"}


def _read_text_file(path: Path) -> str:
    """优先按 UTF-8 读取，失败后回退到 GBK（兼容 Windows 上的中文文件）。"""
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    # 最后兜底：忽略无法解码的字节
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def _read_docx(path: Path) -> str:
    import docx

    document = docx.Document(str(path))
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            parts.append(" | ".join(cells))
    return "\n".join(parts)


def load_document(path: str | Path) -> tuple[str, str]:
    """加载单个文档，返回 (文件名, 纯文本)。

    Raises:
        ValueError: 文件类型不支持或内容为空。
    """
    path = Path(path)
    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        raise ValueError(f"不支持的文件类型: {ext}（支持 {sorted(SUPPORTED)}）")

    if ext in (".pdf",):
        text = _read_pdf(path)
    elif ext in (".docx",):
        text = _read_docx(path)
    else:
        text = _read_text_file(path)

    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not text.strip():
        raise ValueError(f"文档内容为空: {path.name}")

    return path.name, text


def load_all(directory: str | Path) -> list[tuple[str, str]]:
    """加载目录下所有支持的文档，逐个返回 (文件名, 文本)。"""
    results: list[tuple[str, str]] = []
    directory = Path(directory)
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() in SUPPORTED:
            try:
                results.append(load_document(f))
            except Exception as exc:  # 单个文件失败不影响其它文件
                print(f"[loader] 跳过 {f.name}: {exc}")
    return results
