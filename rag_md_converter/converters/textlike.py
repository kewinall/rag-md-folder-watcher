from __future__ import annotations

import csv
import json
from pathlib import Path

from defusedxml import ElementTree as SafeET

from .base import BaseConverter
from ..utils import sniff_csv_dialect, table_to_markdown


class PlainTextConverter(BaseConverter):
    extensions = {".txt"}
    name = "plain-text"

    def convert(self, path: Path) -> str:
        return f"# {path.stem}\n\n" + path.read_text(encoding="utf-8", errors="replace")


class MarkdownConverter(BaseConverter):
    extensions = {".md", ".markdown"}
    name = "markdown-pass-through"

    def convert(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")


class CsvConverter(BaseConverter):
    extensions = {".csv"}
    name = "csv"

    def convert(self, path: Path) -> str:
        sample = path.read_text(encoding="utf-8-sig", errors="replace")[:8192]
        dialect = sniff_csv_dialect(sample)
        rows = []
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
            reader = csv.reader(f, dialect)
            for idx, row in enumerate(reader):
                if idx >= self.config.csv_max_rows:
                    self.warnings.append(f"CSV 已截斷，只保留前 {self.config.csv_max_rows} 列")
                    break
                rows.append(row[: self.config.csv_max_cols])
        return f"# {path.stem}\n\n" + table_to_markdown(rows, self.config.csv_max_cols)


class JsonConverter(BaseConverter):
    extensions = {".json"}
    name = "json"

    def convert(self, path: Path) -> str:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        lines = [f"# {path.stem}", "", "```json"]
        lines.append(json.dumps(data, ensure_ascii=False, indent=2)[: self.config.max_output_chars])
        lines.append("```")
        return "\n".join(lines) + "\n"


class XmlConverter(BaseConverter):
    extensions = {".xml"}
    name = "xml"

    def convert(self, path: Path) -> str:
        root = SafeET.parse(path).getroot()
        lines = [f"# {path.stem}", ""]
        count = 0

        def walk(node, depth: int) -> None:
            nonlocal count
            if count >= self.config.xml_max_nodes:
                return
            if depth > self.config.xml_max_depth:
                return
            count += 1
            indent = "  " * depth
            attrs = " ".join([f'{k}="{v}"' for k, v in node.attrib.items()])
            text = (node.text or "").strip()
            label = node.tag if not attrs else f"{node.tag} ({attrs})"
            if text:
                lines.append(f"{indent}- **{label}**: {text}")
            else:
                lines.append(f"{indent}- **{label}**")
            for child in list(node):
                walk(child, depth + 1)

        walk(root, 0)
        if count >= self.config.xml_max_nodes:
            self.warnings.append(f"XML 已截斷，只保留前 {self.config.xml_max_nodes} 個節點")
        return "\n".join(lines) + "\n"
