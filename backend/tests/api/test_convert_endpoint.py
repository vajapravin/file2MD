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
            files={"file": ("script.sh", io.BytesIO(b"echo hello"), "application/x-sh")},
        )

    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]
