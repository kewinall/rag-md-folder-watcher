from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify as md

from .base import BaseConverter


class HtmlConverter(BaseConverter):
    extensions = {".html", ".htm"}
    name = "html"

    def convert(self, path: Path) -> str:
        html = path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.decompose()
        title = soup.title.get_text(strip=True) if soup.title else path.stem
        body = soup.body or soup
        markdown = md(str(body), heading_style="ATX", bullets="-")
        return f"# {title}\n\n{markdown}\n"
