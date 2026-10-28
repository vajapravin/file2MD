# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

file2MD: a self-hosted web app that converts uploaded files (PDF, DOCX, TXT, HTML, CSV, JSON, MD) to Markdown using Microsoft's `markitdown`. FastAPI backend (`backend/`), React 19 + TypeScript + Tailwind v4 + Vite frontend (`frontend/`), Redis for async job state, all wired up by `docker-compose.yml`.

## Commands

Full stack (backend on :8086, frontend on :5173, Redis on host :6389):
```bash
docker compose up --build -d
```

Backend (run from `backend/`, Python 3.12+). These are the same steps CI runs:
```bash
pip install -e ".[dev]"
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/                      # strict mode
pytest                         # all tests
pytest tests/unit/test_validators.py::test_name   # one test
uvicorn file2md.main:app --reload --port 8086
```

Frontend (run from `frontend/`, Node 20). CI runs lint, format:check, typecheck, test, build:
```bash
npm install
npm run dev
npm test                       # vitest run
npx vitest run path/to/file.test.tsx   # one file (frontend/tests/ is currently empty)
npx vitest run -t "test name"  # tests matching a name
npm run lint && npm run format:check && npm run typecheck && npm run build
```

## Architecture

### Request flow (`backend/src/file2md/api/v1/endpoints/convert.py`)
1. The upload is read into memory and the filename is sanitized. It then goes through triple validation in `services/validators.py`: extension whitelist, declared MIME type, and magic-byte signature (`MAGIC_SIGNATURES`).
2. The file is written to `/tmp/file2md/<uuid>/`. Temp dirs are always deleted afterwards: in a `finally` on the sync path, and by `_run_parallel_job_with_cleanup` on the async path. `/convert/batch` uses the `isolated_temp_directory()` context manager instead.
3. **Sync path** (small files, or `?mode=sync`): `ConversionOrchestrator.convert` (`services/converter.py`) runs the converter in `asyncio.to_thread` under `CONVERSION_TIMEOUT_SECONDS`. It maps failures to HTTP 4xx and returns 200 with a `ConvertResponse`.
4. **Async/parallel path** (`?mode=async`, or when `should_split_document` fires on size ≥ `CHUNK_SPLIT_THRESHOLD_BYTES` (5 MB) or a PDF with more than `PDF_CHUNK_PAGE_SIZE` pages): returns **202** with a job payload. A background task in `services/job_manager.py` then works through these steps:
   - split (`services/splitter.py`: PDF by pages via pypdf, CSV by rows with the header repeated, TXT by lines)
   - convert chunks in a shared `ProcessPoolExecutor`
   - merge (`services/merger.py`; CSV tables are stitched so the header is not duplicated)
   - store status, progress and the final markdown in Redis (key TTL `JOB_TTL_SECONDS`)

   If splitting fails, it falls back to a single-pass conversion. Clients poll `GET /api/v1/jobs/{job_id}`.

### Converters (Strategy pattern)
`converters/base.py` defines `BaseConverter.convert(path) -> str`. There is one class per format, and most wrap `markitdown` plus format-specific cleanup. **The extension→converter map is duplicated** in `ConversionOrchestrator.__init__` and in `_convert_chunk_task` in `job_manager.py`. The second copy exists because worker processes import converters locally. When you add a format, update both maps, plus the validator whitelist and MIME/signature tables, `list_formats` in `endpoints/health.py`, and the frontend `ALLOWED_EXTENSIONS` in `frontend/src/utils/fileValidation.ts`. Checklist: `docs/adding-a-format.md`.

Worker processes raise the recursion limit (`sys.setrecursionlimit(10000)`) because deeply nested PDF/HTML parsing exceeded the default limit.

### Config
`config.py` has a pydantic-settings `Settings` class, accessed through the cached `get_settings()`. It reads env and `backend/.env`. Chunking knobs live there: `PDF_CHUNK_PAGE_SIZE`, `CSV_CHUNK_ROW_SIZE`, `TXT_CHUNK_LINE_SIZE`, `CHUNK_PARALLEL_WORKERS`.

### Frontend
`App.tsx` holds state; components live in `src/components/`. All backend calls go through `src/services/convertApi.ts`. `convertSingleFile` handles a 202 response by polling `fetchJobStatus` every 800 ms and reporting progress. The API base is `VITE_API_BASE_URL`. When it is empty (as in Docker), requests go to relative `/api`, which the Vite dev server proxies to `BACKEND_URL` (default `http://backend:8086`). The frontend types in `src/types/` mirror the backend `api/v1/schemas.py`, so keep the two in sync. The `@` alias points to `src/`.

## Conventions
- Ruff enforces bandit (`S`) and bans `print` (`T20`). Log with `structlog` as `logger.info("snake_case_event", key=value)`.
- Mypy runs in strict mode on `src/`. `markitdown`, `pypdf` and `redis` are configured as untyped.
- pytest uses `asyncio_mode = "auto"`, so async tests need no decorator.
- Privacy is a product promise: never persist uploaded files or converted output beyond the temp dir and the Redis job TTL.
