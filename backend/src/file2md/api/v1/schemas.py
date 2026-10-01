"""Pydantic request and response schemas for file2MD API v1."""

from typing import List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check endpoint response model."""

    status: str = Field(default="healthy", description="Current health status")
    version: str = Field(..., description="Service version")


class FormatInfo(BaseModel):
    """Information regarding a supported conversion format."""

    extension: str = Field(..., description="File extension with leading dot")
    mime_types: List[str] = Field(..., description="Allowed MIME types")
    description: str = Field(..., description="Human-readable description")


class FormatsResponse(BaseModel):
    """Supported formats list response."""

    formats: List[FormatInfo] = Field(..., description="List of supported file formats")


class ConvertMetadata(BaseModel):
    """Metadata regarding a completed conversion."""

    size_bytes: int = Field(..., description="Original file size in bytes")
    conversion_time_ms: int = Field(..., description="Conversion duration in milliseconds")


class ConvertResponse(BaseModel):
    """Successful conversion response."""

    filename: str = Field(..., description="Original sanitised filename")
    original_format: str = Field(..., description="Original file extension/format")
    markdown: str = Field(..., description="Converted Markdown content")
    metadata: ConvertMetadata


class BatchConvertItem(BaseModel):
    """Individual item result in a batch conversion response."""

    filename: str = Field(..., description="Filename")
    status: str = Field(..., description="Result status: 'success' or 'error'")
    markdown: str | None = Field(default=None, description="Markdown if successful")
    error: str | None = Field(default=None, description="Error message if failed")
    metadata: ConvertMetadata | None = Field(default=None, description="Metadata if successful")


class BatchConvertResponse(BaseModel):
    """Batch conversion response."""

    results: List[BatchConvertItem] = Field(..., description="Array of file conversion results")


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str = Field(..., description="Machine-readable error code")
    detail: str = Field(..., description="Actionable error description")
