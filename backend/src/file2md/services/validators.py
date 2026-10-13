"""File validation services for file2MD."""

import re
from pathlib import Path
from typing import Dict, List, Set
from fastapi import HTTPException, status
from file2md.config import get_settings

# Whitelisted extensions and corresponding valid MIME types
SUPPORTED_EXTENSIONS: Dict[str, Set[str]] = {
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/octet-stream",
    },
    ".txt": {"text/plain", "application/octet-stream"},
    ".html": {"text/html", "text/plain", "application/xhtml+xml"},
    ".htm": {"text/html", "text/plain", "application/xhtml+xml"},
    ".csv": {"text/csv", "application/csv", "text/plain"},
    ".json": {"application/json", "text/plain"},
    ".md": {"text/markdown", "text/x-markdown", "text/plain"},
    ".markdown": {"text/markdown", "text/x-markdown", "text/plain"},
}

MAGIC_SIGNATURES: Dict[str, bytes] = {
    ".pdf": b"%PDF",
    ".docx": b"PK\x03\x04",
}


def sanitize_filename(raw_filename: str) -> str:
    """Sanitize filename to prevent directory traversal and remove dangerous characters."""
    if not raw_filename or not raw_filename.strip():
        return "unnamed_document"

    # Normalize backslashes and remove path separators
    name = Path(raw_filename.replace("\\", "/")).name

    # Remove null bytes and control characters
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)

    # Replace suspicious shell / path traversal characters
    name = re.sub(r"[^\w\s\.\-_]", "_", name)

    # Trim excessive length
    if len(name) > 200:
        stem = Path(name).stem[:190]
        ext = Path(name).suffix
        name = f"{stem}{ext}"

    return name.strip() or "unnamed_document"


def validate_file_metadata(
    filename: str, content_type: str | None, size_bytes: int
) -> str:
    """Validate file extension, size limit, and MIME type."""
    settings = get_settings()

    # 1. Size check
    if size_bytes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if size_bytes > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File size ({size_bytes / (1024 * 1024):.1f} MB) exceeds maximum "
                f"allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
            ),
        )

    # 2. Extension check
    clean_filename = sanitize_filename(filename)
    ext = Path(clean_filename).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        valid_exts = ", ".join(sorted(SUPPORTED_EXTENSIONS.keys()))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Supported formats: {valid_exts}",
        )

    return ext


def validate_file_signature(ext: str, header_bytes: bytes) -> None:
    """Validate file header bytes for formats with known magic signatures."""
    if ext in MAGIC_SIGNATURES:
        expected = MAGIC_SIGNATURES[ext]
        if not header_bytes.startswith(expected):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content does not match expected {ext.upper()} file signature.",
            )
