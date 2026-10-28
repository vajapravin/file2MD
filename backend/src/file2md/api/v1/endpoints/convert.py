"""Conversion endpoints for single, batch, and parallel chunking file uploads."""

import asyncio
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

import structlog
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse

from file2md.api.v1.schemas import (
    AsyncJobResponse,
    BatchConvertItem,
    BatchConvertResponse,
    ConvertMetadata,
    ConvertResponse,
)
from file2md.services.converter import orchestrator
from file2md.services.file_cleanup import isolated_temp_directory
from file2md.services.job_manager import job_manager
from file2md.services.splitter import should_split_document
from file2md.services.validators import (
    sanitize_filename,
    validate_file_metadata,
    validate_file_signature,
)

logger = structlog.get_logger()
router = APIRouter(tags=["Conversion"])

_background_tasks: set[asyncio.Task[None]] = set()


async def _run_parallel_job_with_cleanup(
    job_id: str,
    file_path: Path,
    ext: str,
    safe_name: str,
    temp_dir: Path,
    start_time: float,
) -> None:
    """Execute parallel job in background and clean up temp directory."""
    try:
        await job_manager.execute_parallel_job(
            job_id, file_path, ext, safe_name, temp_dir, start_time
        )
    finally:
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception as exc:
            logger.warning(
                "async_temp_cleanup_failed",
                temp_dir=str(temp_dir),
                error=str(exc),
            )


@router.post(
    "/convert",
    summary="Convert a single file to Markdown (Sync or Parallel Async)",
    description=(
        "Converts a document to Markdown. Large files or multi-page documents "
        "are automatically split and processed in parallel across worker "
        "processes, returning an HTTP 202 Accepted job with status polling."
    ),
    responses={
        200: {
            "model": ConvertResponse,
            "description": "Instant synchronous conversion result",
        },
        202: {
            "model": AsyncJobResponse,
            "description": "Asynchronous parallel chunking job created",
        },
    },
)
async def convert_file(
    file: UploadFile = File(...),
    mode: str | None = Query(
        default="auto",
        description=(
            "Conversion execution mode: 'auto' (split if large), "
            "'sync' (force single-pass), 'async'"
        ),
    ),
) -> Any:
    start_time = time.perf_counter()

    raw_filename = file.filename or "uploaded_file"
    safe_name = sanitize_filename(raw_filename)

    # Read content
    content = await file.read()
    size_bytes = len(content)

    # Validation
    ext = validate_file_metadata(safe_name, file.content_type, size_bytes)
    validate_file_signature(ext, content[:16])

    # Create isolated temp folder
    base_dir = Path("/tmp/file2md")  # noqa: S108 - dedicated temporary directory
    base_dir.mkdir(parents=True, exist_ok=True)
    session_id = uuid.uuid4().hex
    temp_dir = base_dir / session_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_file = temp_dir / safe_name
    temp_file.write_bytes(content)

    try:
        # Check whether to trigger parallel splitting
        is_parallel = (mode == "async") or (
            mode != "sync"
            and await asyncio.to_thread(
                should_split_document, temp_file, ext, size_bytes
            )
        )

        if is_parallel:
            job_id = uuid.uuid4().hex
            job_data = await job_manager.create_job(job_id, safe_name, ext, size_bytes)

            # Dispatch background parallel conversion pipeline
            task = asyncio.create_task(
                _run_parallel_job_with_cleanup(
                    job_id, temp_file, ext, safe_name, temp_dir, start_time
                )
            )
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)

            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content=job_data,
            )
    except Exception:
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception as exc:
            logger.warning(
                "temp_cleanup_failed",
                temp_dir=str(temp_dir),
                error=str(exc),
            )
        raise

    # Fast-path synchronous conversion
    try:
        markdown = await orchestrator.convert(temp_file, ext, safe_name)
    finally:
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception as exc:
            logger.warning(
                "sync_temp_cleanup_failed",
                temp_dir=str(temp_dir),
                error=str(exc),
            )

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    return ConvertResponse(
        filename=safe_name,
        original_format=ext.lstrip("."),
        markdown=markdown,
        metadata=ConvertMetadata(
            size_bytes=size_bytes,
            conversion_time_ms=elapsed_ms,
        ),
    )


@router.get(
    "/jobs/{job_id}",
    response_model=AsyncJobResponse,
    summary="Get status and progress of an asynchronous/split conversion job",
    description=(
        "Polls real-time progress of parallel chunk conversion and retrieves "
        "final Markdown upon completion."
    ),
)
async def get_job_status(job_id: str) -> AsyncJobResponse:
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversion job '{job_id}' not found or expired.",
        )
    return AsyncJobResponse(**job)


@router.post(
    "/convert/batch",
    response_model=BatchConvertResponse,
    summary="Batch convert multiple files to Markdown",
    description="Converts multiple files and returns individual conversion results.",
)
async def convert_batch(files: list[UploadFile] = File(...)) -> BatchConvertResponse:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were provided for batch conversion.",
        )

    results: list[BatchConvertItem] = []

    for file in files:
        start_time = time.perf_counter()
        raw_filename = file.filename or "uploaded_file"
        safe_name = sanitize_filename(raw_filename)

        try:
            content = await file.read()
            size_bytes = len(content)

            ext = validate_file_metadata(safe_name, file.content_type, size_bytes)
            validate_file_signature(ext, content[:16])

            async with isolated_temp_directory() as temp_dir:
                temp_file = temp_dir / safe_name
                temp_file.write_bytes(content)
                markdown = await orchestrator.convert(temp_file, ext, safe_name)

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            results.append(
                BatchConvertItem(
                    filename=safe_name,
                    status="success",
                    markdown=markdown,
                    metadata=ConvertMetadata(
                        size_bytes=size_bytes,
                        conversion_time_ms=elapsed_ms,
                    ),
                )
            )
        except HTTPException as exc:
            results.append(
                BatchConvertItem(
                    filename=safe_name,
                    status="error",
                    error=str(exc.detail),
                )
            )
        except Exception as exc:
            logger.error("batch_item_failed", filename=safe_name, error=str(exc))
            results.append(
                BatchConvertItem(
                    filename=safe_name,
                    status="error",
                    error=(
                        "Conversion failed due to an unexpected document "
                        "parsing error."
                    ),
                )
            )

    return BatchConvertResponse(results=results)
