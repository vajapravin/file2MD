"""Pydantic request and response schemas for file2MD API v1."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check endpoint response model."""

    status: str = Field(default="healthy", description="Current health status")
    version: str = Field(..., description="Service version")


class FormatInfo(BaseModel):
    """Information regarding a supported conversion format."""

    extension: str = Field(..., description="File extension with leading dot")
    mime_types: list[str] = Field(..., description="Allowed MIME types")
    description: str = Field(..., description="Human-readable description")


class FormatsResponse(BaseModel):
    """Supported formats list response."""

    formats: list[FormatInfo] = Field(..., description="List of supported file formats")


class ConvertMetadata(BaseModel):
    """Metadata regarding a completed conversion."""

    size_bytes: int = Field(..., description="Original file size in bytes")
    conversion_time_ms: int = Field(
        ..., description="Conversion duration in milliseconds"
    )


class ConvertResponse(BaseModel):
    """Successful conversion response."""

    filename: str = Field(..., description="Original sanitised filename")
    original_format: str = Field(..., description="Original file extension/format")
    markdown: str = Field(..., description="Converted Markdown content")
    metadata: ConvertMetadata


class ConvertUrlRequest(BaseModel):
    """Request model for URL to Markdown conversion."""

    url: str = Field(
        ...,
        description=(
            "Target web page URL (HTTP or HTTPS) to fetch and convert to Markdown"
        ),
        examples=["https://en.wikipedia.org/wiki/Markdown"],
    )


class BatchConvertItem(BaseModel):
    """Individual item result in a batch conversion response."""

    filename: str = Field(..., description="Filename")
    status: str = Field(..., description="Result status: 'success' or 'error'")
    markdown: str | None = Field(default=None, description="Markdown if successful")
    error: str | None = Field(default=None, description="Error message if failed")
    metadata: ConvertMetadata | None = Field(
        default=None, description="Metadata if successful"
    )


class BatchConvertResponse(BaseModel):
    """Batch conversion response."""

    results: list[BatchConvertItem] = Field(
        ..., description="Array of file conversion results"
    )


class AsyncJobResponse(BaseModel):
    """Status/result for an async or split-parallel conversion job."""

    job_id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Uploaded filename")
    extension: str = Field(..., description="File extension")
    size_bytes: int = Field(..., description="File size in bytes")
    status: str = Field(
        ...,
        description=(
            "Job status: pending, splitting, processing, merging, " "completed, failed"
        ),
    )
    progress: int = Field(..., description="Overall progress percentage (0-100)")
    message: str = Field(..., description="Human-readable progress description")
    chunks_total: int = Field(default=1, description="Total number of chunks")
    chunks_completed: int = Field(default=0, description="Completed chunk count")
    markdown: str | None = Field(
        default=None, description="Final markdown when completed"
    )
    error: str | None = Field(default=None, description="Error message if failed")
    conversion_time_ms: int | None = Field(
        default=None, description="Total elapsed time in ms"
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str = Field(..., description="Machine-readable error code")
    detail: str = Field(..., description="Actionable error description")
