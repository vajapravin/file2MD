# Architecture

> Full architecture documentation will be added in Milestone 10.

## Overview

file2MD follows a client-server architecture with two independent applications:

- **Backend** (`backend/`): Python 3.12, FastAPI — handles file validation, conversion, and API serving.
- **Frontend** (`frontend/`): React, TypeScript, Vite, Tailwind CSS — provides the user interface.

## Conversion Pipeline

1. User uploads a file via the frontend.
2. Frontend sends the file to `POST /api/v1/convert`.
3. Backend validates the file (extension, MIME type, size, file signature).
4. Backend selects the appropriate converter based on file type.
5. The converter uses `markitdown` to produce Markdown output.
6. Backend returns the Markdown in the response.
7. Frontend renders the preview and offers copy/download.

## Key Design Decisions

- **Strategy pattern** for converters: each format has an isolated converter class.
- **markitdown** as the core conversion engine: avoids custom parsers.
- **No database**: stateless conversion — files are not persisted.
- **No authentication**: not required for the initial release scope.
