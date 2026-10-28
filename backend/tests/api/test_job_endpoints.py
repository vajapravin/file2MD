"""Integration tests for async and parallel chunking job endpoints."""

import asyncio
import io
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from file2md.main import app


@pytest.mark.asyncio
async def test_convert_async_mode_returns_202_and_completes() -> None:
    content = (
        b"# Asynchronous Document\n\n"
        b"This is processed via parallel worker pipeline."
    )
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
        assert job_data["status"] in {
            "pending",
            "splitting",
            "processing",
            "completed",
        }

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


@pytest.mark.asyncio
async def test_parallel_job_fallback_recovers_to_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify fallback to single-pass completes if chunking fails."""
    from file2md.services import job_manager as jm_mod

    # Simulate an error during splitting (e.g. RecursionError)
    def mock_split_fail(*args: object, **kwargs: object) -> None:
        raise RecursionError("maximum recursion depth exceeded")

    monkeypatch.setattr(jm_mod, "split_document", mock_split_fail)

    content = b"# Document Needing Fallback\n\nContent converted via fallback."
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/convert?mode=async",
            files={"file": ("fallback_doc.md", io.BytesIO(content), "text/markdown")},
        )
        assert response.status_code == 202
        job_id = response.json()["job_id"]

        completed = False
        for _ in range(25):
            await asyncio.sleep(0.2)
            poll_res = await client.get(f"/api/v1/jobs/{job_id}")
            if poll_res.json()["status"] == "completed":
                completed = True
                assert "# Document Needing Fallback" in poll_res.json()["markdown"]
                assert poll_res.json()["progress"] == 100
                break

        assert completed, "Parallel job fallback did not successfully complete the job"


def _mock_sleep_task(*args: object) -> str:
    import time

    time.sleep(2)
    return "done"


@pytest.mark.asyncio
async def test_parallel_job_times_out_and_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify that chunk execution timeout marks the job as failed."""
    import time

    from file2md.config import get_settings
    from file2md.services.job_manager import JobManager, JobStatus
    from file2md.services.splitter import DocumentChunk

    store: dict[str, str] = {}

    class FakeRedis:
        async def set(self, key: str, val: str, ex: int | None = None) -> None:
            store[key] = val

        async def get(self, key: str) -> str | None:
            return store.get(key)

    mgr = JobManager()

    async def mock_get_redis() -> FakeRedis:
        return FakeRedis()

    monkeypatch.setattr(mgr, "get_redis", mock_get_redis)

    settings = get_settings()
    monkeypatch.setattr(settings, "CONVERSION_TIMEOUT_SECONDS", 1)

    chunk_file = tmp_path / "chunk.txt"
    chunk_file.write_text("dummy")
    chunk = DocumentChunk(0, 1, chunk_file, ".txt")
    monkeypatch.setattr(
        "file2md.services.job_manager.split_document", lambda *a, **kw: [chunk]
    )

    monkeypatch.setattr(
        "file2md.services.job_manager._convert_chunk_task", _mock_sleep_task
    )

    job_id = "timeout_test_job"
    await mgr.create_job(job_id, "doc.txt", ".txt", 100)

    start = time.perf_counter()
    await mgr.execute_parallel_job(
        job_id, chunk_file, ".txt", "doc.txt", tmp_path, start
    )

    job = await mgr.get_job(job_id)
    assert job is not None
    assert job["status"] == JobStatus.FAILED.value
    assert "timed out" in str(job.get("error", "")).lower()
