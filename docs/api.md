# API Reference

> Full API documentation will be added in Milestone 10.
> Interactive API documentation is available at `http://localhost:8000/docs` when the backend is running.

## Base URL

All endpoints are prefixed with `/api/v1/`.

## Endpoints

### `GET /api/v1/health`

Health check endpoint.

**Response `200`:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### `POST /api/v1/convert`

Convert a single uploaded file to Markdown.

**Request:** `multipart/form-data` with a `file` field.

**Response `200`:**
```json
{
  "filename": "document.pdf",
  "original_format": "pdf",
  "markdown": "# Converted Content\n\n...",
  "metadata": {
    "size_bytes": 45231,
    "conversion_time_ms": 342
  }
}
```

### `GET /api/v1/formats`

List supported conversion formats.
