from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Detection:
    kind: str
    canonical_extension: str | None
    confidence: str


OOXML_MARKERS = {
    "word/document.xml": ("word", ".docx"),
    "xl/workbook.xml": ("excel", ".xlsx"),
    "ppt/presentation.xml": ("powerpoint", ".pptx"),
}


def detect_format(path: Path) -> Detection:
    with path.open("rb") as file_handle:
        header = file_handle.read(16)

    if header.startswith(b"%PDF-"):
        return Detection("pdf", ".pdf", "high")
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return Detection("png", ".png", "high")
    if header.startswith(b"\xff\xd8\xff"):
        return Detection("jpeg", ".jpg", "high")
    if header.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as archive:
                members = set(archive.namelist())
            for marker, (kind, extension) in OOXML_MARKERS.items():
                if marker in members:
                    return Detection(kind, extension, "high")
        except zipfile.BadZipFile:
            return Detection("invalid-zip", None, "high")
        return Detection("zip", None, "medium")
    if header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return Detection("legacy-office", None, "medium")

    extension = path.suffix.lower()
    text_kinds = {
        ".html": "html", ".htm": "html",
        ".txt": "text", ".csv": "csv", ".json": "json",
        ".xml": "xml", ".md": "markdown", ".markdown": "markdown",
    }
    if extension in text_kinds:
        return Detection(text_kinds[extension], extension, "extension")

    return Detection("unknown", None, "low")


def validate_detected_format(path: Path) -> Detection:
    detection = detect_format(path)
    extension = path.suffix.lower()

    equivalent = {(".jpg", ".jpeg"), (".jpeg", ".jpg")}
    if detection.canonical_extension and detection.canonical_extension != extension:
        if (detection.canonical_extension, extension) not in equivalent:
            raise ValueError(
                "副檔名與檔案內容不一致："
                f"副檔名={extension}，偵測={detection.canonical_extension}"
            )

    if detection.kind == "legacy-office" and extension not in {".doc", ".xls", ".ppt"}:
        raise ValueError("偵測為舊版 Office，但副檔名不是 .doc/.xls/.ppt")
    if detection.kind == "invalid-zip":
        raise ValueError("檔案看似 ZIP/OOXML，但壓縮結構損壞")

    return detection
