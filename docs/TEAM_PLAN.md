# Code Quality Gate API - 5 Day Team Plan

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
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # App configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py           # Request schemas (Pydantic)
│   │   └── report.py            # Report/response schemas
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── upload.py            # File upload endpoints
│   │   ├── github.py            # GitHub repo analysis endpoints
│   │   ├── report.py            # Report retrieval endpoints
│   │   └── health.py            # Health check endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_handler.py      # File upload & temp storage logic
│   │   ├── github_handler.py    # Clone & manage GitHub repos
│   │   └── report_builder.py    # Aggregate results into final report
│   └── analyzers/
│       ├── __init__.py
│       ├── base.py              # Abstract base analyzer class
│       ├── lint_analyzer.py     # Pylint / Flake8 integration
│       ├── static_analyzer.py   # Complexity & code smell detection
│       └── security_analyzer.py # Security pattern scanner
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_upload.py           # Upload endpoint tests
│   ├── test_github.py           # GitHub endpoint tests
│   ├── test_analyzers/
│   │   ├── __init__.py
│   │   ├── test_lint.py
│   │   ├── test_static.py
│   │   └── test_security.py
│   └── test_integration.py      # End-to-end tests
├── sample_files/                 # Sample code files for testing
│   ├── clean_code.py
│   ├── buggy_code.py
│   └── insecure_code.py
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── .flake8
├── pytest.ini
├── Makefile
└── README.md
```

---

## Git Workflow

- `main` branch: stable, protected
- Each member works on their own feature branch:
  - `feature/api-core` (Member 1)
  - `feature/analyzers` (Member 2)
  - `feature/devops-cicd` (Member 3)
- Pull requests to `main` with at least 1 review
- Merge conflicts resolved by the branch owner
- Commit messages follow: `type: short description` (e.g., `feat: add upload endpoint`)

---

# MEMBER 1: Backend API & Core Architecture

**Role:** API Developer & Project Architect
**Branch:** `feature/api-core`
**Focus:** FastAPI application, endpoints, request/response models, file handling, GitHub integration, report builder, and project scaffolding.

---

## Day 1 - Project Setup & Core API Skeleton

### Morning: Project Initialization
- [ ] Initialize Python project with proper structure (see tree above)
- [ ] Create `requirements.txt` with core dependencies:
  ```
  fastapi==0.104.1
  uvicorn==0.24.0
  python-multipart==0.0.6
  pydantic==2.5.0
  gitpython==3.1.40
  aiofiles==23.2.1
  ```
- [ ] Create `requirements-dev.txt`:
  ```
  pytest==7.4.3
  pytest-asyncio==0.23.0
  httpx==0.25.2
  pytest-cov==4.1.0
  ```
- [ ] Create `.gitignore` (Python template + venv, .env, __pycache__, uploads/, repos/)
- [ ] Create `.env.example` with placeholder config values
- [ ] Create `app/__init__.py` and `app/config.py` with settings using pydantic BaseSettings:
  ```python
  # config.py should include:
  class Settings(BaseSettings):
      APP_NAME: str = "Code Quality Gate"
      UPLOAD_DIR: str = "/tmp/cqg_uploads"
      REPO_DIR: str = "/tmp/cqg_repos"
      MAX_FILE_SIZE_MB: int = 10
      QUALITY_THRESHOLD: float = 6.0  # out of 10
      ALLOWED_EXTENSIONS: list = [".py"]
      DEBUG: bool = False
  ```

### Afternoon: FastAPI App & Health Check
- [ ] Create `app/main.py` - FastAPI app instance with:
  - CORS middleware
  - Startup/shutdown events (create temp directories)
  - Include all routers
- [ ] Create `app/routes/health.py`:
  - `GET /health` - returns `{"status": "healthy", "version": "1.0.0"}`
  - `GET /` - redirect to `/docs`
- [ ] Verify app runs locally with `uvicorn app.main:app --reload`
- [ ] Write first test: `tests/test_health.py` - test health endpoint returns 200

### Deliverables
- Running FastAPI app with health check
- Project structure committed to `feature/api-core`
- All team members can clone and run `pip install -r requirements.txt && uvicorn app.main:app`

---

## Day 2 - Request/Response Models & File Upload

### Morning: Pydantic Models
- [ ] Create `app/models/request.py`:
  ```python
  class FileUploadRequest:
      # Handled via Form + UploadFile, no explicit model needed
      # But document expected fields:
      # - file: UploadFile (required)
      # - threshold: Optional[float] = 6.0

  class GitHubAnalysisRequest(BaseModel):
      repo_url: str  # e.g. "https://github.com/user/repo"
      branch: str = "main"
      threshold: float = 6.0
      file_extensions: list[str] = [".py"]
  ```
- [ ] Create `app/models/report.py`:
  ```python
  class AnalyzerResult(BaseModel):
      analyzer_name: str       # "lint", "static", "security"
      score: float             # 0-10
      issues: list[Issue]
      summary: str

  class Issue(BaseModel):
      severity: str            # "error", "warning", "info"
      message: str
      file: str
      line: int | None
      rule: str | None

  class QualityReport(BaseModel):
      report_id: str           # UUID
      timestamp: str           # ISO format
      source: str              # "upload" or "github"
      files_analyzed: int
      overall_score: float     # Weighted average 0-10
      threshold: float
      passed: bool             # overall_score >= threshold
      results: list[AnalyzerResult]
      summary: str
  ```

### Afternoon: File Upload Endpoint
- [ ] Create `app/services/file_handler.py`:
  - `save_upload(file: UploadFile) -> Path` - save uploaded file to temp dir with UUID prefix
  - `cleanup_upload(path: Path)` - delete temp file
  - `validate_file(file: UploadFile)` - check extension, size
- [ ] Create `app/routes/upload.py`:
  - `POST /api/v1/analyze/file` - accepts file upload + optional threshold
    - Validate file
    - Save to temp directory
    - Call analyzers (placeholder for now - return mock report)
    - Return QualityReport
    - Cleanup temp file
  - Error handling: 400 for invalid file, 413 for too large, 500 for analysis failure
- [ ] Write tests: `tests/test_upload.py`
  - Test successful upload with a .py file
  - Test rejection of non-.py file
  - Test file size validation

### Deliverables
- File upload endpoint working with mock analysis results
- Pydantic models defined and validated
- Tests passing

---

## Day 3 - GitHub Integration & Report Builder

### Morning: GitHub Repo Handler
- [ ] Create `app/services/github_handler.py`:
  - `clone_repo(url: str, branch: str) -> Path` - clone repo to temp dir
    - Use GitPython
    - Validate URL format (must be valid GitHub URL)
    - Handle errors: invalid URL, private repo, clone failure
    - Return path to cloned directory
  - `list_python_files(repo_path: Path, extensions: list[str]) -> list[Path]`
    - Walk directory, return all matching files
    - Skip hidden dirs, venv, node_modules, __pycache__
  - `cleanup_repo(path: Path)` - remove cloned repo directory

### Afternoon: GitHub Endpoint & Report Builder
- [ ] Create `app/routes/github.py`:
  - `POST /api/v1/analyze/github` - accepts GitHubAnalysisRequest
    - Clone repository
    - List target files
    - Run analyzers on each file (placeholder for now)
    - Build and return QualityReport
    - Cleanup cloned repo
- [ ] Create `app/services/report_builder.py`:
  - `build_report(analyzer_results: list[AnalyzerResult], source: str, threshold: float) -> QualityReport`
    - Calculate overall_score as weighted average:
      - Lint: 40% weight
      - Static Analysis: 35% weight
      - Security: 25% weight
    - Determine pass/fail
    - Generate human-readable summary
- [ ] Create `app/routes/report.py`:
  - `GET /api/v1/reports/{report_id}` - retrieve a stored report (in-memory dict for now)
- [ ] Write tests for GitHub endpoint and report builder

### Deliverables
- GitHub repo analysis endpoint working
- Report builder aggregating scores correctly
- Both endpoints return consistent QualityReport format

---

## Day 4 - Integration with Analyzers & Error Handling

### Morning: Wire Up Real Analyzers
- [ ] Coordinate with **Member 2** to integrate real analyzers
- [ ] Update `app/routes/upload.py` and `app/routes/github.py`:
  - Replace mock analysis with real analyzer calls
  - Import and instantiate: `LintAnalyzer`, `StaticAnalyzer`, `SecurityAnalyzer`
  - Run all three analyzers on uploaded/cloned files
  - Pass results to `report_builder.build_report()`
- [ ] Handle analyzer errors gracefully:
  - If one analyzer fails, still return results from others
  - Include error info in the failing analyzer's result

### Afternoon: Robust Error Handling & Validation
- [ ] Add global exception handler in `app/main.py`
- [ ] Add request validation middleware:
  - Rate limiting (optional, simple in-memory counter)
  - Request size limits
- [ ] Add proper HTTP error responses with detail messages
- [ ] Add logging throughout the application:
  - Use Python `logging` module
  - Log level configurable via env var
  - Log all analysis requests (source, file count, score, pass/fail)
- [ ] Create `sample_files/` with test Python files for demo:
  - `clean_code.py` - well-written code (should score 8+)
  - `buggy_code.py` - code with lint issues and complexity (should score 4-6)
  - `insecure_code.py` - code with security issues (should score 2-4)
- [ ] End-to-end test: upload each sample file, verify scores are reasonable

### Deliverables
- Fully working API with real analyzers integrated
- Proper error handling and logging
- Sample files for testing and demos

---

## Day 5 - Documentation, Polish & Demo Support

### Morning: API Documentation & README
- [ ] Enhance FastAPI auto-docs:
  - Add descriptions to all endpoints
  - Add request/response examples
  - Add tags for grouping
- [ ] Write `README.md` with:
  - Project overview
  - Quick start guide (local + Docker)
  - API endpoint documentation with curl examples
  - Configuration options
  - Architecture diagram (text-based)
- [ ] Add `POST /api/v1/analyze/file` curl example to README:
  ```bash
  curl -X POST http://localhost:8000/api/v1/analyze/file \
    -F "file=@sample_files/buggy_code.py" \
    -F "threshold=6.0"
  ```

### Afternoon: Final Integration & Bug Fixes
- [ ] Coordinate with **Member 3** for Docker & Jenkins testing
- [ ] Fix any integration bugs found during full pipeline testing
- [ ] Final code review on all PRs
- [ ] Merge `feature/api-core` to `main`
- [ ] Tag release: `v1.0.0`

### Deliverables
- Complete, documented API
- All tests passing
- README with usage instructions
- Merged to main

---
---

# MEMBER 2: Analysis Engines

**Role:** Analysis Engine Developer
**Branch:** `feature/analyzers`
**Focus:** All three analysis engines (lint, static, security), the base analyzer interface, scoring logic, and analyzer unit tests.

---

## Day 1 - Base Analyzer & Lint Analysis

### Morning: Base Analyzer Interface
- [ ] Wait for Member 1 to push initial project structure (or create `app/analyzers/` yourself)
- [ ] Create `app/analyzers/base.py`:
  ```python
  from abc import ABC, abstractmethod
  from app.models.report import AnalyzerResult, Issue

  class BaseAnalyzer(ABC):
      """Base class all analyzers must inherit from."""

      @property
      @abstractmethod
      def name(self) -> str:
          """Analyzer name: 'lint', 'static', or 'security'"""
          pass

      @abstractmethod
      def analyze(self, file_path: str, source_code: str) -> AnalyzerResult:
          """
          Analyze a single file and return results.

          Args:
              file_path: Path to the file being analyzed
              source_code: Contents of the file

          Returns:
              AnalyzerResult with score, issues, and summary
          """
          pass

      def analyze_multiple(self, files: dict[str, str]) -> AnalyzerResult:
          """
          Analyze multiple files and aggregate results.

          Args:
              files: dict mapping file_path -> source_code

          Returns:
              Aggregated AnalyzerResult
          """
          all_issues = []
          total_score = 0.0
          for path, code in files.items():
              result = self.analyze(path, code)
              all_issues.extend(result.issues)
              total_score += result.score
          avg_score = total_score / len(files) if files else 0.0
          return AnalyzerResult(
              analyzer_name=self.name,
              score=round(avg_score, 2),
              issues=all_issues,
              summary=self._build_summary(all_issues, avg_score)
          )

      def _build_summary(self, issues: list[Issue], score: float) -> str:
          errors = sum(1 for i in issues if i.severity == "error")
          warnings = sum(1 for i in issues if i.severity == "warning")
          return f"{self.name}: score {score}/10 | {errors} errors, {warnings} warnings"
  ```

### Afternoon: Lint Analyzer (Pylint + Flake8)
- [ ] Add to `requirements.txt`:
  ```
  pylint==3.0.2
  flake8==6.1.0
  ```
- [ ] Create `app/analyzers/lint_analyzer.py`:
  ```python
  class LintAnalyzer(BaseAnalyzer):
      name = "lint"

      def analyze(self, file_path: str, source_code: str) -> AnalyzerResult:
          # Strategy:
          # 1. Run pylint on the file programmatically
          # 2. Parse pylint output (use pylint.lint.Run with reporter)
          # 3. Convert pylint messages to Issue objects
          # 4. Calculate score (pylint gives 0-10 score natively)
          # 5. Return AnalyzerResult
  ```
  - Implementation details:
    - Use `pylint.lint.Run` with `StringIO` reporter to capture output
    - Parse JSON output from pylint (`--output-format=json`)
    - Map pylint message types to severity: C/R -> "info", W -> "warning", E/F -> "error"
    - Use pylint's native score (0-10 scale)
    - Handle files that can't be parsed (syntax errors)
    - Catch and handle pylint crashes gracefully
- [ ] Write `tests/test_analyzers/test_lint.py`:
  - Test with clean Python code (expect high score)
  - Test with code containing lint issues (unused imports, bad names)
  - Test with syntax error file
  - Test score is between 0 and 10

### Deliverables
- Base analyzer class ready for all analyzers to inherit
- Lint analyzer working with pylint integration
- Unit tests for lint analyzer passing

---

## Day 2 - Static Analysis Engine

### Morning: Static Analyzer - Complexity Analysis
- [ ] Add to `requirements.txt`:
  ```
  radon==6.0.1
  ```
- [ ] Create `app/analyzers/static_analyzer.py`:
  ```python
  class StaticAnalyzer(BaseAnalyzer):
      name = "static"

      def analyze(self, file_path: str, source_code: str) -> AnalyzerResult:
          issues = []
          issues.extend(self._check_complexity(file_path, source_code))
          issues.extend(self._check_maintainability(file_path, source_code))
          issues.extend(self._check_code_smells(file_path, source_code))
          score = self._calculate_score(issues)
          return AnalyzerResult(...)
  ```
- [ ] Implement `_check_complexity()`:
  - Use `radon.complexity.cc_visit()` to get cyclomatic complexity
  - Flag functions with complexity > 10 as "error"
  - Flag functions with complexity 6-10 as "warning"
  - Include function name, line number, and complexity value in issue message
- [ ] Implement `_check_maintainability()`:
  - Use `radon.metrics.mi_visit()` for maintainability index
  - MI < 10: "error" (very hard to maintain)
  - MI 10-20: "warning" (moderate)
  - Include MI score in issue detail

### Afternoon: Code Smell Detection
- [ ] Implement `_check_code_smells()` with these detections:
  - **Long functions**: functions with > 50 lines -> "warning"
  - **Too many arguments**: functions with > 5 parameters -> "warning"
  - **Deep nesting**: nesting depth > 4 levels -> "warning"
  - **Large files**: files with > 300 lines -> "info"
  - **Too many return statements**: > 4 returns in a function -> "info"
  - Implementation approach:
    - Use Python's `ast` module to parse source code
    - Walk the AST to find FunctionDef nodes
    - Count arguments from `node.args`
    - Calculate nesting depth by tracking parent nodes
    - Count lines by checking `end_lineno - lineno`
- [ ] Implement `_calculate_score()`:
  - Start at 10.0
  - Deduct 1.5 per error
  - Deduct 0.5 per warning
  - Deduct 0.1 per info
  - Floor at 0.0
- [ ] Write `tests/test_analyzers/test_static.py`:
  - Test simple clean function (expect high score)
  - Test deeply nested function (expect nesting warning)
  - Test function with 10 parameters (expect too-many-args warning)
  - Test complex function with multiple branches (expect complexity warning)
  - Test maintainability index calculation

### Deliverables
- Static analyzer detecting complexity, maintainability, and code smells
- AST-based detection working for all code smell categories
- Unit tests passing

---

## Day 3 - Security Scanner

### Morning: Security Pattern Scanner
- [ ] Add to `requirements.txt`:
  ```
  bandit==1.7.6
  ```
- [ ] Create `app/analyzers/security_analyzer.py`:
  ```python
  class SecurityAnalyzer(BaseAnalyzer):
      name = "security"

      # Two-pronged approach:
      # 1. Run bandit for known vulnerability patterns
      # 2. Custom regex-based pattern matching for additional checks

      DANGEROUS_PATTERNS = {
          "hardcoded_password": {
              "pattern": r"(password|passwd|pwd|secret|api_key|apikey|token)\s*=\s*['\"][^'\"]+['\"]",
              "severity": "error",
              "message": "Potential hardcoded credential detected"
          },
          "sql_injection": {
              "pattern": r"(execute|cursor\.execute)\s*\(\s*['\"].*%[sd]",
              "severity": "error",
              "message": "Potential SQL injection - use parameterized queries"
          },
          "shell_injection": {
              "pattern": r"os\.system\s*\(|subprocess\.call\s*\(.*shell\s*=\s*True",
              "severity": "error",
              "message": "Potential shell injection vulnerability"
          },
          "eval_usage": {
              "pattern": r"\beval\s*\(|\bexec\s*\(",
              "severity": "error",
              "message": "Use of eval/exec is dangerous - avoid dynamic code execution"
          },
          "debug_flag": {
              "pattern": r"DEBUG\s*=\s*True|debug\s*=\s*True",
              "severity": "warning",
              "message": "Debug flag enabled - ensure this is not in production"
          },
          "insecure_hash": {
              "pattern": r"hashlib\.(md5|sha1)\s*\(",
              "severity": "warning",
              "message": "Weak hashing algorithm - use SHA-256 or bcrypt"
          },
          "pickle_usage": {
              "pattern": r"pickle\.loads?\s*\(",
              "severity": "warning",
              "message": "Pickle can execute arbitrary code - use JSON for untrusted data"
          },
          "http_url": {
              "pattern": r"http://(?!localhost|127\.0\.0\.1)",
              "severity": "info",
              "message": "Non-HTTPS URL detected - consider using HTTPS"
          }
      }
  ```

### Afternoon: Bandit Integration & Score Calculation
- [ ] Implement bandit integration:
  - Use `bandit.core.manager.BanditManager` programmatically
  - Or run bandit via subprocess with JSON output: `bandit -f json <file>`
  - Parse bandit results and convert to Issue objects
  - Map bandit severity/confidence to our severity levels:
    - HIGH severity: "error"
    - MEDIUM severity: "warning"
    - LOW severity: "info"
- [ ] Merge bandit issues with custom pattern issues (deduplicate)
- [ ] Implement security score calculation:
  - Start at 10.0
  - Deduct 2.0 per error (security errors are critical)
  - Deduct 0.8 per warning
  - Deduct 0.2 per info
  - Floor at 0.0
- [ ] Write `tests/test_analyzers/test_security.py`:
  - Test file with `eval()` usage (expect error)
  - Test file with hardcoded password (expect error)
  - Test file with `os.system()` (expect error)
  - Test file with `hashlib.md5()` (expect warning)
  - Test clean file with no security issues (expect high score)
  - Test SQL injection pattern detection

### Deliverables
- Security analyzer with bandit + custom regex patterns
- Covers: credentials, injection, dangerous functions, weak crypto
- All tests passing

---

## Day 4 - Integration, Edge Cases & Combined Testing

### Morning: Analyzer Integration
- [ ] Coordinate with **Member 1** to integrate analyzers into API endpoints
- [ ] Create a convenience function in `app/analyzers/__init__.py`:
  ```python
  from .lint_analyzer import LintAnalyzer
  from .static_analyzer import StaticAnalyzer
  from .security_analyzer import SecurityAnalyzer

  def get_all_analyzers():
      return [LintAnalyzer(), StaticAnalyzer(), SecurityAnalyzer()]

  def run_all_analyzers(files: dict[str, str]) -> list[AnalyzerResult]:
      results = []
      for analyzer in get_all_analyzers():
          try:
              result = analyzer.analyze_multiple(files)
              results.append(result)
          except Exception as e:
              results.append(AnalyzerResult(
                  analyzer_name=analyzer.name,
                  score=0.0,
                  issues=[],
                  summary=f"Analyzer failed: {str(e)}"
              ))
      return results
  ```
- [ ] Test the full analysis pipeline end-to-end using sample files

### Afternoon: Edge Cases & Robustness
- [ ] Handle edge cases across all analyzers:
  - Empty files (0 bytes)
  - Very large files (> 10,000 lines) - add timeout/limit
  - Binary files accidentally uploaded
  - Files with encoding issues (non-UTF-8)
  - Files with syntax errors (should still run security scan)
  - Files with only comments (no executable code)
- [ ] Add timeout mechanism for each analyzer (max 30 seconds per file)
- [ ] Review and fix any failing tests from integration
- [ ] Run full test suite: `pytest tests/ -v --cov=app/analyzers`

### Deliverables
- All three analyzers integrated and working through the API
- Edge cases handled gracefully
- Full test coverage on analyzers (aim for > 85%)

---

## Day 5 - Polish, Performance & Final Testing

### Morning: Scoring Calibration & Sample Files
- [ ] Create/refine sample files for demo:
  - `sample_files/clean_code.py`: Well-structured code with docstrings, type hints, proper naming
  - `sample_files/buggy_code.py`: Unused imports, long functions, deep nesting, no docstrings
  - `sample_files/insecure_code.py`: Hardcoded passwords, eval(), os.system(), SQL string formatting
- [ ] Run all analyzers against sample files and calibrate scoring:
  - clean_code.py should score 8-10
  - buggy_code.py should score 4-6
  - insecure_code.py should score 1-4
  - Adjust deduction weights if scores don't make sense
- [ ] Test with real open-source Python files from GitHub to verify realistic scoring

### Afternoon: Final Integration & Merge
- [ ] Coordinate with **Member 3** to verify analyzers work inside Docker
- [ ] Fix any issues found during Jenkins pipeline testing
- [ ] Final code review
- [ ] Merge `feature/analyzers` to `main`
- [ ] Document analyzer details in README (what each checks for, scoring weights)

### Deliverables
- All analyzers calibrated with realistic scoring
- Tests passing in Docker environment
- Documentation complete
- Merged to main

---
---

# MEMBER 3: DevOps, CI/CD & Infrastructure

**Role:** DevOps Engineer
**Branch:** `feature/devops-cicd`
**Focus:** Docker containerization, Jenkins pipeline, Makefile, testing infrastructure, deployment configuration, and CI/CD integration.

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
- [ ] Add deployment section to README:
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
---

# Cross-Team Coordination Schedule

| Day | Morning Sync | Afternoon Check-in |
|-----|-------------|-------------------|
| Day 1 | Agree on project structure & models | M1 pushes skeleton, M2 & M3 pull and start building on it |
| Day 2 | Review models/interfaces are compatible | M2 shares analyzer interface with M1 for endpoint integration |
| Day 3 | M1 & M2 coordinate analyzer integration | M3 shares Jenkinsfile with team for review |
| Day 4 | Full integration testing - all three branches | Bug fixes and edge case handling |
| Day 5 | Final testing in Docker + CI pipeline | Merge all branches, tag v1.0.0, demo prep |

# Key Integration Points

1. **M1 <-> M2 (Day 3-4):** Member 1 imports analyzers from `app/analyzers/` into API endpoints. The interface is `run_all_analyzers(files: dict[str, str]) -> list[AnalyzerResult]`. Both must agree on the `AnalyzerResult` and `Issue` Pydantic models.

2. **M1 <-> M3 (Day 4-5):** Member 3 needs the API to be stable to test Docker and Jenkins integration. Member 1 should have working endpoints by Day 3 afternoon.

3. **M2 <-> M3 (Day 4-5):** Member 3 needs analyzers to work inside Docker (all system deps must be in Dockerfile). Member 2 must communicate any system-level dependencies (e.g., `pylint`, `bandit` must be in `requirements.txt`).

# Definition of Done (Day 5 End)

- [ ] API accepts file upload and returns quality report
- [ ] API accepts GitHub URL and returns quality report
- [ ] Lint analyzer runs pylint and reports issues
- [ ] Static analyzer detects complexity and code smells
- [ ] Security scanner finds dangerous patterns
- [ ] Overall score calculated with weighted average
- [ ] Pass/fail based on configurable threshold
- [ ] Docker image builds and runs
- [ ] Jenkins pipeline builds, tests, and gates on quality
- [ ] All unit tests passing (> 80% coverage)
- [ ] Integration tests passing
- [ ] README with setup and usage instructions
- [ ] Sample files demonstrating pass/fail scenarios
