from __future__ import annotations

import io
import shutil
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from ..config import ConverterConfig


class UnsupportedImageForOcr(ValueError):
    """Raised when an embedded Office image cannot safely be decoded for OCR."""


_VECTOR_SUFFIXES = {".emf", ".wmf", ".svg", ".wdp"}
_VECTOR_CONTENT_TYPES = {
    "image/emf",
    "image/x-emf",
    "image/wmf",
    "image/x-wmf",
    "image/svg+xml",
    "image/vnd.ms-photo",
    "application/x-msmetafile",
}


def ocr_available() -> bool:
    return bool(shutil.which("tesseract"))


def _prepare_for_tesseract(image: Image.Image) -> Image.Image:
    """Normalize orientation, animation and transparency before invoking Tesseract."""
    image.seek(0)
    normalized = ImageOps.exif_transpose(image)

    if normalized.mode in {"RGBA", "LA"} or "transparency" in normalized.info:
        rgba = normalized.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background

    if normalized.mode not in {"RGB", "L"}:
        return normalized.convert("RGB")

    return normalized.copy()


def ocr_pil_image(image: Image.Image, config: ConverterConfig) -> str:
    if not config.ocr or not ocr_available():
        return ""

    image.load()
    pixels = image.width * image.height
    if pixels > config.max_image_pixels:
        raise RuntimeError(
            f"圖片像素過大：{pixels:,} > {config.max_image_pixels:,}"
        )

    prepared = _prepare_for_tesseract(image)
    try:
        import pytesseract

        return pytesseract.image_to_string(
            prepared,
            lang=config.ocr_lang,
            timeout=config.ocr_timeout_sec,
        ).strip()
    finally:
        prepared.close()


def _looks_like_svg(data: bytes) -> bool:
    head = data[:4096].lstrip().lower()
    return head.startswith(b"<svg") or (
        head.startswith(b"<?xml") and b"<svg" in head
    )


def _rasterize_svg(data: bytes, config: ConverterConfig) -> bytes:
    """Render SVG to PNG with the already-required PyMuPDF dependency."""
    import fitz

    document = fitz.open(stream=data, filetype="svg")
    try:
        if document.page_count < 1:
            raise UnsupportedImageForOcr("SVG 沒有可渲染頁面")

        page = document[0]
        zoom = max(1.0, min(4.0, config.pdf_ocr_dpi / 72.0))
        estimated_pixels = int(page.rect.width * zoom) * int(page.rect.height * zoom)
        if estimated_pixels > config.max_image_pixels:
            raise RuntimeError(
                f"SVG 渲染像素過大：{estimated_pixels:,} > "
                f"{config.max_image_pixels:,}"
            )

        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(zoom, zoom),
            alpha=False,
        )
        return pixmap.tobytes("png")
    finally:
        document.close()


def _unsupported_vector_reason(
    source_name: str | None,
    content_type: str | None,
) -> str | None:
    suffix = Path(source_name or "").suffix.lower()
    normalized_content_type = (content_type or "").lower().split(";", 1)[0].strip()

    if suffix == ".svg" or normalized_content_type == "image/svg+xml":
        return None

    if suffix in _VECTOR_SUFFIXES or normalized_content_type in _VECTOR_CONTENT_TYPES:
        display_type = normalized_content_type or suffix or "未知向量格式"
        return f"Linux 容器暫不支援此向量/特殊圖片 OCR：{display_type}"

    return None


def ocr_image_path(path: Path, config: ConverterConfig) -> str:
    with Image.open(path) as image:
        return ocr_pil_image(image, config)


def ocr_image_bytes(
    data: bytes,
    config: ConverterConfig,
    *,
    source_name: str | None = None,
    content_type: str | None = None,
) -> str:
    if not data:
        raise UnsupportedImageForOcr("圖片內容為空")

    unsupported_reason = _unsupported_vector_reason(source_name, content_type)
    if unsupported_reason:
        raise UnsupportedImageForOcr(unsupported_reason)

    payload = data
    suffix = Path(source_name or "").suffix.lower()
    normalized_content_type = (content_type or "").lower().split(";", 1)[0].strip()
    if suffix == ".svg" or normalized_content_type == "image/svg+xml" or _looks_like_svg(data):
        try:
            payload = _rasterize_svg(data, config)
        except Exception as exc:
            if isinstance(exc, (RuntimeError, UnsupportedImageForOcr)):
                raise
            raise UnsupportedImageForOcr(
                f"SVG 無法渲染：{type(exc).__name__}: {exc}"
            ) from exc

    try:
        with Image.open(io.BytesIO(payload)) as image:
            return ocr_pil_image(image, config)
    except UnidentifiedImageError as exc:
        suffix_text = suffix or "無副檔名"
        content_type_text = normalized_content_type or "無 content-type"
        signature = data[:12].hex()
        raise UnsupportedImageForOcr(
            "Pillow 無法辨識圖片；"
            f"名稱={source_name or '未知'}，副檔名={suffix_text}，"
            f"content-type={content_type_text}，signature={signature}"
        ) from exc
