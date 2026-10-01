"""HTML to Markdown converter using MarkItDown."""

from pathlib import Path
from markitdown import MarkItDown
from file2md.converters.base import BaseConverter


class HtmlConverter(BaseConverter):
    """Converts HTML files to Markdown preserving links, headers, and formatting."""

    def __init__(self) -> None:
        self._engine = MarkItDown()

    def convert(self, file_path: Path) -> str:
        result = self._engine.convert(str(file_path))
        content = result.text_content.strip()
        if not content:
            raise ValueError("HTML document contains no extractable content.")
        return content
