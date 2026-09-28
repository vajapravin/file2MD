# Development Setup

> Full development instructions will be added in Milestone 10.

## Prerequisites

- Python 3.12+ (use `pyenv` to manage versions)
- Node.js 20+ and npm
- Docker and Docker Compose (for containerised development)

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

# Run the development server
uvicorn file2md.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest

# Lint and format
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/
```

## Frontend

```bash
cd frontend
npm install
cp .env.example .env

# Run the development server
npm run dev

# Run tests
npm test

# Lint and format
npm run lint
npm run format
```

## Docker

```bash
# Start both services
docker compose up --build

# Stop
docker compose down
```
