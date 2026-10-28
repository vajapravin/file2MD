"""Document converters module with shared format-to-converter mapping."""

from file2md.converters.base import BaseConverter
from file2md.converters.json_converter import JsonConverter
from file2md.converters.markdown import MarkdownNormalizer
from file2md.converters.markitdown_converter import MarkItDownConverter

CONVERTERS: dict[str, BaseConverter] = {
    ".pdf": MarkItDownConverter(
        "PDF document contains no extractable text or structure."
    ),
    ".docx": MarkItDownConverter("DOCX document contains no extractable content."),
    ".txt": MarkItDownConverter("Plain text document is empty."),
    ".html": MarkItDownConverter("HTML document contains no extractable content."),
    ".htm": MarkItDownConverter("HTML document contains no extractable content."),
    ".csv": MarkItDownConverter("CSV file contains no valid rows or data."),
    ".json": JsonConverter(),
    ".md": MarkdownNormalizer(),
    ".markdown": MarkdownNormalizer(),
}

__all__ = ["CONVERTERS", "BaseConverter", "MarkItDownConverter"]
