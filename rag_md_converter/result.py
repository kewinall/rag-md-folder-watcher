from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConvertResult:
    source_path: Path
    output_path: Path | None
    success: bool
    converter: str
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
    chars_written: int = 0
