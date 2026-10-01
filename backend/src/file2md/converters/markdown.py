"""Markdown cleanup and normalization service."""

import re
from pathlib import Path
from file2md.converters.base import BaseConverter


class MarkdownNormalizer(BaseConverter):
    """Normalizes and cleans up existing Markdown files.

    Standardizes newlines, trims trailing whitespace on lines, and removes excessive blank lines.
    """

    def convert(self, file_path: Path) -> str:
        raw_text = file_path.read_text(encoding="utf-8", errors="replace")
        content = raw_text.strip()
        if not content:
            raise ValueError("Markdown file is empty.")

        # Normalize line breaks to \n
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")

        # Trim trailing whitespace on each line
        lines = [line.rstrip() for line in normalized.split("\n")]

        # Collapse more than two consecutive empty lines to two
        result = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
        return result.strip()
