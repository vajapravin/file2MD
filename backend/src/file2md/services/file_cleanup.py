"""Safe temporary file management and cleanup utilities."""

import os
import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
import structlog
from file2md.config import get_settings

logger = structlog.get_logger()


@asynccontextmanager
async def isolated_temp_directory() -> AsyncGenerator[Path, None]:
    """Provide an isolated, uniquely named directory that is strictly deleted upon exit."""
    settings = get_settings()
    base_dir = Path("/tmp/file2md")
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
            logger.warning("temp_cleanup_failed", temp_dir=str(temp_dir), error=str(exc))
