from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..config import ConverterConfig


class BaseConverter(ABC):
    extensions: set[str] = set()
    name: str = "base"

    def __init__(self, config: ConverterConfig):
        self.config = config
        self.warnings: list[str] = []

    @abstractmethod
    def convert(self, path: Path) -> str:
        raise NotImplementedError
