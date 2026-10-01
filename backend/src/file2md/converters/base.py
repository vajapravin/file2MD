"""Base interface for all document-to-markdown converters."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseConverter(ABC):
    """Abstract base class for format-specific Markdown converters."""

    @abstractmethod
    def convert(self, file_path: Path) -> str:
        """Convert the given file to Markdown text.

        Args:
            file_path: Absolute path to the local input file.

        Returns:
            The converted and normalized Markdown string.

        Raises:
            Exception: If parsing fails or output cannot be generated.
        """
        pass
