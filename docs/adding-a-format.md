# Adding a New Conversion Format

> Full guide will be added in Milestone 10.

## Overview

To add support for a new file format:

1. Create a new converter class in `backend/src/file2md/converters/`.
2. Implement the `BaseConverter` interface.
3. Register the converter in the converter orchestrator.
4. Add the format to the validator's whitelist.
5. Create test fixtures in `backend/tests/fixtures/`.
6. Write unit tests in `backend/tests/unit/test_converters/`.
7. Write API tests in `backend/tests/api/`.
8. Update the supported formats table in `README.md`.
9. Update `docs/api.md` with the new format.
