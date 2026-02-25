# Member 1: Backend API & Core Architecture

**Role:** API Developer & Project Architect
**Branch:** `feature/api-core`
**Focus:** FastAPI application, endpoints, request/response models, file handling, GitHub integration, report builder, and project scaffolding.

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
- Your feature branch: `feature/api-core`
- Other members:
  - `feature/analyzers` (Member 2)
  - `feature/devops-cicd` (Member 3)
- Pull requests to `main` with at least 1 review
- Merge conflicts resolved by the branch owner
- Commit messages follow: `type: short description` (e.g., `feat: add upload endpoint`)

---

## Your Files (Ownership)

You are responsible for creating and maintaining:

| File | Description |
|------|-------------|
| `app/__init__.py` | Package init |
| `app/main.py` | FastAPI app entry point, CORS, routers |
| `app/config.py` | App settings via Pydantic BaseSettings |
| `app/models/__init__.py` | Package init |
| `app/models/request.py` | Request schemas |
| `app/models/report.py` | Report/response schemas (shared with M2) |
| `app/routes/__init__.py` | Package init |
| `app/routes/health.py` | Health check endpoint |
| `app/routes/upload.py` | File upload analysis endpoint |
| `app/routes/github.py` | GitHub repo analysis endpoint |
| `app/routes/report.py` | Report retrieval endpoint |
| `app/services/__init__.py` | Package init |
| `app/services/file_handler.py` | File upload & temp storage |
| `app/services/github_handler.py` | Clone & manage GitHub repos |
| `app/services/report_builder.py` | Aggregate results into final report |
| `requirements.txt` | Core dependencies |
| `requirements-dev.txt` | Dev/test dependencies |
| `.gitignore` | Git ignore rules |
| `README.md` | Project documentation |
| `sample_files/*.py` | Sample test files for demo |

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

## Integration Points (What You Need From Others)

### From Member 2 (Analysis Engines) - Needed by Day 4 Morning
- `app/analyzers/__init__.py` exposing `run_all_analyzers(files: dict[str, str]) -> list[AnalyzerResult]`
- All analyzer classes inheriting from `BaseAnalyzer`
- Analyzers must return data matching the `AnalyzerResult` and `Issue` Pydantic models you define in `app/models/report.py`

### From Member 3 (DevOps) - Needed by Day 4 Afternoon
- Working `Dockerfile` that can run the API
- `docker-compose.yml` for local testing
- Feedback on any API issues found during Docker/Jenkins testing

### What You Provide to Others
- **To Member 2 (Day 1):** Project skeleton, `app/models/report.py` with `AnalyzerResult` and `Issue` schemas
- **To Member 3 (Day 3):** Stable API with working endpoints for Docker/Jenkins integration

---

## Coordination Schedule

| Day | Morning Sync | Afternoon Check-in |
|-----|-------------|-------------------|
| Day 1 | Agree on project structure & models with team | Push skeleton so M2 & M3 can start building on it |
| Day 2 | Confirm models/interfaces are compatible with M2 | Share endpoint contracts with M3 |
| Day 3 | Review analyzer interface with M2 | Ensure endpoints work for M3's Jenkins integration |
| Day 4 | Integrate real analyzers from M2 | Full integration testing with M3's Docker setup |
| Day 5 | Final testing in Docker + CI pipeline | Merge to main, tag v1.0.0, demo prep |
