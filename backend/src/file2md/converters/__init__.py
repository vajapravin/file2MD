"""Document converters module with shared format-to-converter mapping."""

from file2md.converters.base import BaseConverter
from file2md.converters.csv_converter import CsvConverter
from file2md.converters.docx import DocxConverter
from file2md.converters.html import HtmlConverter
from file2md.converters.json_converter import JsonConverter
from file2md.converters.markdown import MarkdownNormalizer
from file2md.converters.pdf import PdfConverter
from file2md.converters.txt import TxtConverter

CONVERTERS: dict[str, BaseConverter] = {
    ".pdf": PdfConverter(),
    ".docx": DocxConverter(),
    ".txt": TxtConverter(),
    ".html": HtmlConverter(),
    ".htm": HtmlConverter(),
    ".csv": CsvConverter(),
    ".json": JsonConverter(),
    ".md": MarkdownNormalizer(),
    ".markdown": MarkdownNormalizer(),
}

__all__ = ["CONVERTERS", "BaseConverter"]
