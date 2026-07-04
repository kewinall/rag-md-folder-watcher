from __future__ import annotations

from pathlib import Path

from PIL import Image

from .base import BaseConverter
from .ocr import ocr_available, ocr_image_path


class ImageConverter(BaseConverter):
    extensions = {".png", ".jpg", ".jpeg"}
    name = "image-ocr"

    def convert(self, path: Path) -> str:
        with Image.open(path) as image:
            width, height = image.size
            pixels = width * height
            if pixels > self.config.max_image_pixels:
                raise RuntimeError(
                    f"圖片像素過大：{pixels:,} > {self.config.max_image_pixels:,}"
                )
            image_format = image.format or path.suffix.lstrip(".").upper()

        lines = [
            f"# {path.stem}",
            "",
            "## 圖片資訊",
            f"- 格式：{image_format}",
            f"- 尺寸：{width} x {height}",
            "",
        ]

        if not self.config.ocr:
            self.warnings.append("OCR 已停用")
            return "\n".join(lines) + "\n"
        if not ocr_available():
            self.warnings.append("找不到 tesseract，無法執行 OCR")
            return "\n".join(lines) + "\n"

        try:
            text = ocr_image_path(path, self.config)
        except Exception as exc:
            self.warnings.append(f"OCR 失敗：{type(exc).__name__}: {exc}")
            text = ""

        lines.extend(["## OCR 文字", text or "（未辨識到文字）", ""])
        return "\n".join(lines) + "\n"
