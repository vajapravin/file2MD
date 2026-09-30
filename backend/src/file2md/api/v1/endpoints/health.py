"""Health check and format discovery endpoints."""

from fastapi import APIRouter
from file2md.api.v1.schemas import FormatInfo, FormatsResponse, HealthResponse
from file2md.config import get_settings

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check service health",
    description="Returns the current operational status and version of the file2MD backend.",
)
async def check_health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
    )


@router.get(
    "/formats",
    response_model=FormatsResponse,
    summary="List supported formats",
    description="Returns list of file extensions and MIME types accepted for conversion.",
)
async def list_formats() -> FormatsResponse:
    # Formats defined per specification
    supported = [
        FormatInfo(
            extension=".pdf",
            mime_types=["application/pdf"],
            description="Portable Document Format",
        ),
        FormatInfo(
            extension=".docx",
            mime_types=[
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ],
            description="Microsoft Word Document",
        ),
        FormatInfo(
            extension=".txt",
            mime_types=["text/plain"],
            description="Plain text document",
        ),
        FormatInfo(
            extension=".html",
            mime_types=["text/html"],
            description="HyperText Markup Language",
        ),
        FormatInfo(
            extension=".csv",
            mime_types=["text/csv", "application/csv"],
            description="Comma-separated values",
        ),
        FormatInfo(
            extension=".json",
            mime_types=["application/json"],
            description="JavaScript Object Notation",
        ),
        FormatInfo(
            extension=".md",
            mime_types=["text/markdown", "text/x-markdown"],
            description="Markdown document cleanup & normalization",
        ),
    ]
    return FormatsResponse(formats=supported)
