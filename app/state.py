from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ProcessedIndex:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.by_sha256: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sha256 = item.get("source_sha256")
                if sha256:
                    self.by_sha256[sha256] = item

    def get(self, sha256: str) -> dict[str, Any] | None:
        return self.by_sha256.get(sha256)

    def append(self, item: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
            handle.flush()
        sha256 = item.get("source_sha256")
        if sha256:
            self.by_sha256[sha256] = item
