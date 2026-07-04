from __future__ import annotations

import io
from pathlib import Path

import fitz
from PIL import Image

from .base import BaseConverter
from .ocr import ocr_available, ocr_pil_image


class PdfConverter(BaseConverter):
    extensions = {".pdf"}
    name = "pdf-pymupdf-ocr"

    def convert(self, path: Path) -> str:
        lines: list[str] = [f"# {path.stem}", ""]
        ocr_pages = 0

        with fitz.open(str(path)) as document:
            if document.needs_pass:
                raise RuntimeError("PDF 有密碼保護，無法處理")

            page_count = min(len(document), self.config.pdf_max_pages)
            if len(document) > page_count:
                self.warnings.append(
                    f"PDF 已截斷，只保留前 {self.config.pdf_max_pages} 頁"
                )

            for page_index in range(page_count):
                page_number = page_index + 1
                page = document[page_index]
                text = page.get_text("text", sort=True).strip()

                if not text and self.config.ocr and ocr_available():
                    if ocr_pages < self.config.pdf_ocr_max_pages:
                        try:
                            zoom = self.config.pdf_ocr_dpi / 72.0
                            pixmap = page.get_pixmap(
                                matrix=fitz.Matrix(zoom, zoom),
                                alpha=False,
                            )
                            with Image.open(io.BytesIO(pixmap.tobytes("png"))) as image:
                                text = ocr_pil_image(image, self.config)
                            ocr_pages += 1
                        except Exception as exc:
                            self.warnings.append(
                                f"第 {page_number} 頁 OCR 失敗："
                                f"{type(exc).__name__}: {exc}"
                            )
                    else:
                        self.warnings.append(
                            f"掃描 PDF OCR 已達 {self.config.pdf_ocr_max_pages} 頁上限"
                        )

                lines.append(f"## 第 {page_number} 頁")
                lines.append(text or "（未擷取或辨識到文字）")
                lines.append("")

        return "\n".join(lines) + "\n"
