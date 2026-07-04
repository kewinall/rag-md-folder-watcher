from __future__ import annotations

from pathlib import Path

from .config import ConverterConfig
from .converters.base import BaseConverter
from .converters.excel import XlsxConverter
from .converters.html import HtmlConverter
from .converters.image import ImageConverter
from .converters.pdf import PdfConverter
from .converters.powerpoint import PptxConverter
from .converters.textlike import CsvConverter, JsonConverter, MarkdownConverter, PlainTextConverter, XmlConverter
from .converters.word import DocxConverter
from .converters.legacy_office import LegacyOfficeConverter

CONVERTER_CLASSES: tuple[type[BaseConverter], ...] = (
    PlainTextConverter,
    MarkdownConverter,
    CsvConverter,
    JsonConverter,
    XmlConverter,
    HtmlConverter,
    DocxConverter,
    XlsxConverter,
    PptxConverter,
    PdfConverter,
    ImageConverter,
    LegacyOfficeConverter,
)


def get_converter(path: Path, config: ConverterConfig) -> BaseConverter:
    ext = path.suffix.lower()
    for cls in CONVERTER_CLASSES:
        if ext in cls.extensions:
            return cls(config)
    raise ValueError(f"找不到 converter：{ext}")
