from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import BaseConverter
from ..config import ConverterConfig

LEGACY_TARGET = {".doc": ".docx", ".xls": ".xlsx", ".ppt": ".pptx"}


class LegacyOfficeConverter(BaseConverter):
    extensions = {".doc", ".xls", ".ppt"}
    name = "legacy-office-libreoffice"

    def convert(self, path: Path) -> str:
        raise NotImplementedError("Legacy Office 由 pipeline 先轉為 OOXML")


def libreoffice_convert(path: Path, config: ConverterConfig) -> tuple[Path, Path]:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("找不到 LibreOffice/soffice，無法轉換舊版 Office 檔")

    extension = path.suffix.lower()
    if extension not in LEGACY_TARGET:
        raise RuntimeError(f"不是舊版 Office 格式：{extension}")

    target_extension = LEGACY_TARGET[extension]
    filter_name = {".doc": "docx", ".xls": "xlsx", ".ppt": "pptx"}[extension]

    temp_root = Path(tempfile.mkdtemp(prefix="rag_lo_"))
    profile = temp_root / "profile"
    output_dir = temp_root / "out"
    output_dir.mkdir(parents=True, exist_ok=True)
    profile.mkdir(parents=True, exist_ok=True)

    environment = os.environ.copy()
    environment["HOME"] = str(profile)

    command = [
        soffice,
        "--headless",
        "--nologo",
        "--nodefault",
        "--nolockcheck",
        "--nofirststartwizard",
        f"-env:UserInstallation=file://{profile}",
        "--convert-to",
        filter_name,
        "--outdir",
        str(output_dir),
        str(path),
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=str(temp_root),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=config.libreoffice_timeout_sec,
            text=True,
            check=False,
        )
    except Exception:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise

    if completed.returncode != 0:
        shutil.rmtree(temp_root, ignore_errors=True)
        details = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"LibreOffice 轉換失敗：{details}")

    converted = output_dir / f"{path.stem}{target_extension}"
    if not converted.exists():
        candidates = list(output_dir.glob(f"*{target_extension}"))
        if not candidates:
            shutil.rmtree(temp_root, ignore_errors=True)
            raise RuntimeError("LibreOffice 未產生預期轉檔結果")
        converted = candidates[0]

    return converted, temp_root
