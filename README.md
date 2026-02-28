# Code Quality Gate API

A Python-based web application that accepts code file uploads (or GitHub repo URLs), runs lint analysis, static analysis, and security pattern scanning, then returns a structured quality report. Integrable with Jenkins pipelines to fail builds below a quality threshold.

## Features

- **File Upload Analysis** - Upload Python files for instant quality analysis
- **GitHub Repo Analysis** - Analyze entire GitHub repositories by URL
- **Three Analysis Engines:**
  - Lint Analysis (Flake8-based) - code style and formatting
  - Static Analysis (Radon + AST) - complexity, maintainability, code smells
  - Security Scanning (Regex patterns) - hardcoded credentials, injection risks, dangerous functions
- **Quality Gate** - Pass/fail based on configurable score threshold
- **CI/CD Integration** - Jenkins pipeline, GitHub Actions, standalone script
- **Docker Support** - Production-ready containerized deployment

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Test the health endpoint
curl http://localhost:8000/health
```

### Docker

```bash
# Build and run
docker-compose up -d api

# Or use the Makefile
make docker-build
make docker-run
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | Swagger API documentation |
| POST | `/api/v1/analyze/file` | Analyze an uploaded Python file |
| POST | `/api/v1/analyze/github` | Analyze a GitHub repository |
| GET | `/api/v1/reports/{id}` | Retrieve a stored report |
| GET | `/api/v1/reports` | List all stored reports |

### Example: Analyze a File

```bash
curl -X POST http://localhost:8000/api/v1/analyze/file \
  -F "file=@sample_files/buggy_code.py" \
  -F "threshold=6.0"
```

### Example: Analyze a GitHub Repo

```bash
curl -X POST http://localhost:8000/api/v1/analyze/github \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo", "threshold": 6.0}'
```

## Deployment

### Docker Deployment

```bash
# Production
docker-compose up -d api

# Development (with hot reload)
docker-compose up api-dev

# Stop
docker-compose down
```

### Jenkins Integration

The project includes a `Jenkinsfile` with stages for:
1. Checkout
2. Docker Build
3. Unit Tests
4. Code Linting
5. Quality Gate Check
6. Image Push (on main branch)

### GitHub Actions

CI pipeline (`.github/workflows/ci.yml`) runs automatically on:
- Push to `main`
- Pull requests to `main`

### Standalone Quality Gate Script

```bash
# Analyze a local file
./scripts/quality_gate.sh ./my_code.py 7.0

# Analyze a GitHub repo
./scripts/quality_gate.sh https://github.com/user/repo 6.0

# Environment variables
export CQG_API_URL=http://localhost:8000
export CQG_THRESHOLD=7.0
```

## Configuration

All settings can be configured via environment variables. See `.env.example` for the full list.

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `info` | Logging level |
| `QUALITY_THRESHOLD` | `6.0` | Default quality gate threshold |
| `MAX_FILE_SIZE_MB` | `10` | Maximum upload file size |
| `PORT` | `8000` | Server port |

## Scoring

The overall quality score (0-10) is a weighted average:
- **Lint** (40%) - Code style via Flake8
- **Static Analysis** (35%) - Complexity via Radon + AST code smell detection
- **Security** (25%) - Pattern-based vulnerability scanning

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing guidelines, and PR process.

### Common Commands

```bash
make help          # Show all available commands
make install-dev   # Install dev dependencies
make run           # Run locally
make test          # Run tests with coverage
make lint          # Run linting
make ci            # Run full CI pipeline locally
make clean         # Clean temp files
```

## Team

- **Member 1** - Backend API & Core Architecture
- **Member 2** - Analysis Engines
- **Member 3** - DevOps, CI/CD & Infrastructure
