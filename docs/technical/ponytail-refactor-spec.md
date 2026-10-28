# Ponytail Refactor Spec

**Status:** Proposed · **Date:** 2026-10-28 · **Source:** ponytail audit of `main` @ `127fa2c` (full audit in the [Appendix](#appendix-audit-report))

## 1. Goal

Make file2MD keep its privacy promise, survive bad uploads under public-demo load, and get CI green again. Along the way, cut about 200 lines of duplicated or dead code.

Order of priority: correct → safe → holds under load → tested → fast → lean.

## 2. Baseline (measured at audit time)

| Check | Result |
|---|---|
| Backend `ruff check src tests` | 155 errors (68 auto-fixable) |
| Backend `ruff format --check` | 12 files would be reformatted |
| Backend `mypy src` (strict) | 3 errors (`job_manager.py:98`, `job_manager.py:133`, `main.py:53`) |
| Backend `pytest` (no Redis) | 20 passed, 3 failed (all in `tests/api/test_job_endpoints.py`, `ConnectionError` to `redis:6379`) |
| Frontend CI | Fails: no `package-lock.json`, no `eslint.config.js`, no test files |
| GitHub Actions | Every run since 2026-10-14 is red |

Assumed load: one backend container serving the public demo. Dozens of anonymous users at once, uploads up to 60 MB.

## 3. Non-goals

- No new features, formats, endpoints or config options.
- No new dependencies. Everything below uses the stdlib or packages that are already installed.
- No change to the public API shape (`/convert`, `/convert/batch`, `/jobs/{id}`, `/health`, `/formats`).
- No UI redesign.

## 4. Work plan

Each phase is one PR. Phases 1 and 2 come first; phases 3–6 can be done in any order after that. Item numbers (#N) refer to the audit findings.

### Phase 1: Privacy (#2, #3)

**1a. Clean up the temp dir if job creation fails** (#2)
- File: `backend/src/file2md/api/v1/endpoints/convert.py` (`convert_file`, async branch).
- Change: if anything between `temp_file.write_bytes(...)` and the start of the background task raises (`create_job`, `should_split_document`), `shutil.rmtree(temp_dir)` and re-raise.
- Acceptance: with `job_manager.create_job` monkeypatched to raise, `POST /convert?mode=async` returns 5xx and `/tmp/file2md/` has no new directory.

**1b. Keep a strong reference to background tasks** (#3)
- File: `convert.py`.
- Change:
  ```python
  _background_tasks: set[asyncio.Task[None]] = set()
  ...
  task = asyncio.create_task(_run_parallel_job_with_cleanup(...))
  _background_tasks.add(task)
  task.add_done_callback(_background_tasks.discard)
  ```
- Acceptance: ruff `RUF006` is gone.

### Phase 2: CI green (#1)

- Backend:
  - Run `ruff check --fix src tests` and `ruff format src tests`.
  - Fix the remaining errors by hand: E501, E402, F841, B008, S108.
    - B008 (`File(...)`/`Query(...)` defaults): add per-file ignores for `api/**`. That is the FastAPI idiom.
    - S108 (`/tmp/file2md`): add `# noqa: S108` with a reason. Or move the base dir into `Settings`, but only if it's needed anyway.
  - Fix the 3 mypy errors:
    - `get_redis` return: narrow with `assert self._redis is not None`.
    - `get_job`: `return cast(dict[str, Any], json.loads(raw))`.
    - CORS: type `CORS_ALLOWED_ORIGINS` as `list[str]`. The validator already guarantees it.
  - `backend-ci.yml`: add a `services: redis: image: redis:7-alpine` with port 6379, and set `REDIS_URL=redis://localhost:6379/0` for the test step.
- Frontend:
  - Run `npm install` and commit `frontend/package-lock.json`.
  - Add a minimal flat `frontend/eslint.config.js` that uses the plugins already in `devDependencies`: `@eslint/js`, `typescript-eslint`, `react-hooks`, `react-refresh`.
  - Change the `test` script to `vitest run --passWithNoTests` until phase 5 adds tests.
- Acceptance: both workflows pass on the PR.

### Phase 3: Reliability under load (#4, #5, #6, #7)

**3a. Timeout on the parallel path** (#4)
- File: `backend/src/file2md/services/job_manager.py` (`execute_parallel_job`).
- Change: wrap the chunk wait in `asyncio.wait_for(..., timeout=settings.CONVERSION_TIMEOUT_SECONDS)`. On timeout, mark the job `failed`, do not try the single-pass fallback, and replace the pool (`_executor = None` after `shutdown(wait=False, cancel_futures=True)`).
- Known limit: `ProcessPoolExecutor` cannot kill a running worker. Mark it in the code: `# shortcut: hung worker process is orphaned until it exits, upgrade to per-task processes if this shows up in logs`.
- Acceptance: a test with `_convert_chunk_task` patched to `time.sleep` beyond a short timeout ends with job status `failed`.

**3b. Split CSV by rows, not lines** (#5)
- File: `backend/src/file2md/services/splitter.py` (`split_csv`, and the CSV row check in `should_split_document`).
- Change: read with `csv.reader(f)` and write each chunk with `csv.writer`, repeating the header row. Count rows with the reader in the threshold check too. Open files with `newline=""` as the `csv` docs require.
- Acceptance: see the phase 5 test with a quoted cell that contains a newline at the chunk boundary.

**3c. Run sync conversions in the process pool** (#6)
- File: `backend/src/file2md/services/converter.py` (`ConversionOrchestrator.convert`).
- Change: replace `asyncio.to_thread(converter.convert, file_path)` with `loop.run_in_executor(get_process_executor(), _convert_chunk_task, str(file_path), ext, original_filename)`. Keep the existing `wait_for` timeout and the error mapping unchanged.
- Note: this makes the converter map shared (see 4b) a hard requirement.
- Acceptance: existing `/convert` tests pass. A timed-out conversion no longer holds a web-process thread.

**3d. Don't parse PDFs on the event loop** (#7)
- File: `convert.py`.
- Change: `await asyncio.to_thread(should_split_document, temp_file, ext, size_bytes)`.
- Acceptance: `GET /health` keeps answering while a large PDF upload is being checked.

### Phase 4: Lean (#8, #9, #10, #11, #13)

**4a. Remove the fake MIME check** (#8)
- `validators.py`: turn `SUPPORTED_EXTENSIONS` into a `set[str]`, drop the unused `content_type` parameter, and update its 2 callers in `convert.py` and the tests.
- `README.md`: replace "triple-layer validation" with what is actually checked (extension whitelist + magic bytes for PDF/DOCX). Replace "no caching layer" with "results are held in Redis for `JOB_TTL_SECONDS` (default 1 h), then expire".

**4b. One converter map** (#9)
- `converters/__init__.py`: define `CONVERTERS: dict[str, BaseConverter]` once.
- `converter.py` and `job_manager._convert_chunk_task` both import it. Delete the two inline dicts.

**4c. One MarkItDown converter class** (#10)
- Replace `pdf.py`, `html.py`, `csv_converter.py`, `docx.py` and `txt.py` with `converters/markitdown_converter.py`: `MarkItDownConverter(empty_message: str)`. Keep the current error text for each format in `CONVERTERS`.
- Keep `JsonConverter` and `MarkdownNormalizer`.
- Delete the per-call `sys.setrecursionlimit` lines in the converters, the splitter and `_convert_chunk_task`. Keep the ones in `main.py` and `_worker_init`.

**4d. Stop splitting TXT/MD** (#11)
- `splitter.py`: drop `.txt` and `.md` from `should_split_document` and delete `split_text`. Remove the `TXT_CHUNK_LINE_SIZE` setting.
- `merger.py`: collapse the identical PDF/default branches into one.
- Update or remove the related tests in `tests/unit/test_splitter_and_merger.py`.

**4e. Delete dead code** (#13)
- `frontend/src/services/convertApi.ts`: delete `convertBatchFiles` and `fetchSupportedFormats`. Grep again before deleting. The backend endpoints stay.
- `services/file_cleanup.py`: remove the unused `os` import and the `settings` variable.
- `config.py`: delete `APP_NAME`, `APP_DEBUG`, `HOST` and `PORT` if they are still unread. Remove them from `.env.example` and `docker-compose.yml` too.
- `convert.py`: use `isolated_temp_directory()` on the sync path instead of the hand-written copy.

Acceptance for phase 4: all tests pass and the net diff is about −200 lines.

### Phase 5: Tests for the risky paths (#12)

Add these tests to `backend/tests/`:
1. **Temp-dir cleanup when job creation fails:** covered by 1a.
2. **CSV split with a quoted newline:** a CSV whose quoted cell contains `\n` sits on the chunk boundary (`rows_per_chunk=2`). After split and merge, the row count equals the input row count and the cell text is intact.
3. **Parallel timeout:** covered by 3a.

Frontend: one vitest test for `convertSingleFile` covering the 202 → poll → completed path, with `fetch` mocked. Then remove `--passWithNoTests`.

### Phase 6: Polish (#14, #15)

- `convertApi.ts` `convertSingleFile` and `convertBatchFiles`: `const data = await res.json().catch(() => ({}));`
- `job_manager.py` failure branch: replace `str(exc)` with the generic sync-path message: "Failed to convert '<name>'. The file may be corrupt, password-protected, or in an unsupported sub-format." The full exception stays in the logs.

## 5. Definition of done

- Both CI workflows are green on `main`.
- No uploaded file stays under `/tmp/file2md/` after any request ends, success or failure.
- No conversion path runs without a timeout.
- README privacy and security claims match the code.

---

## Appendix: Audit report

What this repo does: file2MD is a self-hosted web app. It takes an uploaded PDF, Word, HTML, CSV, JSON, TXT or Markdown file and returns Markdown. Small files are converted during the request. Big files are split into pieces, converted in parallel by worker processes, and the client asks the server for progress until the job is done (polling). Job state lives in Redis.
**Load I assumed:** one backend container serving the public demo, so dozens of anonymous users at once, some sending files up to 60 MB.

### Must fix

1. **CI is red on both pipelines, and has been on every recent push** (`.github/workflows/*`, `backend/`, `frontend/`)
   - **What this is:** GitHub Actions runs lint, type checks and tests on every push.
   - **Problem:** The backend fails four ways. Ruff reports 155 errors and 12 unformatted files, mypy reports 3 errors, and 3 job tests need a live Redis that CI doesn't have. The frontend fails because `package-lock.json` and `eslint.config.js` are missing and `frontend/tests/` has no tests, so `vitest run` exits with an error. So right now CI tells you nothing.
   - **Fix:** Run `ruff check --fix` and `ruff format`, then fix the 3 mypy lines and whatever ruff errors remain by hand. Add a `services: redis` block to `backend-ci.yml`. Commit the lockfile, add a basic eslint config, and use `vitest run --passWithNoTests` until real tests exist.
   - **If we skip it:** Every finding below can come back unnoticed.

2. **Uploaded file stays on disk when Redis is down** (`backend/src/file2md/api/v1/endpoints/convert.py:L87-110`)
   - **What this is:** The upload is written to `/tmp/file2md/<id>/` before the server decides how to convert it.
   - **Problem:** On the big-file path, `create_job` runs after the file is written and nothing cleans up if it fails. If Redis is unreachable (I hit this in the tests), the request returns 500 and the user's document stays in `/tmp` forever. That breaks the "zero retention" promise.
   - **Fix:** Wrap everything after `temp_file.write_bytes` in try/except. On any error before the background task starts, `shutil.rmtree(temp_dir)` and re-raise.
   - **If we skip it:** Private documents pile up on the server every time Redis has a blip.

3. **The background job can disappear in the middle of a run** (`convert.py:L107`)
   - **What this is:** `asyncio.create_task(...)` starts the big-file conversion and keeps no reference to it.
   - **Problem:** asyncio only holds a weak reference to tasks, so Python's garbage collector can destroy a running task. Ruff flags this as RUF006. When that happens, the job stays "pending" forever and its `finally` cleanup never runs, so the file is left behind too.
   - **Fix:** Keep the tasks in a module-level set: `_tasks.add(t); t.add_done_callback(_tasks.discard)`. Two lines.
   - **If we skip it:** Big uploads sometimes hang with no error, and their files stay on disk.

4. **The parallel path has no timeout** (`backend/src/file2md/services/job_manager.py:L190-225`)
   - **What this is:** Chunks are converted in a pool of 4 worker processes.
   - **Problem:** The sync path has a 120 s limit, but the chunk tasks are awaited with no limit. A chunk that hangs on a malformed PDF page keeps the job "processing" forever and keeps that worker busy forever. After four such files, every big-file job on the server stops moving.
   - **Fix:** Wrap the wait in `asyncio.wait_for(..., CONVERSION_TIMEOUT_SECONDS)` so the job is marked failed. That frees the user, but not the stuck worker: to kill it, recreate the pool after a timeout.
   - **If we skip it:** One bad public upload can quietly break big-file conversion until someone restarts the server.

5. **CSV splitting breaks quoted cells that contain line breaks** (`backend/src/file2md/services/splitter.py:L154-215`, also the row count at `L50-56`)
   - **What this is:** Big CSVs are split every 1000 rows, and each piece repeats the header.
   - **Problem:** The splitter counts text lines, not CSV rows. A cell like `"line one⏎line two"` that sits on a 1000-line boundary is cut in half, so both pieces have broken quoting and the merged table has shifted or garbled rows. The row-count check is wrong for the same reason.
   - **Fix:** Read rows with `csv.reader` and write each piece with `csv.writer`, both from the standard library. About the same amount of code.
   - **If we skip it:** Real exports (addresses, notes fields) come out silently corrupted.

### Should fix

6. **Timed-out conversions keep running in the background** (`backend/src/file2md/services/converter.py:L57-60`)
   - **What this is:** A sync conversion runs in a thread with `asyncio.wait_for`.
   - **Problem:** On timeout the user gets a 422, but a Python thread can't be stopped, so the conversion keeps running after its temp file has been deleted. The default thread pool has about 8–14 threads on typical hardware, and a few slow uploads fill it, so every later conversion waits in line.
   - **Fix:** Send sync conversions to the same process pool as chunks (`loop.run_in_executor(get_process_executor(), _convert_chunk_task, ...)`). This also takes CPU-heavy parsing out of the web process.
   - **If we skip it:** A handful of heavy PDFs makes the whole site slow.

7. **The PDF page count blocks the whole server** (`splitter.py:L36-46`, called from `convert.py:L97`)
   - **What this is:** Before choosing sync or async, the endpoint opens the PDF with pypdf to count its pages.
   - **Problem:** That parse runs directly inside the async request handler. For a 60 MB PDF this stalls every other request, including health checks and job polling, for as long as the parse takes.
   - **Fix:** `await asyncio.to_thread(should_split_document, temp_file, ext, size_bytes)`. One line.
   - **If we skip it:** One big upload freezes the site for everyone.

8. **The MIME check is advertised but never done** (`backend/src/file2md/services/validators.py:L10-24, L55-89`)
   - **What this is:** The MIME type is the file type the browser declares in the upload.
   - **Problem:** `validate_file_metadata` takes `content_type` and never reads it. The MIME sets in `SUPPORTED_EXTENSIONS` are unused. The README still claims "triple-layer validation" and "no caching layer", but Redis stores converted Markdown for an hour.
   - **Fix:** Delete the MIME sets and the unused parameter, since the browser can send any type it likes anyway. The magic-byte check (looking at the file's first bytes) is the real guard. Then correct those two README claims.
   - **If we skip it:** The privacy and security docs promise things the code doesn't do.

9. **The extension → converter map is written twice** (`converter.py:L25-35`, `job_manager.py:L44-62`)
   - **What this is:** Both the web process and the worker processes need to know which converter handles which extension.
   - **Problem:** The two copies must change together. If you add a format to only one, the worker fails with "No converter found" and the job quietly falls back to a slow single-pass conversion.
   - **Fix:** Define the dict once, as `CONVERTERS` in `converters/__init__.py`, and import it in both places.
   - **If we skip it:** The next new format half-works.

10. **Five converter classes are the same code** (`converters/pdf.py`, `html.py`, `csv_converter.py`, `docx.py`, `txt.py`)
    - **What this is:** Each class calls `MarkItDown().convert()`, strips the result, and raises if it's empty.
    - **Problem:** The only difference between them is the error text. The `setrecursionlimit` call is also repeated in 6 places, when `main.py` and the worker's `_worker_init` already cover it.
    - **Fix:** One `MarkItDownConverter(empty_message)` class. Keep `JsonConverter` and `MarkdownNormalizer`, which do real work. About 80 lines fewer.
    - **If we skip it:** Five files to edit for every behavior change.

11. **Splitting TXT/MD files adds stray blank lines and gains nothing** (`splitter.py:L219-266`, `services/merger.py`)
    - **What this is:** Text files over 5 MB are cut every 2000 lines and joined back with `"\n\n"`.
    - **Problem:** A paragraph or code block that crosses line 2000 gets a blank line inserted in the middle. Plain text converts very quickly anyway, so starting worker processes is slower than converting it in one pass.
    - **Fix:** Remove `.txt` and `.md` from `should_split_document` and delete `split_text`. About 50 lines fewer, and the bug goes with them.
    - **If we skip it:** Large text and Markdown files come back subtly changed.

12. **The risky paths have no tests**
    - **What this is:** There are 23 backend tests. The frontend has none.
    - **Problem:** No test covers the temp-dir cleanup when a conversion fails (findings 2 and 3), or quoted CSV cells during splitting (finding 5). Those are the privacy and data-corruption paths.
    - **Fix:** Add one test that forces `create_job` to raise and asserts the temp dir is gone. Add one `split_csv` test with a quoted line break at the chunk boundary.
    - **If we skip it:** Those regressions stay invisible.

13. **Dead code and unused settings**
    - **What this is:** Code and settings that nothing uses.
    - **Problem:** In `frontend/src/services/convertApi.ts`, `convertBatchFiles` and `fetchSupportedFormats` are never called. `services/file_cleanup.py` has an unused `os` import and an unused `settings` variable. In `config.py`, `APP_NAME`, `APP_DEBUG`, `HOST` and `PORT` are read nowhere. `convert.py:L87-96` re-writes `isolated_temp_directory` by hand.
    - **Fix:** Delete them, and use the context manager on the sync path.
    - **If we skip it:** Readers keep wondering what these do.

### Nice to have

14. **Error responses that aren't JSON show a confusing message** (`frontend/src/services/convertApi.ts:L46`)
    - **What this is:** After uploading, the frontend reads the response as JSON.
    - **Problem:** If a proxy in front of the backend returns an HTML error page (413 too large, 502 bad gateway), the user sees "Unexpected token <" instead of a real error.
    - **Fix:** `res.json().catch(() => ({}))`, the same as `fetchJobStatus` already does.
    - **If we skip it:** The error messages are cryptic.

15. **Failed jobs show the raw internal error** (`job_manager.py:~L292`)
    - **What this is:** When a big-file job fails, the error text is shown to the user.
    - **Problem:** `"error": str(exc)` sends raw pypdf messages, and possibly server paths under `/tmp/file2md/...`, to anonymous users.
    - **Fix:** Use the same generic message the sync path uses.
    - **If we skip it:** Small information leak.

I left out 3 smaller findings: unused `DocumentChunk` metadata, a `get_redis` reconnect-per-event-loop oddity, and a duplicate merge branch for PDF.

**Verdict:** Fix 2 and 3 first because they break the privacy promise, then 1 so CI catches regressions again, then 4 and 5.

**Lean:** about −200 lines possible (findings 8–11 and 13), no dependencies to remove.

**Not checked:** I didn't run the frontend (no `node_modules`). I didn't read the Dockerfiles, the production or Nginx setup, `docs/`, or the UI components beyond `App.tsx`. I ran the backend tests in a temporary virtualenv without Redis: 20 passed and 3 failed, all because Redis wasn't reachable. I changed no repo code.
