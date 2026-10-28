"""MarkItDown-backed document converter with configurable empty-content message."""

from pathlib import Path

from markitdown import MarkItDown

from file2md.converters.base import BaseConverter


class MarkItDownConverter(BaseConverter):
    """Generic MarkItDown converter for text, PDF, DOCX, HTML, and CSV documents."""

    def __init__(
        self, empty_message: str = "Document contains no extractable content."
    ) -> None:
        self._engine = MarkItDown()
        self._empty_message = empty_message

    def convert(self, file_path: Path) -> str:
        result = self._engine.convert(str(file_path))
        content = result.text_content.strip()
        if not content:
            raise ValueError(self._empty_message)
        return content
