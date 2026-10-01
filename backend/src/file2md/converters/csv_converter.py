"""CSV to Markdown table converter using MarkItDown."""

from pathlib import Path
from markitdown import MarkItDown
from file2md.converters.base import BaseConverter


class CsvConverter(BaseConverter):
    """Converts CSV tabular data to clean Markdown tables."""

    def __init__(self) -> None:
        self._engine = MarkItDown()

    def convert(self, file_path: Path) -> str:
        result = self._engine.convert(str(file_path))
        content = result.text_content.strip()
        if not content:
            raise ValueError("CSV file contains no valid rows or data.")
        return content
