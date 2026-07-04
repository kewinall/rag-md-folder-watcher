from __future__ import annotations

import os
import shutil
import traceback
from pathlib import Path

from .config import ConverterConfig
from .converters.legacy_office import LegacyOfficeConverter, libreoffice_convert
from .registry import get_converter
from .result import ConvertResult
from .security import validate_input
from .utils import frontmatter, normalize_text, remove_repeated_short_lines, unique_output_path


def _atomic_write_text(path: Path, content: str) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def convert_one(path: Path | str, config: ConverterConfig) -> ConvertResult:
    source = Path(path).expanduser().resolve()
    legacy_temp_root: Path | None = None

    try:
        validate_input(source, config)
        converter = get_converter(source, config)
        effective_source = source
        warnings: list[str] = []

        if isinstance(converter, LegacyOfficeConverter):
            effective_source, legacy_temp_root = libreoffice_convert(source, config)
            converter = get_converter(effective_source, config)
            warnings.append("已使用 LibreOffice 將舊版 Office 轉為 OOXML 後擷取")

        markdown_body = converter.convert(effective_source)
        warnings.extend(converter.warnings)

        if config.remove_repeated_lines:
            markdown_body = remove_repeated_short_lines(
                markdown_body,
                min_count=config.repeated_line_min_count,
                max_len=config.repeated_line_max_len,
            )

        markdown_body = normalize_text(markdown_body)
        if len(markdown_body) > config.max_output_chars:
            markdown_body = markdown_body[: config.max_output_chars]
            warnings.append(f"輸出已截斷為前 {config.max_output_chars} 字元")

        output_path = unique_output_path(source, config.output_dir, config.overwrite)
        content = frontmatter(source, converter.name, warnings) + markdown_body
        _atomic_write_text(output_path, content)

        return ConvertResult(
            source_path=source,
            output_path=output_path,
            success=True,
            converter=converter.name,
            warnings=warnings,
            chars_written=len(content),
        )
    except Exception as exc:
        return ConvertResult(
            source_path=source,
            output_path=None,
            success=False,
            converter="unknown",
            error=f"{type(exc).__name__}: {exc}",
            warnings=[traceback.format_exc(limit=3)],
        )
    finally:
        if legacy_temp_root is not None:
            shutil.rmtree(legacy_temp_root, ignore_errors=True)


def iter_input_files(input_path: Path, config: ConverterConfig) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if not input_path.is_dir():
        raise FileNotFoundError(f"找不到輸入路徑：{input_path}")
    pattern = "**/*" if config.recursive else "*"
    return [
        candidate
        for candidate in input_path.glob(pattern)
        if candidate.is_file()
        and not candidate.is_symlink()
        and candidate.suffix.lower() in config.allowed_extensions
    ]


def convert_path(input_path: Path | str, config: ConverterConfig) -> list[ConvertResult]:
    root = Path(input_path).expanduser().resolve()
    return [convert_one(file_path, config) for file_path in iter_input_files(root, config)]
