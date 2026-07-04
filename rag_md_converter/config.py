from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ConverterConfig:
    """Bounded, local conversion settings used by the folder watcher."""

    output_dir: Path = Path("./output")
    recursive: bool = True
    overwrite: bool = False

    max_file_mb: int = 100
    max_zip_uncompressed_mb: int = 500
    max_zip_member_count: int = 5000
    max_image_pixels: int = 40_000_000

    max_output_chars: int = 2_000_000
    remove_repeated_lines: bool = True
    repeated_line_min_count: int = 3
    repeated_line_max_len: int = 120

    excel_max_rows_per_sheet: int = 5000
    excel_max_cols_per_sheet: int = 100
    csv_max_rows: int = 10_000
    csv_max_cols: int = 120

    json_max_items: int = 5000
    xml_max_nodes: int = 10_000
    xml_max_depth: int = 24

    ocr: bool = True
    ocr_lang: str = "eng+chi_tra"
    ocr_timeout_sec: int = 120
    pdf_max_pages: int = 500
    pdf_ocr_max_pages: int = 100
    pdf_ocr_dpi: int = 200

    enable_libreoffice: bool = True
    libreoffice_timeout_sec: int = 180

    allowed_extensions: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                ".docx", ".xlsx", ".pptx",
                ".doc", ".xls", ".ppt",
                ".pdf",
                ".html", ".htm",
                ".txt", ".csv", ".json", ".xml",
                ".md", ".markdown",
                ".png", ".jpg", ".jpeg",
            }
        )
    )
