from __future__ import annotations

import zipfile
from pathlib import Path

from .config import ConverterConfig

OOXML_EXTENSIONS = {".docx", ".xlsx", ".pptx"}
LEGACY_OFFICE_EXTENSIONS = {".doc", ".xls", ".ppt"}


class SecurityError(RuntimeError):
    pass


def validate_input(path: Path, config: ConverterConfig) -> None:
    if not path.exists():
        raise SecurityError(f"檔案不存在：{path}")
    if not path.is_file():
        raise SecurityError(f"不是一般檔案：{path}")
    if path.is_symlink():
        raise SecurityError(f"拒絕處理 symbolic link：{path}")

    ext = path.suffix.lower()
    if ext not in config.allowed_extensions:
        raise SecurityError(f"不支援的副檔名：{ext}")

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > config.max_file_mb:
        raise SecurityError(f"檔案過大：{size_mb:.1f} MB > {config.max_file_mb} MB")

    if ext in LEGACY_OFFICE_EXTENSIONS and not config.enable_libreoffice:
        raise SecurityError(
            f"{ext} 是舊版 Office 格式；預設停用。若已在隔離環境，請加 --enable-libreoffice。"
        )

    if ext in OOXML_EXTENSIONS:
        validate_zip_container(path, config)


def validate_zip_container(path: Path, config: ConverterConfig) -> None:
    try:
        with zipfile.ZipFile(path) as zf:
            infos = zf.infolist()
            if len(infos) > config.max_zip_member_count:
                raise SecurityError(
                    f"OOXML zip entries 過多：{len(infos)} > {config.max_zip_member_count}"
                )
            total = 0
            for info in infos:
                total += info.file_size
                normalized = Path(info.filename)
                if normalized.is_absolute() or ".." in normalized.parts:
                    raise SecurityError(f"OOXML 內含可疑路徑：{info.filename}")
            total_mb = total / (1024 * 1024)
            if total_mb > config.max_zip_uncompressed_mb:
                raise SecurityError(
                    f"OOXML 解壓後過大：{total_mb:.1f} MB > {config.max_zip_uncompressed_mb} MB"
                )
    except zipfile.BadZipFile as exc:
        raise SecurityError(f"OOXML zip 結構不合法：{path.name}") from exc
