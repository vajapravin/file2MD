# file2MD

[![CI](https://github.com/vajapravin/file2md/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/vajapravin/file2md/actions)

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

A self-hosted, privacy-first web application that converts documents and data
files into clean, readable, structured Markdown (.md). Powered by Microsoft's
[MarkItDown](https://github.com/microsoft/markitdown) engine, file2MD preserves
essential document hierarchy — headings, tables, lists, links, and code blocks —
without exposing your sensitive files to third-party cloud services. Built with a
FastAPI backend, a modern React single-page app styled with Tailwind CSS, and
packaged with Docker Compose so it runs anywhere in minutes.

![file2MD dashboard](assets/dashboard.png)

🌐 **Live demo:** [https://file2md.vajapravin.me/](https://file2md.vajapravin.me/)

## 📸 Screens

<table>
  <tr>
    <td width="50%" align="center">
      <img src="assets/upload.png" alt="File Upload" />
      <br /><sub><b>File Upload</b> — intuitive drag-and-drop with instant type and size validation</sub>
    </td>
    <td width="50%" align="center">
      <img src="assets/dashboard.png" alt="Workspace Dashboard" />
      <br /><sub><b>Workspace Dashboard</b> — batch conversion queue with per-file status and progress</sub>
    </td>
  </tr>
</table>

## 🏗 Architecture

file2MD separates concerns across distinct layers to ensure security, maintainability, and modularity:

1. **React SPA (frontend)** — a responsive interface built with React 19,
   TypeScript, and Tailwind CSS. Features drag-and-drop uploads, instant client-side
   validation, live markdown preview with syntax highlighting, and batch export.
2. **FastAPI backend** — a versioned REST API (`/api/v1/`). Handles file upload
   reception, file signature validation checks, and dispatches files to dedicated
   conversion workers.
3. **Modular Conversion Strategy (MarkItDown)** — wraps Microsoft's `markitdown`
   library using the Strategy pattern (`BaseConverter`). Each document format has
   an isolated converter with custom normalization and structure extraction.
4. **Security & Sanitization Layer** — validates file extensions, MIME types, and
   binary signatures (magic bytes). Enforces upload limits and wraps conversions in
   strict timeout handlers.
5. **Ephemeral Sandbox Processing** — files are processed in isolated temporary
   directories with cryptographically random UUIDs. Temp files are purged immediately
   after conversion. No databases or persistent storage are used.

## ✨ Core Features

- **Multi-format support** — converts PDF, Word (`.docx`), Plain Text (`.txt`),
  HTML (`.html`), CSV (`.csv`), JSON (`.json`), and normalizes existing Markdown (`.md`).
- **Structure preservation** — maintains headings, paragraphs, bullet/numbered
  lists, nested tables, code fences, and hyperlinks.
- **Interactive Markdown preview** — side-by-side or tabbed view showing rendered
  HTML preview alongside the raw Markdown code.
- **Batch processing** — upload multiple files simultaneously and track individual
  conversion statuses.
- **One-click copy & export** — copy Markdown directly to your clipboard or download
  individual `.md` files.
- **Zero-retention privacy** — uploaded files are processed strictly in memory/ephemeral
  storage and wiped immediately upon completion.
- **Actionable error feedback** — clear, descriptive error messages for corrupted,
  password-protected, or unsupported files.
- **Light & dark mode** — polished modern interface designed for focus.
- **Self-contained deployment** — simple one-command orchestration with Docker Compose.

## 🔒 How file2MD protects your data

- **Zero permanent persistence.** file2MD stores no persistent document records or analytics
  trackers. Source files are strictly isolated in temporary directories and deleted immediately
  upon conversion. For asynchronous jobs, results are held in Redis with an ephemeral TTL
  (`JOB_TTL_SECONDS`, default 1 hour) before automatic expiration.
- **Robust file validation.** Every upload is inspected across an extension whitelist and
  magic byte signature inspection to prevent file spoofing and malicious payloads.
- **Isolated execution & safe filenames.** Uploads are written to dedicated temporary
  directories using generated UUIDs, mitigating path traversal and filesystem clashes.
- **No script or macro execution.** Documents are parsed strictly for text and structural
  nodes; embedded macros or JavaScript payloads are never executed.
- **Timeout & resource protection.** Conversions run under strict timeout envelopes and
  size boundaries to prevent denial-of-service from decompression bombs or corrupted files.
- **Configurable limits.** Administrators can configure upload limits (`MAX_UPLOAD_SIZE_MB`),
  request timeouts, and CORS origins via environment variables.

## 🤔 Why file2MD instead of cloud document converters?

Most online converters upload your files to third-party cloud infrastructure where
data may be cached, indexed, or logged.

**Pros of file2MD**

- **Your documents never leave your control.** Ideal for proprietary code, legal
  contracts, financial sheets, and sensitive personal notes.
- **LLM & RAG-ready Markdown.** Markdown produced by MarkItDown is token-efficient
  and structured specifically for LLM pipelines and knowledge bases.
- **100% Free & Open Source.** No subscription tiers, conversion credits, or file
  count limits.
- **Reproducible & self-hosted.** Runs locally or on private VPS instances via Docker.

**Cons (equally honest)**

- **Self-hosted responsibility.** You manage your own container host and updates.
- **OCR requires optional configuration.** High-accuracy image OCR requires an
  explicitly configured LLM vision client or local engine.
- **No cloud sync.** It is a converter tool, not a cloud document storage vault.

## 🚀 Installation

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

### 1. Clone

```bash
git clone https://github.com/vajapravin/file2md.git
cd file2md
```

### 2. Configure environment (optional)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Adjust variables if needed (e.g., `MAX_UPLOAD_SIZE_MB=50`, `CONVERSION_TIMEOUT_SECONDS=60`).

### 3. Launch with Docker Compose

```bash
docker compose up --build -d
```

Once running, access the services:

| URL | What |
|---|---|
| http://localhost:5173 | file2MD Web Application |
| http://localhost:8000/docs | Interactive Swagger API Documentation |
| http://localhost:8000/api/v1/health | Backend Health Check |

To stop the containers:

```bash
docker compose down
```

## 🧪 Development

### Backend (Python 3.12+)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Lint and formatting
ruff check src/ tests/
ruff format --check src/ tests/

# Type checking
mypy src/

# Run test suite
pytest
```

### Frontend (Node 20+)

```bash
cd frontend
npm install

# Dev server with HMR
npm run dev

# Tests & Linting
npm test
npm run lint
npm run typecheck
```

## 🗺 Roadmap

- [x] Initial multi-format engine (PDF, DOCX, TXT, HTML, CSV, JSON, MD)
- [x] Live side-by-side Markdown preview and clipboard copy
- [x] Strict security sandbox, signature validation, and timeout limits
- [ ] OCR extraction for images using vision models / Tesseract
- [ ] Multi-file archive support (converting all contents of `.zip`)
- [ ] CLI utility (`file2md-cli`) for terminal workflows
- [ ] Syntax highlighting export for code blocks in converted output

## 📄 License

This project is licensed under the [MIT License](LICENSE).
