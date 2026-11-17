"""上传文件名校验。

只取原始文件名的 basename，保留中文等字符用于界面展示；扩展名单独返回，
供服务端生成安全的唯一存储路径。不要把用户文件名直接拼进路径。
"""
from __future__ import annotations

from pathlib import Path

from config import ALLOWED_EXTENSIONS


class UploadNameError(ValueError):
    """上传文件名不合法。"""


def validate_upload_name(filename: str | None) -> tuple[str, str]:
    """返回 (用于展示的原始文件名, 小写扩展名)。

    Raises:
        UploadNameError: 文件名为空或扩展名不受支持。
    """
    original = Path(str(filename or "").replace("\\", "/")).name.strip()
    if not original or original in {".", ".."}:
        raise UploadNameError("文件名不能为空")

    suffix = Path(original).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise UploadNameError(
            f"不支持的文件类型 {suffix or '(无扩展名)'}，"
            f"支持：{sorted(ALLOWED_EXTENSIONS)}"
        )
    return original, suffix
