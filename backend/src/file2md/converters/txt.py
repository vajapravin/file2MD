"""Plain text to Markdown converter."""

from pathlib import Path
from markitdown import MarkItDown
from file2md.converters.base import BaseConverter


class TxtConverter(BaseConverter):
    """Converts plain text to Markdown with preserved paragraphing and encoding normalization."""

    def __init__(self) -> None:
        self._engine = MarkItDown()

    def convert(self, file_path: Path) -> str:
        result = self._engine.convert(str(file_path))
        content = result.text_content.strip()
        if not content:
            raise ValueError("Plain text document is empty.")
        return content
