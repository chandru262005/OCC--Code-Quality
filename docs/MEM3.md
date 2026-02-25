# Member 3: DevOps, CI/CD & Infrastructure

**Role:** DevOps Engineer
**Branch:** `feature/devops-cicd`
**Focus:** Docker containerization, Jenkins pipeline, Makefile, testing infrastructure, deployment configuration, and CI/CD integration.

---

## Project Overview

A Python-based web application that accepts code file uploads (or GitHub repo URLs),
runs lint analysis, static analysis, and security pattern scanning, then returns a
structured quality report. Integrable with Jenkins pipelines to fail builds below a
quality threshold.

---

## Target Project Structure

```
code-quality-gate/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point          (Member 1)
│   ├── config.py                # App configuration                (Member 1)
│   ├── models/                                                     (Member 1)
│   ├── routes/                                                     (Member 1)
│   ├── services/                                                   (Member 1)
│   ├── logging_config.py        # Structured logging               <<<< YOURS
│   └── analyzers/                                                  (Member 2)
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures                  <<<< YOURS
│   ├── test_upload.py                                              (Member 1)
│   ├── test_github.py                                              (Member 1)
│   ├── test_analyzers/                                             (Member 2)
│   └── test_integration.py      # End-to-end tests                <<<< YOURS
├── scripts/                                                        <<<< YOUR DOMAIN
│   └── quality_gate.sh          # Standalone quality gate script
├── .github/workflows/                                              <<<< YOUR DOMAIN
│   └── ci.yml                   # GitHub Actions CI pipeline
├── sample_files/                                                   (Member 1 & 2)
├── Dockerfile                                                      <<<< YOURS
├── .dockerignore                                                   <<<< YOURS
├── docker-compose.yml                                              <<<< YOURS
├── Jenkinsfile                                                     <<<< YOURS
├── Makefile                                                        <<<< YOURS
├── pytest.ini                                                      <<<< YOURS
├── .flake8                                                         <<<< YOURS
├── .env.example                                                    <<<< YOURS
├── CONTRIBUTING.md                                                 <<<< YOURS
├── requirements.txt                                                (Member 1)
├── requirements-dev.txt                                            (Member 1)
├── .gitignore                                                      (Member 1)
└── README.md                                                       (Member 1, you add deployment section)
```

---

## Git Workflow

- `main` branch: stable, protected
- Your feature branch: `feature/devops-cicd`
- Other members:
  - `feature/api-core` (Member 1)
  - `feature/analyzers` (Member 2)
- Pull requests to `main` with at least 1 review
- Merge conflicts resolved by the branch owner
- Commit messages follow: `type: short description` (e.g., `feat: add Dockerfile`)

---

## Your Files (Ownership)

You are responsible for creating and maintaining:

| File | Description |
|------|-------------|
| `Dockerfile` | Multi-stage Docker build for the API |
| `.dockerignore` | Files excluded from Docker build context |
| `docker-compose.yml` | Production and dev service definitions |
| `Jenkinsfile` | Full Jenkins CI/CD pipeline |
| `Makefile` | All common dev/build/test/deploy commands |
| `pytest.ini` | Pytest configuration |
| `.flake8` | Flake8 linting configuration |
| `.env.example` | Documented environment variables |
| `tests/conftest.py` | Shared test fixtures |
| `tests/test_integration.py` | End-to-end integration tests |
| `scripts/quality_gate.sh` | Standalone CI quality gate script |
| `.github/workflows/ci.yml` | GitHub Actions CI pipeline |
| `app/logging_config.py` | Structured JSON logging config |
| `CONTRIBUTING.md` | Dev setup, testing, and PR guidelines |

---

## Day 1 - Docker Setup & Makefile

### Morning: Dockerfile
- [ ] Create `Dockerfile`:
  ```dockerfile
  # Multi-stage build for smaller image
  FROM python:3.11-slim as base

  # Set environment variables
  ENV PYTHONDONTWRITEBYTECODE=1 \
      PYTHONUNBUFFERED=1 \
      PIP_NO_CACHE_DIR=1

  WORKDIR /app

  # Install system dependencies (git needed for cloning repos)
  RUN apt-get update && \
      apt-get install -y --no-install-recommends git && \
      rm -rf /var/lib/apt/lists/*

  # Install Python dependencies
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  # Copy application code
  COPY . .

  # Create non-root user
  RUN useradd -m appuser && \
      mkdir -p /tmp/cqg_uploads /tmp/cqg_repos && \
      chown -R appuser:appuser /app /tmp/cqg_uploads /tmp/cqg_repos
  USER appuser

  EXPOSE 8000

  HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
      CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- [ ] Create `.dockerignore`:
  ```
  .git
  .gitignore
  __pycache__
  *.pyc
  .env
  venv/
  .venv/
  .pytest_cache/
  .coverage
  htmlcov/
  ```

### Afternoon: Docker Compose & Makefile
- [ ] Create `docker-compose.yml`:
  ```yaml
  version: "3.8"
  services:
    api:
      build:
        context: .
        dockerfile: Dockerfile
      ports:
        - "8000:8000"
      environment:
        - QUALITY_THRESHOLD=6.0
        - DEBUG=false
        - LOG_LEVEL=info
      volumes:
        - upload_data:/tmp/cqg_uploads
        - repo_data:/tmp/cqg_repos
      restart: unless-stopped

    api-dev:
      build:
        context: .
        dockerfile: Dockerfile
      ports:
        - "8000:8000"
      environment:
        - DEBUG=true
        - LOG_LEVEL=debug
      volumes:
        - .:/app                    # Mount source for hot reload
        - upload_data:/tmp/cqg_uploads
        - repo_data:/tmp/cqg_repos
      command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  volumes:
    upload_data:
    repo_data:
  ```
- [ ] Create `Makefile`:
  ```makefile
  .PHONY: help install run test lint docker-build docker-run clean

  help:            ## Show this help message
  install:         ## Install dependencies
  install-dev:     ## Install dev dependencies
  run:             ## Run the app locally
  test:            ## Run tests with coverage
  lint:            ## Run linting on project code
  docker-build:    ## Build Docker image
  docker-run:      ## Run with Docker Compose
  docker-dev:      ## Run with Docker Compose (dev mode with hot reload)
  docker-stop:     ## Stop Docker containers
  docker-test:     ## Run tests inside Docker
  clean:           ## Clean temp files, caches, build artifacts
  ```
- [ ] Verify: `docker build -t code-quality-gate .` builds successfully
- [ ] Verify: `docker-compose up api` runs the app and health check passes

### Deliverables
- Working Dockerfile with multi-stage build
- docker-compose.yml with production and dev services
- Makefile with all common commands
- Container builds and runs successfully

---

## Day 2 - Testing Infrastructure & CI Config

### Morning: Testing Setup
- [ ] Create `pytest.ini`:
  ```ini
  [pytest]
  testpaths = tests
  python_files = test_*.py
  python_functions = test_*
  addopts = -v --tb=short --strict-markers
  markers =
      unit: Unit tests
      integration: Integration tests
      slow: Slow tests (> 5s)
  ```
- [ ] Create `tests/conftest.py`:
  ```python
  import pytest
  from fastapi.testclient import TestClient
  from app.main import app

  @pytest.fixture
  def client():
      return TestClient(app)

  @pytest.fixture
  def sample_clean_code():
      return '''
  def add(a: int, b: int) -> int:
      """Add two numbers."""
      return a + b
  '''

  @pytest.fixture
  def sample_buggy_code():
      return '''
  import os
  import sys
  import json  # unused

  def x(a,b,c,d,e,f,g):
      if a:
          if b:
              if c:
                  if d:
                      return e
      return None
  '''

  @pytest.fixture
  def sample_insecure_code():
      return '''
  import os
  password = "super_secret_123"
  os.system("rm -rf " + user_input)
  eval(user_input)
  '''

  @pytest.fixture
  def sample_file_path(tmp_path, sample_clean_code):
      p = tmp_path / "test_file.py"
      p.write_text(sample_clean_code)
      return str(p)
  ```
- [ ] Create `tests/test_integration.py`:
  ```python
  # End-to-end tests that test the full flow:
  # 1. Upload file -> get report -> verify structure
  # 2. Upload clean file -> verify high score
  # 3. Upload buggy file -> verify low score
  # 4. Upload insecure file -> verify security issues detected
  # 5. Test threshold pass/fail logic
  ```

### Afternoon: CI Lint & Pre-commit
- [ ] Create `.flake8` config:
  ```ini
  [flake8]
  max-line-length = 120
  exclude = .git,__pycache__,venv,.venv,build,dist
  ignore = E203,W503
  ```
- [ ] Add `Makefile` target for full CI check:
  ```makefile
  ci: lint test  ## Run full CI pipeline locally
  ```
- [ ] Verify `make test` runs all tests with coverage report
- [ ] Verify `make lint` checks code style
- [ ] Add `make docker-test` that runs tests inside the container:
  ```makefile
  docker-test:
      docker-compose run --rm api pytest tests/ -v --cov=app --cov-report=term-missing
  ```

### Deliverables
- Full test infrastructure with fixtures
- Integration tests covering the complete flow
- CI-compatible Makefile commands
- Linting configuration

---

## Day 3 - Jenkins Pipeline

### Morning: Jenkinsfile
- [ ] Create `Jenkinsfile`:
  ```groovy
  pipeline {
      agent any

      environment {
          DOCKER_IMAGE = 'code-quality-gate'
          DOCKER_TAG = "${BUILD_NUMBER}"
          QUALITY_THRESHOLD = '6.0'
      }

      stages {
          stage('Checkout') {
              steps {
                  checkout scm
              }
          }

          stage('Build Docker Image') {
              steps {
                  script {
                      docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                  }
              }
          }

          stage('Run Unit Tests') {
              steps {
                  script {
                      docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").inside {
                          sh 'pip install -r requirements-dev.txt'
                          sh 'pytest tests/ -v --junitxml=reports/junit.xml --cov=app --cov-report=xml:reports/coverage.xml'
                      }
                  }
              }
              post {
                  always {
                      junit 'reports/junit.xml'
                      publishHTML([
                          reportName: 'Coverage Report',
                          reportDir: 'reports',
                          reportFiles: 'coverage.xml'
                      ])
                  }
              }
          }

          stage('Code Quality Gate') {
              steps {
                  script {
                      // Start the API server
                      docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").withRun('-p 8000:8000') { container ->
                          // Wait for server to be ready
                          sh '''
                              for i in $(seq 1 30); do
                                  if curl -s http://localhost:8000/health | grep -q "healthy"; then
                                      break
                                  fi
                                  sleep 1
                              done
                          '''

                          // Analyze the project's own code
                          sh """
                              REPORT=\$(curl -s -X POST http://localhost:8000/api/v1/analyze/file \\
                                  -F "file=@app/main.py" \\
                                  -F "threshold=${QUALITY_THRESHOLD}")

                              echo "Quality Report:"
                              echo "\${REPORT}" | python -m json.tool

                              PASSED=\$(echo "\${REPORT}" | python -c "import sys,json; print(json.load(sys.stdin)['passed'])")

                              if [ "\${PASSED}" = "False" ]; then
                                  echo "QUALITY GATE FAILED - Score below threshold ${QUALITY_THRESHOLD}"
                                  exit 1
                              fi

                              echo "QUALITY GATE PASSED"
                          """
                      }
                  }
              }
          }

          stage('Push Image') {
              when {
                  branch 'main'
              }
              steps {
                  script {
                      docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push()
                      docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push('latest')
                  }
              }
          }
      }

      post {
          always {
              cleanWs()
          }
          success {
              echo 'Pipeline completed successfully!'
          }
          failure {
              echo 'Pipeline failed!'
          }
      }
  }
  ```

### Afternoon: Jenkins Client Script
- [ ] Create `scripts/quality_gate.sh`:
  ```bash
  #!/bin/bash
  # Standalone script to run quality gate check against the API
  # Usage: ./scripts/quality_gate.sh <file_or_repo_url> [threshold]
  #
  # Examples:
  #   ./scripts/quality_gate.sh ./my_code.py 7.0
  #   ./scripts/quality_gate.sh https://github.com/user/repo 6.0
  #
  # Exit codes:
  #   0 - Quality gate passed
  #   1 - Quality gate failed
  #   2 - Error (API unreachable, invalid input, etc.)
  ```
  - Implement the script with:
    - Auto-detect if input is file or GitHub URL
    - Call appropriate API endpoint
    - Pretty-print the quality report
    - Exit with code 0 (pass) or 1 (fail)
    - Support `CQG_API_URL` environment variable (default: http://localhost:8000)
    - Support `CQG_THRESHOLD` environment variable (default: 6.0)
- [ ] Make script executable: `chmod +x scripts/quality_gate.sh`
- [ ] Test the script locally against running API

### Deliverables
- Complete Jenkinsfile with build, test, quality gate, and push stages
- Standalone quality gate script usable in any CI system
- Quality gate fails the build when score < threshold

---

## Day 4 - Advanced CI/CD & Monitoring

### Morning: GitHub Actions (Bonus CI)
- [ ] Create `.github/workflows/ci.yml`:
  ```yaml
  name: CI Pipeline

  on:
    push:
      branches: [main]
    pull_request:
      branches: [main]

  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: '3.11'
        - name: Install dependencies
          run: |
            pip install -r requirements.txt
            pip install -r requirements-dev.txt
        - name: Run linting
          run: flake8 app/ tests/
        - name: Run tests
          run: pytest tests/ -v --cov=app --cov-report=xml
        - name: Upload coverage
          uses: codecov/codecov-action@v3

    docker:
      needs: test
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - name: Build Docker image
          run: docker build -t code-quality-gate .
        - name: Run tests in Docker
          run: docker run --rm code-quality-gate pytest tests/ -v

    quality-gate:
      needs: docker
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - name: Build and start API
          run: |
            docker-compose up -d api
            sleep 10
        - name: Run quality gate on own code
          run: |
            for file in app/*.py app/**/*.py; do
              if [ -f "$file" ]; then
                echo "Analyzing: $file"
                curl -s -X POST http://localhost:8000/api/v1/analyze/file \
                  -F "file=@$file" -F "threshold=6.0" | python -m json.tool
              fi
            done
        - name: Stop API
          run: docker-compose down
  ```

### Afternoon: Logging, Health Monitoring & .env Configuration
- [ ] Add structured JSON logging configuration:
  - Create `app/logging_config.py` with:
    - JSON formatter for production
    - Colored console formatter for development
    - Log rotation configuration
    - Configurable log level via environment variable
- [ ] Enhance `docker-compose.yml` with:
  - Log volume mounts
  - Resource limits (memory, CPU)
  - Health check configuration
- [ ] Create `.env.example` with all environment variables documented:
  ```bash
  # Application
  APP_NAME=Code Quality Gate
  DEBUG=false
  LOG_LEVEL=info

  # Analysis
  QUALITY_THRESHOLD=6.0
  MAX_FILE_SIZE_MB=10
  ANALYZER_TIMEOUT_SECONDS=30

  # Server
  HOST=0.0.0.0
  PORT=8000
  WORKERS=4
  ```
- [ ] Verify all Docker and CI configurations work end-to-end

### Deliverables
- GitHub Actions CI pipeline as backup/alternative to Jenkins
- Structured logging configured
- Docker compose with production-ready settings
- All environment variables documented

---

## Day 5 - Final Integration, Testing & Deployment Readiness

### Morning: End-to-End Pipeline Validation
- [ ] Run complete Jenkins pipeline locally (if Jenkins available) or validate Jenkinsfile syntax
- [ ] Run complete GitHub Actions workflow validation:
  ```bash
  # Use act to test locally (optional)
  act -j test
  ```
- [ ] Full end-to-end test:
  1. `docker-compose build` (clean build)
  2. `docker-compose up api`
  3. Run `scripts/quality_gate.sh` against sample files
  4. Verify pass/fail behavior
  5. `docker-compose down`
- [ ] Test `make` commands all work:
  - `make install`
  - `make test`
  - `make lint`
  - `make docker-build`
  - `make docker-run`
  - `make docker-test`
  - `make clean`

### Afternoon: Documentation & Final Merge
- [ ] Add deployment section to README (coordinate with Member 1):
  - Docker deployment instructions
  - Jenkins integration guide
  - GitHub Actions setup
  - Environment variable reference
- [ ] Create `CONTRIBUTING.md` with:
  - Development setup instructions
  - Testing guidelines
  - PR process
- [ ] Final review of all DevOps configs
- [ ] Merge `feature/devops-cicd` to `main`
- [ ] Verify final `main` branch:
  - Docker builds cleanly
  - All tests pass
  - CI pipeline works

### Deliverables
- All CI/CD pipelines validated
- Docker deployment working
- Documentation complete
- Merged to main

---

## Integration Points (What You Need From Others)

### From Member 1 (Backend API) - Needed by Day 1
- `requirements.txt` with core dependencies (you need this to build Docker image)
- Working `app/main.py` with at least the health check endpoint (for Docker HEALTHCHECK)
- Stable API endpoints by Day 3 afternoon (for Jenkins quality gate stage)

### From Member 2 (Analysis Engines) - Needed by Day 1
- List of pip dependencies needed: `pylint`, `flake8`, `radon`, `bandit`
- Confirmation of any system-level packages required (beyond `git`)
- All analyzer deps must be in `requirements.txt` for Docker build

### What You Provide to Others
- **To Member 1 (Day 1):** Working Docker setup so they can test their API in containers
- **To Member 2 (Day 4):** Confirmation that analyzers work inside Docker
- **To Both (Day 2):** Test fixtures in `conftest.py`, pytest configuration, Makefile commands

---

## Coordination Schedule

| Day | Morning Sync | Afternoon Check-in |
|-----|-------------|-------------------|
| Day 1 | Get `requirements.txt` from M1, dep list from M2 | Verify Docker builds with initial skeleton |
| Day 2 | Share test infrastructure with team | Confirm `make test` and `make lint` work for all |
| Day 3 | Share Jenkinsfile draft with team for review | Test Jenkins pipeline against M1's API |
| Day 4 | Full integration testing in Docker | Bug fixes, verify all analyzers work in container |
| Day 5 | Final pipeline validation | Merge to main, verify everything works, demo prep |

---

## Infrastructure Architecture Reference

```
┌─────────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline Flow                       │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌───────┐ │
│  │ Checkout │───>│  Build   │───>│  Test    │───>│ Quality│ │
│  │   SCM    │    │  Docker  │    │  Suite   │    │  Gate  │ │
│  └──────────┘    └──────────┘    └──────────┘    └───┬───┘ │
│                                                      │      │
│                                          ┌───────────┤      │
│                                          │           │      │
│                                     PASS ▼      FAIL ▼      │
│                                   ┌──────────┐ ┌─────────┐  │
│                                   │  Push    │ │  Abort  │  │
│                                   │  Image   │ │  Build  │  │
│                                   └──────────┘ └─────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Docker Architecture                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Docker Container                        │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │           Python 3.11-slim                    │   │    │
│  │  │  ┌────────────────────────────────────────┐  │   │    │
│  │  │  │         FastAPI Application             │  │   │    │
│  │  │  │  ┌─────┐  ┌────────┐  ┌────────────┐  │  │   │    │
│  │  │  │  │ API │  │Analyzers│  │  Services   │  │  │   │    │
│  │  │  │  │Route│  │pylint   │  │file_handler │  │  │   │    │
│  │  │  │  │     │  │radon    │  │github_handle│  │  │   │    │
│  │  │  │  │     │  │bandit   │  │report_build │  │  │   │    │
│  │  │  │  └─────┘  └────────┘  └────────────┘  │  │   │    │
│  │  │  └────────────────────────────────────────┘  │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                     │    │
│  │  Volumes: /tmp/cqg_uploads, /tmp/cqg_repos          │    │
│  │  Port: 8000                                         │    │
│  │  User: appuser (non-root)                           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Key Commands Quick Reference

| Command | Description |
|---------|-------------|
| `make install` | Install production dependencies |
| `make install-dev` | Install dev + test dependencies |
| `make run` | Start API locally on port 8000 |
| `make test` | Run tests with coverage |
| `make lint` | Run flake8 linting |
| `make ci` | Run lint + test (full local CI) |
| `make docker-build` | Build Docker image |
| `make docker-run` | Run API via docker-compose |
| `make docker-dev` | Run API with hot reload |
| `make docker-test` | Run tests inside Docker |
| `make docker-stop` | Stop all containers |
| `make clean` | Remove caches and temp files |
