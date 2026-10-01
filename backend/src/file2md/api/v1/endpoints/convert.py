"""Conversion endpoints for single and batch file uploads."""

import time
from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile, status
import structlog
from file2md.api.v1.schemas import (
    BatchConvertItem,
    BatchConvertResponse,
    ConvertMetadata,
    ConvertResponse,
)
from file2md.services.converter import orchestrator
from file2md.services.file_cleanup import isolated_temp_directory
from file2md.services.validators import (
    sanitize_filename,
    validate_file_metadata,
    validate_file_signature,
)

logger = structlog.get_logger()
router = APIRouter(tags=["Conversion"])


@router.post(
    "/convert",
    response_model=ConvertResponse,
    summary="Convert a single file to Markdown",
    description="Accepts a supported document or data file and returns converted, clean Markdown text.",
)
async def convert_file(file: UploadFile = File(...)) -> ConvertResponse:
    start_time = time.perf_counter()

    raw_filename = file.filename or "uploaded_file"
    safe_name = sanitize_filename(raw_filename)

    # Read content
    content = await file.read()
    size_bytes = len(content)

    # Validation
    ext = validate_file_metadata(safe_name, file.content_type, size_bytes)
    validate_file_signature(ext, content[:16])

    # Isolated processing
    async with isolated_temp_directory() as temp_dir:
        temp_file = temp_dir / safe_name
        temp_file.write_bytes(content)

        markdown = await orchestrator.convert(temp_file, ext, safe_name)

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


@router.post(
    "/convert/batch",
    response_model=BatchConvertResponse,
    summary="Batch convert multiple files to Markdown",
    description="Converts multiple files in parallel and returns individual conversion results.",
)
async def convert_batch(files: List[UploadFile] = File(...)) -> BatchConvertResponse:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were provided for batch conversion.",
        )

    results: List[BatchConvertItem] = []

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
                    error="Conversion failed due to an unexpected document parsing error.",
                )
            )

    return BatchConvertResponse(results=results)
