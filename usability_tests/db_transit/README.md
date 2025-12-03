## Usability Tests for db_transit

Goal: validate the ergonomics and ease-of-use of the `DbTransitClient` (DB transport.rest API) without network access, using asynchronous HTTP mocks.

- Covered scenarios:
  - Input validation and explicit error messages
  - API parameter construction (/locations, /locations/nearby, /journeys)
  - Resolving stops from coordinates before route search
  - Ergonomics: ISO 8601 normalization, departure/arrival exclusivity
  - API surface: configuration, HTTP client reuse, clean shutdown

### Prerequisites
- Python 3.14+
- uv (package manager)

Test dependencies are declared as dev-dependencies in `pyproject.toml`. uv will resolve them automatically at runtime.

### Run

```bash
uv run -m pytest -q usability_tests/db_transit
```

These tests do not use the network: they patch the internal HTTP client and inject controlled responses.

### Structure

- `usability_tests/db_transit/conftest.py`: asynchronous HTTP mocks and patch utilities.
- `usability_tests/db_transit/test_*.py`: usability and ergonomics test suites.
