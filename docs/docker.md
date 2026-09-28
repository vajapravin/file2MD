# Docker Guide

> Full Docker documentation will be added in Milestone 8.

## Quick Start

```bash
docker compose up --build
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/v1/health
- **API Docs**: http://localhost:8000/docs

## Stopping

```bash
docker compose down
```

## Rebuilding

```bash
docker compose up --build --force-recreate
```

## Environment Variables

See `backend/.env.example` and `frontend/.env.example` for available configuration options.
