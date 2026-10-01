"""Word (.docx) to Markdown converter using MarkItDown."""

from pathlib import Path
from markitdown import MarkItDown
from file2md.converters.base import BaseConverter


class DocxConverter(BaseConverter):
    """Converts DOCX documents to Markdown preserving headings, tables, and lists."""

    def __init__(self) -> None:
        self._engine = MarkItDown()

    def convert(self, file_path: Path) -> str:
        result = self._engine.convert(str(file_path))
        content = result.text_content.strip()
        if not content:
            raise ValueError("DOCX document contains no extractable content.")
        return content
