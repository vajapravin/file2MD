"""Unit tests for file validation and sanitization services."""

import pytest
from fastapi import HTTPException
from file2md.services.validators import (
    sanitize_filename,
    validate_file_metadata,
    validate_file_signature,
)


def test_sanitize_filename_removes_path_traversal() -> None:
    assert sanitize_filename("../../../etc/passwd.pdf") == "passwd.pdf"
    assert sanitize_filename("..\\..\\windows\\system32.docx") == "system32.docx"
    assert sanitize_filename("safe_file.txt") == "safe_file.txt"
    assert sanitize_filename("") == "unnamed_document"


def test_validate_file_metadata_accepts_supported_extensions() -> None:
    assert validate_file_metadata("doc.pdf", "application/pdf", 1024) == ".pdf"
    assert validate_file_metadata("file.docx", None, 2048) == ".docx"
    assert validate_file_metadata("data.csv", "text/csv", 500) == ".csv"
    assert validate_file_metadata("info.json", "application/json", 200) == ".json"
    assert validate_file_metadata("page.html", "text/html", 300) == ".html"
    assert validate_file_metadata("notes.txt", "text/plain", 100) == ".txt"
    assert validate_file_metadata("readme.md", "text/markdown", 150) == ".md"


def test_validate_file_metadata_rejects_empty_file() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_file_metadata("empty.txt", "text/plain", 0)
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail


def test_validate_file_metadata_rejects_unsupported_extension() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_file_metadata("danger.exe", "application/octet-stream", 1000)
    assert exc_info.value.status_code == 400
    assert "Unsupported file format" in exc_info.value.detail


def test_validate_file_metadata_rejects_oversized_file() -> None:
    oversized = 51 * 1024 * 1024 # 51 MB
    with pytest.raises(HTTPException) as exc_info:
        validate_file_metadata("huge.pdf", "application/pdf", oversized)
    assert exc_info.value.status_code == 413
    assert "exceeds maximum allowed limit" in exc_info.value.detail


def test_validate_file_signature_matches_expected() -> None:
    # PDF magic bytes
    validate_file_signature(".pdf", b"%PDF-1.7\n...")
    # DOCX magic bytes (Zip)
    validate_file_signature(".docx", b"PK\x03\x04\x14\x00...")

    # Mismatch raises
    with pytest.raises(HTTPException) as exc_info:
        validate_file_signature(".pdf", b"NOT_A_PDF")
    assert exc_info.value.status_code == 400
    assert "file signature" in exc_info.value.detail
