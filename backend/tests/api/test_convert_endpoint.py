"""API tests for the file conversion endpoint."""

import io

import pytest
from httpx import ASGITransport, AsyncClient

from file2md.main import app


@pytest.mark.asyncio
async def test_convert_markdown_success() -> None:
    content = b"# Title\n\nSome text content."
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/convert",
            files={"file": ("test.md", io.BytesIO(content), "text/markdown")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.md"
    assert data["original_format"] == "md"
    assert "# Title" in data["markdown"]
    assert "metadata" in data
    assert data["metadata"]["size_bytes"] == len(content)


@pytest.mark.asyncio
async def test_convert_html_success() -> None:
    html = b"<h1>Heading</h1><p>Test paragraph with <a href='https://example.com'>link</a></p>"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/convert",
            files={"file": ("page.html", io.BytesIO(html), "text/html")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "# Heading" in data["markdown"]
    assert "[link](https://example.com)" in data["markdown"]


@pytest.mark.asyncio
async def test_convert_csv_success() -> None:
    csv = b"Col1,Col2\nVal1,Val2\nVal3,Val4"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/convert",
            files={"file": ("data.csv", io.BytesIO(csv), "text/csv")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "| Col1 | Col2 |" in data["markdown"]


@pytest.mark.asyncio
async def test_convert_json_success() -> None:
    json_bytes = b'{"name": "file2MD", "version": 1}'
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/convert",
            files={"file": ("data.json", io.BytesIO(json_bytes), "application/json")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "```json" in data["markdown"]
    assert '"name": "file2MD"' in data["markdown"]


@pytest.mark.asyncio
async def test_convert_rejects_empty_file() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/convert",
            files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
        )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_convert_rejects_unsupported_format() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/convert",
            files={
                "file": ("script.sh", io.BytesIO(b"echo hello"), "application/x-sh")
            },
        )

    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_convert_async_cleans_temp_dir_on_create_job_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pathlib import Path

    from file2md.services.job_manager import job_manager

    base_dir = Path("/tmp/file2md")
    initial_dirs = set(base_dir.iterdir()) if base_dir.exists() else set()

    async def mock_create_job(*args: object, **kwargs: object) -> None:
        raise RuntimeError("Redis connection error simulated")

    monkeypatch.setattr(job_manager, "create_job", mock_create_job)

    content = b"# Test Markdown"
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/convert?mode=async",
            files={"file": ("test.md", io.BytesIO(content), "text/markdown")},
        )

    assert response.status_code >= 500
    current_dirs = set(base_dir.iterdir()) if base_dir.exists() else set()
    assert current_dirs == initial_dirs


@pytest.mark.asyncio
async def test_convert_cleans_temp_dir_on_should_split_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pathlib import Path

    import file2md.api.v1.endpoints.convert as convert_module

    base_dir = Path("/tmp/file2md")
    initial_dirs = set(base_dir.iterdir()) if base_dir.exists() else set()

    def mock_should_split(*args: object, **kwargs: object) -> bool:
        raise ValueError("Corrupt file metadata")

    monkeypatch.setattr(convert_module, "should_split_document", mock_should_split)

    content = b"# Test Markdown"
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/convert?mode=auto",
            files={"file": ("test.md", io.BytesIO(content), "text/markdown")},
        )

    assert response.status_code >= 500
    current_dirs = set(base_dir.iterdir()) if base_dir.exists() else set()
    assert current_dirs == initial_dirs
