# Contributing to Code Quality Gate

Thank you for your interest in contributing! This guide will help you get set up and start contributing.

## Development Setup

### Prerequisites
- Python 3.11+
- Docker and Docker Compose (for containerized development)
- Git

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/chandru262005/OCC--Code-Quality.git
   cd OCC--Code-Quality
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   ```

3. Install dependencies:
   ```bash
   make install-dev
   # or manually:
   pip install -r requirements-dev.txt
   ```

4. Run the application:
   ```bash
   make run
   # or manually:
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. Verify it works:
   ```bash
   curl http://localhost:8000/health
   ```

### Docker Setup

```bash
make docker-build    # Build the image
make docker-run      # Run in production mode
make docker-dev      # Run in dev mode with hot reload
```

## Testing

### Running Tests

```bash
make test            # Run all tests with coverage
make lint            # Run linting
make ci              # Run lint + tests (full CI check)
```

### Writing Tests

- Place unit tests in `tests/test_*.py`
- Place analyzer tests in `tests/test_analyzers/`
- Integration tests go in `tests/test_integration.py`
- Use fixtures from `tests/conftest.py` for shared test data
- Mark slow tests with `@pytest.mark.slow`
- Mark integration tests with `@pytest.mark.integration`

### Test Conventions

- Test files must start with `test_`
- Test functions must start with `test_`
- Use descriptive test names: `test_upload_rejects_non_python_file`
- Each test should test one thing

## Code Style

- Maximum line length: 120 characters
- Follow PEP 8 conventions
- Use type hints where possible
- Add docstrings to all public functions and classes
- Run `make lint` before committing

## Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure:
   - All tests pass: `make test`
   - Linting passes: `make lint`
   - New features have tests

3. Commit with meaningful messages:
   ```
   type: short description

   Types: feat, fix, refactor, test, docs, chore
   Examples:
     feat: add upload endpoint
     fix: handle empty file upload
     test: add security analyzer tests
   ```

4. Push and create a Pull Request to `main`

5. Get at least 1 code review approval

## Project Structure

```
app/
├── main.py              # FastAPI entry point
├── config.py            # App configuration
├── logging_config.py    # Logging setup
├── models/              # Pydantic request/response models
├── routes/              # API endpoint handlers
├── services/            # Business logic (file handling, GitHub, reports)
└── analyzers/           # Analysis engines (lint, static, security)

tests/
├── conftest.py          # Shared test fixtures
├── test_upload.py       # Upload endpoint tests
├── test_github.py       # GitHub endpoint tests
├── test_integration.py  # End-to-end tests
└── test_analyzers/      # Analyzer unit tests
```

## Questions?

Open an issue on the repository for any questions or suggestions.
