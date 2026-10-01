"""PDF to Markdown converter using MarkItDown."""

from pathlib import Path
from markitdown import MarkItDown
from file2md.converters.base import BaseConverter


class PdfConverter(BaseConverter):
    """Converts PDF documents to Markdown, preserving structure and tables."""

    def __init__(self) -> None:
        self._engine = MarkItDown()

    def convert(self, file_path: Path) -> str:
        result = self._engine.convert(str(file_path))
        content = result.text_content.strip()
        if not content:
            raise ValueError("PDF document contains no extractable text or structure.")
        return content
