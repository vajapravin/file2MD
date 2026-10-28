"""Safe temporary file management and cleanup utilities."""

import shutil
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import structlog

logger = structlog.get_logger()


@asynccontextmanager
async def isolated_temp_directory() -> AsyncGenerator[Path, None]:
    """Provide an isolated, unique temp directory deleted strictly upon exit."""
    base_dir = Path("/tmp/file2md")  # noqa: S108 - dedicated temporary directory
    base_dir.mkdir(parents=True, exist_ok=True)

    session_id = uuid.uuid4().hex
    temp_dir = base_dir / session_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        yield temp_dir
    finally:
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception as exc:
            logger.warning(
                "temp_cleanup_failed", temp_dir=str(temp_dir), error=str(exc)
            )
