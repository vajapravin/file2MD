"""API tests for POST /api/v1/convert/url endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from file2md.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_convert_url_endpoint_success(app) -> None:
    mock_html = (
        "<!DOCTYPE html><html><head><title>Markdown Spec</title></head>"
        "<body><h1>Markdown Guide</h1>"
        "<p>Markdown is a lightweight markup language.</p></body></html>"
    )

    transport = ASGITransport(app=app)
    with patch(
        "file2md.api.v1.endpoints.convert.fetch_url_content",
        new_callable=AsyncMock,
    ) as mock_fetch:
        mock_fetch.return_value = (mock_html, "Markdown_Spec.html")
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/convert/url",
                json={"url": "https://example.com/markdown-spec"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "Markdown_Spec.html"
        assert data["original_format"] == "url"
        assert "Markdown Guide" in data["markdown"]
        assert data["metadata"]["size_bytes"] > 0
        assert "conversion_time_ms" in data["metadata"]


@pytest.mark.asyncio
async def test_convert_url_endpoint_invalid_url(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/convert/url",
            json={"url": "ftp://not-supported.org"},
        )
        assert response.status_code == 400
        assert "Unsupported URL scheme" in response.json()["detail"]


@pytest.mark.asyncio
async def test_convert_url_endpoint_blocks_private_ip(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/convert/url",
            json={"url": "http://127.0.0.1:8080/admin"},
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "Access to private or local network addresses is prohibited" in detail
