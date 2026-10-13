"""Integration tests for async and parallel chunking job endpoints."""

import asyncio
import io
import pytest
from httpx import ASGITransport, AsyncClient
from file2md.main import app


@pytest.mark.asyncio
async def test_convert_async_mode_returns_202_and_completes() -> None:
    content = b"# Asynchronous Document\n\nThis is processed via parallel worker pipeline."
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit async job
        response = await client.post(
            "/api/v1/convert?mode=async",
            files={"file": ("async_doc.md", io.BytesIO(content), "text/markdown")},
        )

        assert response.status_code == 202
        job_data = response.json()
        assert "job_id" in job_data
        assert job_data["status"] in {"pending", "splitting", "processing", "completed"}

        job_id = job_data["job_id"]

        # Poll until completion or timeout (max 5s)
        completed = False
        for _ in range(25):
            await asyncio.sleep(0.2)
            poll_res = await client.get(f"/api/v1/jobs/{job_id}")
            assert poll_res.status_code == 200
            current_status = poll_res.json()["status"]
            if current_status == "completed":
                completed = True
                assert "# Asynchronous Document" in poll_res.json()["markdown"]
                assert poll_res.json()["progress"] == 100
                break

        assert completed, "Async parallel job did not complete within timeout"


@pytest.mark.asyncio
async def test_get_nonexistent_job_returns_404() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/jobs/nonexistent_job_id_999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
