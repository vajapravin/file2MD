"""Tests for health check and format discovery endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from file2md.main import app


@pytest.mark.asyncio
async def test_health_check_returns_healthy() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_list_formats_returns_supported_list() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/formats")

    assert response.status_code == 200
    data = response.json()
    assert "formats" in data
    extensions = [f["extension"] for f in data["formats"]]
    assert ".pdf" in extensions
    assert ".docx" in extensions
    assert ".txt" in extensions
    assert ".html" in extensions
    assert ".csv" in extensions
    assert ".json" in extensions
    assert ".md" in extensions
