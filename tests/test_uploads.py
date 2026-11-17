from __future__ import annotations

import pytest

from rag.uploads import UploadNameError, validate_upload_name


def test_chinese_filename_keeps_extension() -> None:
    # secure_filename 会把中文名压成 "txt"，这里必须保留原始文件名和扩展名。
    assert validate_upload_name("产品使用手册.txt") == ("产品使用手册.txt", ".txt")


def test_path_prefix_is_removed_but_name_kept() -> None:
    assert validate_upload_name(r"C:\fakepath\公司简介.md") == ("公司简介.md", ".md")
    assert validate_upload_name("../季度报告.docx") == ("季度报告.docx", ".docx")


def test_unsupported_extension_and_empty_name_are_rejected() -> None:
    with pytest.raises(UploadNameError, match="不支持"):
        validate_upload_name("恶意脚本.exe")
    with pytest.raises(UploadNameError, match="不能为空"):
        validate_upload_name("")
    with pytest.raises(UploadNameError, match="不能为空"):
        validate_upload_name(None)
