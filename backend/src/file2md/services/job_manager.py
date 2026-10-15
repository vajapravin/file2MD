"""Redis-backed asynchronous job manager with ProcessPoolExecutor parallel worker dispatch."""

import asyncio
import json
import os
from concurrent.futures import ProcessPoolExecutor
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import structlog
from redis.asyncio import Redis
from file2md.config import get_settings
from file2md.services.merger import merge_markdown_chunks
from file2md.services.splitter import DocumentChunk, split_document

logger = structlog.get_logger()

# Shared process pool executor for CPU-bound chunk conversions
_executor: Optional[ProcessPoolExecutor] = None


def _worker_init() -> None:
    """Initialize worker process with increased recursion limit for complex parsing."""
    import sys
    sys.setrecursionlimit(10000)


def get_process_executor() -> ProcessPoolExecutor:
    """Return a shared ProcessPoolExecutor instance."""
    global _executor
    if _executor is None:
        settings = get_settings()
        workers = min(settings.CHUNK_PARALLEL_WORKERS, max(1, (os.cpu_count() or 2)))
        _executor = ProcessPoolExecutor(max_workers=workers, initializer=_worker_init)
        logger.info("process_pool_executor_initialized", max_workers=workers)
    return _executor


def _convert_chunk_task(chunk_path_str: str, ext: str, filename: str) -> str:
    """Standalone worker function executed inside an isolated OS process (bypasses GIL)."""
    import sys
    sys.setrecursionlimit(10000)

    from file2md.converters.csv_converter import CsvConverter
    from file2md.converters.docx import DocxConverter
    from file2md.converters.html import HtmlConverter
    from file2md.converters.json_converter import JsonConverter
    from file2md.converters.markdown import MarkdownNormalizer
    from file2md.converters.pdf import PdfConverter
    from file2md.converters.txt import TxtConverter

    converters = {
        ".pdf": PdfConverter(),
        ".docx": DocxConverter(),
        ".txt": TxtConverter(),
        ".html": HtmlConverter(),
        ".htm": HtmlConverter(),
        ".csv": CsvConverter(),
        ".json": JsonConverter(),
        ".md": MarkdownNormalizer(),
        ".markdown": MarkdownNormalizer(),
    }

    converter = converters.get(ext.lower())
    if not converter:
        raise ValueError(f"No converter found for format '{ext}'")

    return converter.convert(Path(chunk_path_str))


class JobStatus(str, Enum):
    PENDING = "pending"
    SPLITTING = "splitting"
    PROCESSING = "processing"
    MERGING = "merging"
    COMPLETED = "completed"
    FAILED = "failed"


class JobManager:
    """Manages Redis job state and orchestrates multi-process chunk conversions."""

    def __init__(self) -> None:
        self._redis: Optional[Redis] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def get_redis(self) -> Redis:
        """Get or initialize the async Redis connection bound to the running event loop."""
        loop = asyncio.get_running_loop()
        if self._redis is None or self._loop != loop:
            self._loop = loop
            settings = get_settings()
            self._redis = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5.0,
            )
        return self._redis

    def _job_key(self, job_id: str) -> str:
        return f"file2md:job:{job_id}"

    async def create_job(self, job_id: str, filename: str, ext: str, size_bytes: int) -> Dict[str, Any]:
        """Create a new job in Redis with pending state."""
        redis = await self.get_redis()
        settings = get_settings()

        job_data = {
            "job_id": job_id,
            "filename": filename,
            "extension": ext,
            "size_bytes": size_bytes,
            "status": JobStatus.PENDING.value,
            "progress": 0,
            "message": "Job queued for conversion",
            "chunks_total": 1,
            "chunks_completed": 0,
            "markdown": None,
            "error": None,
            "conversion_time_ms": None,
        }

        key = self._job_key(job_id)
        await redis.set(key, json.dumps(job_data), ex=settings.JOB_TTL_SECONDS)
        return job_data

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve current job state from Redis."""
        redis = await self.get_redis()
        raw = await redis.get(self._job_key(job_id))
        if not raw:
            return None
        return json.loads(raw)

    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        """Update fields of an active job in Redis."""
        redis = await self.get_redis()
        current = await self.get_job(job_id)
        if not current:
            return

        current.update(updates)
        settings = get_settings()
        await redis.set(self._job_key(job_id), json.dumps(current), ex=settings.JOB_TTL_SECONDS)

    async def execute_parallel_job(
        self,
        job_id: str,
        file_path: Path,
        ext: str,
        filename: str,
        temp_dir: Path,
        start_time_perf: float,
    ) -> None:
        """Asynchronously split, convert chunks in ProcessPoolExecutor, merge, and store result."""
        import time

        loop = asyncio.get_running_loop()
        executor = get_process_executor()

        try:
            # 1. Splitting phase
            await self.update_job(
                job_id,
                {
                    "status": JobStatus.SPLITTING.value,
                    "progress": 10,
                    "message": "Analyzing document and preparing chunks...",
                },
            )

            chunks_dir = temp_dir / "chunks"
            chunks_dir.mkdir(exist_ok=True)

            chunks = await asyncio.to_thread(split_document, file_path, ext, chunks_dir)
            total_chunks = len(chunks)

            await self.update_job(
                job_id,
                {
                    "status": JobStatus.PROCESSING.value,
                    "progress": 15,
                    "chunks_total": total_chunks,
                    "chunks_completed": 0,
                    "message": f"Processing {total_chunks} chunk(s) in parallel...",
                },
            )

            # 2. Parallel processing phase
            tasks = []
            for chunk in chunks:
                task = loop.run_in_executor(
                    executor,
                    _convert_chunk_task,
                    str(chunk.file_path),
                    ext,
                    filename,
                )
                tasks.append(task)

            # Gather with progress reporting as each finishes
            completed_count = 0
            chunk_results: List[Optional[str]] = [None] * total_chunks

            # Map tasks to their chunk indexes
            for coro in asyncio.as_completed(tasks):
                res = await coro
                completed_count += 1
                progress = int(15 + (completed_count / total_chunks) * 75)
                await self.update_job(
                    job_id,
                    {
                        "progress": progress,
                        "chunks_completed": completed_count,
                        "message": f"Converted chunk {completed_count} of {total_chunks} ({progress}%)...",
                    },
                )

            # Re-collect results in strict order
            ordered_results = await asyncio.gather(*tasks)

            # 3. Merging phase
            await self.update_job(
                job_id,
                {
                    "status": JobStatus.MERGING.value,
                    "progress": 92,
                    "message": "Stitching and normalizing final Markdown document...",
                },
            )

            merged_markdown = await asyncio.to_thread(
                merge_markdown_chunks, ordered_results, ext
            )

            elapsed_ms = int((time.perf_counter() - start_time_perf) * 1000)

            # 4. Completion
            await self.update_job(
                job_id,
                {
                    "status": JobStatus.COMPLETED.value,
                    "progress": 100,
                    "message": "Conversion completed successfully",
                    "markdown": merged_markdown,
                    "conversion_time_ms": elapsed_ms,
                },
            )
            logger.info("parallel_job_completed", job_id=job_id, chunks=total_chunks, time_ms=elapsed_ms)

        except Exception as exc:
            logger.error("parallel_job_failed", job_id=job_id, error=str(exc), exc_info=True)

            # Graceful recovery: attempt direct single-pass conversion if chunking failed
            try:
                logger.info("parallel_job_attempting_fallback", job_id=job_id)
                await self.update_job(
                    job_id,
                    {
                        "status": JobStatus.PROCESSING.value,
                        "progress": 50,
                        "message": "Parallel chunk processing encountered an issue; falling back to direct conversion...",
                    },
                )
                from file2md.services.converter import orchestrator

                single_markdown = await orchestrator.convert(file_path, ext, filename)
                elapsed_ms = int((time.perf_counter() - start_time_perf) * 1000)
                await self.update_job(
                    job_id,
                    {
                        "status": JobStatus.COMPLETED.value,
                        "progress": 100,
                        "message": "Conversion completed successfully",
                        "markdown": single_markdown,
                        "conversion_time_ms": elapsed_ms,
                    },
                )
                logger.info("parallel_job_fallback_succeeded", job_id=job_id, time_ms=elapsed_ms)
                return
            except Exception as fallback_exc:
                logger.error("parallel_job_fallback_failed", job_id=job_id, error=str(fallback_exc), exc_info=True)

            await self.update_job(
                job_id,
                {
                    "status": JobStatus.FAILED.value,
                    "error": str(exc) or "Parallel document processing failed.",
                    "message": "Conversion failed",
                },
            )


job_manager = JobManager()
