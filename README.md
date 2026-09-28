# file2MD

> Convert files to clean, readable Markdown.

file2MD is an open-source web application that converts supported document formats into well-structured Markdown files. It preserves meaningful document structure — headings, paragraphs, lists, tables, and links — using Microsoft's [markitdown](https://github.com/microsoft/markitdown) library.

## Supported Formats

| Format | Extension | Status |
|--------|-----------|--------|
| PDF | `.pdf` | 🚧 Planned |
| Word | `.docx` | 🚧 Planned |
| Plain Text | `.txt` | 🚧 Planned |
| HTML | `.html` | 🚧 Planned |
| CSV | `.csv` | 🚧 Planned |
| JSON | `.json` | 🚧 Planned |
| Markdown | `.md` | 🚧 Planned |

> Format support is listed only after implementation and tests exist.

## Architecture

file2MD is composed of two independent applications:

- **`backend/`** — Python 3.12, FastAPI, Pydantic, modular conversion services
- **`frontend/`** — React, TypeScript, Vite, Tailwind CSS

They communicate exclusively through documented HTTP APIs (`/api/v1/`).

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

### Run with Docker Compose

```bash
git clone https://github.com/your-org/file2MD.git
cd file2MD
docker compose up --build
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/v1/health
- **API Docs**: http://localhost:8000/docs

### Local Development

See [docs/development.md](docs/development.md) for full instructions.

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Development Setup](docs/development.md)
- [Docker Guide](docs/docker.md)
- [Security](docs/security.md)
- [Adding a Format](docs/adding-a-format.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## License

This project is licensed under the [MIT License](LICENSE).

### Third-Party Licenses

file2MD depends on open-source libraries. Key dependencies and their licenses:

| Library | License |
|---------|---------|
| [markitdown](https://github.com/microsoft/markitdown) | MIT |
| [FastAPI](https://fastapi.tiangolo.com/) | MIT |
| [React](https://react.dev/) | MIT |
| [Vite](https://vite.dev/) | MIT |
| [Tailwind CSS](https://tailwindcss.com/) | MIT |

A complete list is available in each application's dependency manifest (`backend/pyproject.toml`, `frontend/package.json`).
