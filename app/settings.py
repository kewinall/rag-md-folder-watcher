from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from rag_md_converter.config import ConverterConfig


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Settings:
    data_root: Path
    input_dir: Path
    processing_dir: Path
    output_dir: Path
    archive_dir: Path
    failed_dir: Path
    state_dir: Path
    logs_dir: Path

    poll_interval_seconds: float
    stable_checks: int
    recursive: bool
    archive_source: bool
    write_metadata: bool
    write_done_marker: bool
    deduplicate: bool
    process_existing_on_start: bool
    log_level: str

    converter: ConverterConfig

    @classmethod
    def from_env(cls) -> "Settings":
        root = Path(os.getenv("DATA_ROOT", "/data")).expanduser()
        output_dir = root / os.getenv("OUTPUT_SUBDIR", "output")

        converter = ConverterConfig(
            output_dir=output_dir,
            recursive=env_bool("WATCH_RECURSIVE", True),
            overwrite=env_bool("OVERWRITE_OUTPUT", False),
            max_file_mb=env_int("MAX_FILE_MB", 100),
            max_zip_uncompressed_mb=env_int("MAX_ZIP_UNCOMPRESSED_MB", 500),
            max_zip_member_count=env_int("MAX_ZIP_MEMBER_COUNT", 5000),
            max_image_pixels=env_int("MAX_IMAGE_PIXELS", 40_000_000),
            max_output_chars=env_int("MAX_OUTPUT_CHARS", 2_000_000),
            remove_repeated_lines=env_bool("REMOVE_REPEATED_LINES", True),
            excel_max_rows_per_sheet=env_int("EXCEL_MAX_ROWS_PER_SHEET", 5000),
            excel_max_cols_per_sheet=env_int("EXCEL_MAX_COLS_PER_SHEET", 100),
            csv_max_rows=env_int("CSV_MAX_ROWS", 10_000),
            csv_max_cols=env_int("CSV_MAX_COLS", 120),
            json_max_items=env_int("JSON_MAX_ITEMS", 5000),
            xml_max_nodes=env_int("XML_MAX_NODES", 10_000),
            xml_max_depth=env_int("XML_MAX_DEPTH", 24),
            ocr=env_bool("OCR_ENABLED", True),
            ocr_lang=os.getenv("OCR_LANG", "eng+chi_tra"),
            ocr_timeout_sec=env_int("OCR_TIMEOUT_SEC", 120),
            pdf_max_pages=env_int("PDF_MAX_PAGES", 500),
            pdf_ocr_max_pages=env_int("PDF_OCR_MAX_PAGES", 100),
            pdf_ocr_dpi=env_int("PDF_OCR_DPI", 200),
            enable_libreoffice=env_bool("ENABLE_LIBREOFFICE", True),
            libreoffice_timeout_sec=env_int("LIBREOFFICE_TIMEOUT_SEC", 180),
        )

        return cls(
            data_root=root,
            input_dir=root / os.getenv("INPUT_SUBDIR", "input"),
            processing_dir=root / os.getenv("PROCESSING_SUBDIR", "processing"),
            output_dir=output_dir,
            archive_dir=root / os.getenv("ARCHIVE_SUBDIR", "archive"),
            failed_dir=root / os.getenv("FAILED_SUBDIR", "failed"),
            state_dir=root / os.getenv("STATE_SUBDIR", "state"),
            logs_dir=root / os.getenv("LOGS_SUBDIR", "logs"),
            poll_interval_seconds=env_float("POLL_INTERVAL_SECONDS", 3.0),
            stable_checks=env_int("STABLE_CHECKS", 3),
            recursive=env_bool("WATCH_RECURSIVE", True),
            archive_source=env_bool("ARCHIVE_SOURCE", True),
            write_metadata=env_bool("WRITE_METADATA", True),
            write_done_marker=env_bool("WRITE_DONE_MARKER", True),
            deduplicate=env_bool("DEDUPLICATE", False),
            process_existing_on_start=env_bool("PROCESS_EXISTING_ON_START", True),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            converter=converter,
        )
