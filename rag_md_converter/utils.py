from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while chunk := file_handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t\f\v]+", " ", text)
    text = re.sub(r"[ \u00a0]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip() + "\n" if text.strip() else ""


def escape_md_cell(value: object) -> str:
    string_value = "" if value is None else str(value)
    string_value = string_value.replace("\n", "<br>").replace("\r", "")
    return string_value.replace("|", "\\|").strip()


def table_to_markdown(rows: Sequence[Sequence[object]], max_cols: int | None = None) -> str:
    cleaned: list[list[str]] = []
    for row in rows:
        values = [escape_md_cell(value) for value in row]
        if max_cols is not None:
            values = values[:max_cols]
        if any(values):
            cleaned.append(values)
    if not cleaned:
        return ""

    width = max(len(row) for row in cleaned)
    cleaned = [row + [""] * (width - len(row)) for row in cleaned]
    header = [value or f"欄位{index + 1}" for index, value in enumerate(cleaned[0])]
    separator = ["---"] * width
    body = cleaned[1:]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines) + "\n"


def sniff_csv_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample)
    except csv.Error:
        return csv.excel


def unique_output_path(source: Path, output_dir: Path, overwrite: bool = False) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = source.stem or "document"
    source_type = source.suffix.lower().lstrip(".") or "file"
    target = output_dir / f"{stem}.{source_type}.md"
    if overwrite or not target.exists():
        return target

    short_hash = sha256_file(source)[:8]
    hashed_target = output_dir / f"{stem}.{source_type}__{short_hash}.md"
    if not hashed_target.exists():
        return hashed_target

    index = 2
    while True:
        candidate = output_dir / f"{stem}.{source_type}__{short_hash}_{index}.md"
        if not candidate.exists():
            return candidate
        index += 1


def remove_repeated_short_lines(text: str, min_count: int = 3, max_len: int = 120) -> str:
    lines = text.splitlines()
    normalized = [line.strip() for line in lines if 0 < len(line.strip()) <= max_len]
    counts = Counter(normalized)
    repeated = {line for line, count in counts.items() if count >= min_count}
    if not repeated:
        return text
    return "\n".join(line for line in lines if line.strip() not in repeated)


def frontmatter(source: Path, converter: str, warnings: Iterable[str]) -> str:
    warning_values = list(warnings)
    warning_block = "\n".join(
        f"  - {json.dumps(warning, ensure_ascii=False)}" for warning in warning_values
    ) or "  - none"
    return (
        "---\n"
        f"source_file: {json.dumps(source.name, ensure_ascii=False)}\n"
        f"source_extension: {json.dumps(source.suffix.lower())}\n"
        f"source_sha256: {sha256_file(source)}\n"
        f"converter: {json.dumps(converter)}\n"
        "warnings:\n"
        f"{warning_block}\n"
        "---\n\n"
    )
