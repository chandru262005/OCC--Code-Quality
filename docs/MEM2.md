# Member 2: Analysis Engines

**Role:** Analysis Engine Developer
**Branch:** `feature/analyzers`
**Focus:** All three analysis engines (lint, static, security), the base analyzer interface, scoring logic, and analyzer unit tests.

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
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py           # Request schemas (Pydantic)       (Member 1)
│   │   └── report.py            # Report/response schemas          (Member 1, shared)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── upload.py            # File upload endpoints            (Member 1)
│   │   ├── github.py            # GitHub repo analysis endpoints   (Member 1)
│   │   ├── report.py            # Report retrieval endpoints       (Member 1)
│   │   └── health.py            # Health check endpoint            (Member 1)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_handler.py      # File upload & temp storage       (Member 1)
│   │   ├── github_handler.py    # Clone & manage GitHub repos      (Member 1)
│   │   └── report_builder.py    # Aggregate results into report    (Member 1)
│   └── analyzers/                                                  <<<< YOUR DOMAIN
│       ├── __init__.py          # Convenience imports & runner
│       ├── base.py              # Abstract base analyzer class
│       ├── lint_analyzer.py     # Pylint / Flake8 integration
│       ├── static_analyzer.py   # Complexity & code smell detection
│       └── security_analyzer.py # Security pattern scanner
├── tests/
│   └── test_analyzers/                                             <<<< YOUR TESTS
│       ├── __init__.py
│       ├── test_lint.py
│       ├── test_static.py
│       └── test_security.py
├── sample_files/                 # Sample code files for testing
│   ├── clean_code.py
│   ├── buggy_code.py
│   └── insecure_code.py
├── Dockerfile                                                      (Member 3)
├── docker-compose.yml                                              (Member 3)
├── Jenkinsfile                                                     (Member 3)
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── .flake8
├── pytest.ini
├── Makefile                                                        (Member 3)
└── README.md                                                       (Member 1)
```

---

## Git Workflow

- `main` branch: stable, protected
- Your feature branch: `feature/analyzers`
- Other members:
  - `feature/api-core` (Member 1)
  - `feature/devops-cicd` (Member 3)
- Pull requests to `main` with at least 1 review
- Merge conflicts resolved by the branch owner
- Commit messages follow: `type: short description` (e.g., `feat: add lint analyzer`)

---

## Your Files (Ownership)

You are responsible for creating and maintaining:

| File | Description |
|------|-------------|
| `app/analyzers/__init__.py` | Convenience imports, `get_all_analyzers()`, `run_all_analyzers()` |
| `app/analyzers/base.py` | Abstract base analyzer class |
| `app/analyzers/lint_analyzer.py` | Pylint-based lint analysis |
| `app/analyzers/static_analyzer.py` | Radon + AST-based static analysis |
| `app/analyzers/security_analyzer.py` | Bandit + regex-based security scanning |
| `tests/test_analyzers/__init__.py` | Package init |
| `tests/test_analyzers/test_lint.py` | Lint analyzer unit tests |
| `tests/test_analyzers/test_static.py` | Static analyzer unit tests |
| `tests/test_analyzers/test_security.py` | Security analyzer unit tests |
| `sample_files/clean_code.py` | Well-written sample (shared with M1) |
| `sample_files/buggy_code.py` | Buggy sample (shared with M1) |
| `sample_files/insecure_code.py` | Insecure sample (shared with M1) |

### Dependencies You Need in `requirements.txt`
Coordinate with Member 1 to add these to `requirements.txt`:
```
pylint==3.0.2
flake8==6.1.0
radon==6.0.1
bandit==1.7.6
```

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
- [ ] Add to `requirements.txt` (coordinate with Member 1):
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
- [ ] Add to `requirements.txt` (coordinate with Member 1):
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
- [ ] Add to `requirements.txt` (coordinate with Member 1):
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

## Integration Points (What You Need From Others)

### From Member 1 (Backend API) - Needed by Day 1 Morning
- Project skeleton with `app/` directory structure
- `app/models/report.py` with `AnalyzerResult` and `Issue` Pydantic models
- Your analyzers must return data matching these schemas exactly

### From Member 3 (DevOps) - Needed by Day 4
- Working `Dockerfile` that installs `pylint`, `flake8`, `radon`, `bandit` (via `requirements.txt`)
- Confirmation that all analyzer dependencies work inside the Docker container

### What You Provide to Others
- **To Member 1 (Day 2 afternoon):** Analyzer interface contract: `run_all_analyzers(files: dict[str, str]) -> list[AnalyzerResult]`
- **To Member 1 (Day 4 morning):** Working analyzers ready for API integration
- **To Member 3 (Day 1):** List of system/pip dependencies needed in Dockerfile

---

## Coordination Schedule

| Day | Morning Sync | Afternoon Check-in |
|-----|-------------|-------------------|
| Day 1 | Pull M1's skeleton, agree on `AnalyzerResult` model | Share base analyzer interface with M1 |
| Day 2 | Confirm models are compatible | Share analyzer contract with M1 for endpoint planning |
| Day 3 | Discuss integration approach with M1 | Share dependency list with M3 for Dockerfile |
| Day 4 | Hand off analyzers to M1 for integration | Full integration testing with all three members |
| Day 5 | Calibrate scoring with sample files | Merge to main, verify in Docker, demo prep |

---

## Analyzer Architecture Reference

```
┌─────────────────────────────────────────────────┐
│                  BaseAnalyzer                    │
│  ┌───────────────────────────────────────────┐   │
│  │  analyze(file_path, source_code)          │   │
│  │  analyze_multiple(files: dict)            │   │
│  │  _build_summary(issues, score)            │   │
│  └───────────────────────────────────────────┘   │
└──────────┬──────────────┬──────────────┬─────────┘
           │              │              │
    ┌──────▼──────┐ ┌─────▼──────┐ ┌────▼───────┐
    │ LintAnalyzer│ │  Static    │ │  Security  │
    │             │ │  Analyzer  │ │  Analyzer  │
    │ - pylint    │ │ - radon    │ │ - bandit   │
    │ - flake8    │ │ - ast      │ │ - regex    │
    │             │ │            │ │            │
    │ Score: 0-10 │ │ Score: 0-10│ │ Score: 0-10│
    │ (pylint     │ │ (deduction │ │ (deduction │
    │  native)    │ │  based)    │ │  based)    │
    └─────────────┘ └────────────┘ └────────────┘

    Weight: 40%       Weight: 35%    Weight: 25%
```

### Scoring Summary

| Analyzer | Method | Error Deduction | Warning Deduction | Info Deduction |
|----------|--------|-----------------|-------------------|----------------|
| Lint | Pylint native score (0-10) | N/A (built-in) | N/A (built-in) | N/A (built-in) |
| Static | Start at 10, deduct | -1.5 | -0.5 | -0.1 |
| Security | Start at 10, deduct | -2.0 | -0.8 | -0.2 |
