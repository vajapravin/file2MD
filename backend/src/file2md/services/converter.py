"""Converter orchestrator implementing the Strategy pattern with timeout controls."""

import asyncio
from pathlib import Path

import structlog
from fastapi import HTTPException, status

from file2md.config import get_settings
from file2md.converters import CONVERTERS
from file2md.services.job_manager import _convert_chunk_task, get_process_executor

logger = structlog.get_logger()


class ConversionOrchestrator:
    """Manages converter strategies and executes conversions within sandboxes."""

    def __init__(self) -> None:
        self._converters = CONVERTERS

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

        loop = asyncio.get_running_loop()
        try:
            # Run CPU/parser synchronous work in process pool with strict timeout
            markdown = await asyncio.wait_for(
                loop.run_in_executor(
                    get_process_executor(),
                    _convert_chunk_task,
                    str(file_path),
                    ext,
                    original_filename,
                ),
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
