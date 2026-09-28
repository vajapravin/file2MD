# Contributing to file2MD

Thank you for your interest in contributing to file2MD! This document provides guidelines for contributing to the project.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/your-org/file2MD/issues) to avoid duplicates.
2. Use the bug report template.
3. Include: steps to reproduce, expected behaviour, actual behaviour, and environment details.
4. **Never include file contents or sensitive data in bug reports.**

### Suggesting Features

1. Open an issue with the `enhancement` label.
2. Describe the use case and proposed solution.

### Submitting Changes

1. Fork the repository and create a feature branch from `main`.
2. Make small, focused commits following [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat(backend): add XLSX conversion service`
   - `fix(frontend): handle empty file upload`
   - `test(backend): cover PDF malformed input`
   - `docs: update API reference`
3. Ensure all tests pass and linters are clean.
4. Open a pull request with a clear description.

### Development Setup

See [docs/development.md](docs/development.md) for complete local setup instructions.

### Running Tests

**Backend:**

```bash
cd backend
python -m pytest
```

**Frontend:**

```bash
cd frontend
npm test
```

### Code Style

**Backend:**
- Python 3.12+ with type hints
- Formatted and linted with [Ruff](https://github.com/astral-sh/ruff)
- Type-checked with [mypy](https://mypy-lang.org/)

**Frontend:**
- Strict TypeScript (minimal `any`)
- Formatted with [Prettier](https://prettier.io/)
- Linted with [ESLint](https://eslint.org/)

### Adding a New Conversion Format

See [docs/adding-a-format.md](docs/adding-a-format.md) for the step-by-step process.

## Pull Request Process

1. Update documentation if your change affects the public API or user workflow.
2. Add or update tests for your changes.
3. Ensure CI passes.
4. Request review from a maintainer.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
