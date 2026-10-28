"""Converter orchestrator implementing the Strategy pattern with timeout controls."""

import asyncio
from pathlib import Path

import structlog
from fastapi import HTTPException, status

from file2md.config import get_settings
from file2md.converters.base import BaseConverter
from file2md.converters.csv_converter import CsvConverter
from file2md.converters.docx import DocxConverter
from file2md.converters.html import HtmlConverter
from file2md.converters.json_converter import JsonConverter
from file2md.converters.markdown import MarkdownNormalizer
from file2md.converters.pdf import PdfConverter
from file2md.converters.txt import TxtConverter

logger = structlog.get_logger()


class ConversionOrchestrator:
    """Manages converter strategies and executes conversions within sandboxes."""

    def __init__(self) -> None:
        self._converters: dict[str, BaseConverter] = {
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

    async def convert(
        self, file_path: Path, extension: str, original_filename: str
    ) -> str:
        """Execute conversion with timeout and error classification."""
        settings = get_settings()
        ext = extension.lower()

        converter = self._converters.get(ext)
        if not converter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No converter strategy found for format '{ext}'",
            )

        logger.info(
            "conversion_started",
            extension=ext,
            filename=original_filename,
        )

        try:
            # Run CPU/parser synchronous work in thread pool with strict timeout
            markdown = await asyncio.wait_for(
                asyncio.to_thread(converter.convert, file_path),
                timeout=float(settings.CONVERSION_TIMEOUT_SECONDS),
            )

            if not markdown or not markdown.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Conversion produced empty Markdown for "
                        f"'{original_filename}'."
                    ),
                )

            logger.info(
                "conversion_completed",
                extension=ext,
                chars_generated=len(markdown),
            )
            return markdown

        except TimeoutError as exc:
            logger.error(
                "conversion_timeout",
                filename=original_filename,
                extension=ext,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Conversion timed out after "
                    f"{settings.CONVERSION_TIMEOUT_SECONDS} seconds."
                ),
            ) from exc

        except HTTPException:
            raise

        except ValueError as exc:
            logger.warning(
                "conversion_value_error",
                error=str(exc),
                filename=original_filename,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        except Exception as exc:
            logger.error(
                "conversion_error",
                error=str(exc),
                filename=original_filename,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Failed to convert '{original_filename}'. The file may "
                    f"be corrupt, password-protected, or in an unsupported "
                    f"sub-format."
                ),
            ) from exc


orchestrator = ConversionOrchestrator()
