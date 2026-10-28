"""Global error handling and exception formatting middleware."""

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = structlog.get_logger()


def register_error_handlers(app: FastAPI) -> None:
    """Register custom exception handlers with the FastAPI application."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        logger.warning(
            "http_exception",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
        )
        error_code = "http_error"
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            error_code = "bad_request"
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            error_code = "not_found"
        elif exc.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
            error_code = "file_too_large"
        elif exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            error_code = "conversion_failed"

        return JSONResponse(
            status_code=exc.status_code,
            content={"error": error_code, "detail": str(exc.detail)},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        first_msg = errors[0].get("msg") if errors else "Validation failed"
        logger.warning("validation_error", errors=errors, path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "validation_error", "detail": first_msg},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            exc_info=True,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "detail": "An unexpected server error occurred during processing.",
            },
        )
