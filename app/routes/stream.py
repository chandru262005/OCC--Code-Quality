"""
SSE streaming endpoints that emit step-by-step progress events
so the frontend can show a live pipeline (like GitHub Actions).

Event types sent over the stream:
  step   – a pipeline step changed status (pending / running / completed / failed)
  result – the final quality report (same shape as the non-streaming endpoints)
  error  – an unrecoverable error
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.models.request import GitHubAnalysisRequest
from app.models.report import AnalyzerResult
from app.services.file_handler import save_upload, cleanup_upload, validate_file
from app.services.github_handler import clone_repo, list_python_files, cleanup_repo
from app.analyzers import LintAnalyzer, StaticAnalyzer, SecurityAnalyzer
from app.services.report_builder import build_report
import json
import time
import logging
import asyncio

router = APIRouter(tags=["Streaming Analysis"])
logger = logging.getLogger(__name__)


def _sse(event: str, data: dict) -> str:
    """Format a single SSE frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _step_event(step_id: str, status: str, message: str, duration_ms: int = 0) -> str:
    return _sse(
        "step",
        {
            "step": step_id,
            "status": status,
            "message": message,
            "duration_ms": duration_ms,
        },
    )


# ── File upload streaming endpoint ──────────────────────────────────────────


@router.post("/analyze/file/stream", summary="Analyze file with live progress")
async def analyze_file_stream(
    file: UploadFile = File(...),
    threshold: float = Form(6.0),
):
    async def generate():
        file_path = None
        try:
            # Step 1 – validate
            t0 = time.time()
            yield _step_event("validate", "running", f"Validating {file.filename}...")
            await asyncio.sleep(0)  # flush
            validate_file(file)
            yield _step_event(
                "validate",
                "completed",
                f"File accepted: {file.filename}",
                int((time.time() - t0) * 1000),
            )

            # Step 2 – save
            t0 = time.time()
            yield _step_event("save", "running", "Saving upload to workspace...")
            await asyncio.sleep(0)
            file_path = save_upload(file)
            yield _step_event(
                "save", "completed", "Upload saved", int((time.time() - t0) * 1000)
            )

            # Step 3 – read
            t0 = time.time()
            yield _step_event("read", "running", "Reading source code...")
            await asyncio.sleep(0)
            with open(file_path, "r") as f:
                source_code = f.read()
            line_count = len(source_code.splitlines())
            yield _step_event(
                "read",
                "completed",
                f"Read {line_count} lines",
                int((time.time() - t0) * 1000),
            )

            # Steps 4-6 – analyzers
            analyzers = [
                ("lint", "Lint Analysis", "Running Flake8 linter...", LintAnalyzer()),
                (
                    "static",
                    "Static Analysis",
                    "Running complexity & AST checks...",
                    StaticAnalyzer(),
                ),
                (
                    "security",
                    "Security Scan",
                    "Scanning for vulnerability patterns...",
                    SecurityAnalyzer(),
                ),
            ]
            analyzer_results: list[AnalyzerResult] = []

            for step_id, label, msg, analyzer in analyzers:
                t0 = time.time()
                yield _step_event(step_id, "running", msg)
                await asyncio.sleep(0)
                try:
                    result = analyzer.analyze(str(file_path), source_code)
                    analyzer_results.append(result)
                    issue_count = len(result.issues)
                    yield _step_event(
                        step_id,
                        "completed",
                        f"{label}: {result.score}/10 — {issue_count} issue{'s' if issue_count != 1 else ''}",
                        int((time.time() - t0) * 1000),
                    )
                except Exception as exc:
                    logger.error(f"{label} failed: {exc}")
                    analyzer_results.append(
                        AnalyzerResult(
                            analyzer_name=analyzer.name,
                            score=0.0,
                            issues=[],
                            summary=f"Failed: {exc}",
                        )
                    )
                    yield _step_event(
                        step_id,
                        "failed",
                        f"{label} failed: {exc}",
                        int((time.time() - t0) * 1000),
                    )

            # Step 7 – build report
            t0 = time.time()
            yield _step_event(
                "report", "running", "Aggregating scores & building report..."
            )
            await asyncio.sleep(0)
            report = build_report(
                analyzer_results=analyzer_results,
                source="upload",
                files_analyzed=1,
                threshold=threshold,
            )
            status_label = "PASSED" if report.passed else "FAILED"
            yield _step_event(
                "report",
                "completed",
                f"Quality Gate {status_label} — Score {report.overall_score}/10",
                int((time.time() - t0) * 1000),
            )

            # Final result
            yield _sse("result", report.model_dump())

        except HTTPException as he:
            yield _sse("error", {"message": he.detail})
        except Exception as exc:
            logger.error(f"Stream analysis failed: {exc}")
            yield _sse("error", {"message": str(exc)})
        finally:
            if file_path:
                cleanup_upload(file_path)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── GitHub repo streaming endpoint ──────────────────────────────────────────


@router.post("/analyze/github/stream", summary="Analyze GitHub repo with live progress")
async def analyze_github_stream(request: GitHubAnalysisRequest):
    async def generate():
        repo_path = None
        try:
            # Step 1 – validate URL
            t0 = time.time()
            yield _step_event(
                "validate", "running", f"Validating URL: {request.repo_url}..."
            )
            await asyncio.sleep(0)
            # clone_repo validates internally; we just surface it here
            yield _step_event(
                "validate", "completed", "URL accepted", int((time.time() - t0) * 1000)
            )

            # Step 2 – clone
            t0 = time.time()
            yield _step_event(
                "clone", "running", f"Cloning repository (branch: {request.branch})..."
            )
            await asyncio.sleep(0)
            repo_path = clone_repo(request.repo_url, request.branch)
            yield _step_event(
                "clone",
                "completed",
                "Repository cloned",
                int((time.time() - t0) * 1000),
            )

            # Step 3 – discover files
            t0 = time.time()
            yield _step_event("discover", "running", "Discovering Python files...")
            await asyncio.sleep(0)
            python_files = list_python_files(repo_path, request.file_extensions)
            if not python_files:
                yield _step_event(
                    "discover",
                    "failed",
                    "No Python files found in repository",
                    int((time.time() - t0) * 1000),
                )
                yield _sse(
                    "error", {"message": "No Python files found in the repository"}
                )
                return
            yield _step_event(
                "discover",
                "completed",
                f"Found {len(python_files)} Python file{'s' if len(python_files) != 1 else ''}",
                int((time.time() - t0) * 1000),
            )

            # Step 4 – read all files
            t0 = time.time()
            yield _step_event(
                "read", "running", f"Reading {len(python_files)} files..."
            )
            await asyncio.sleep(0)
            files_content = {}
            for fp in python_files:
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        files_content[str(fp)] = f.read()
                except Exception as exc:
                    logger.warning(f"Could not read {fp}: {exc}")
            total_lines = sum(c.count("\n") + 1 for c in files_content.values())
            yield _step_event(
                "read",
                "completed",
                f"Read {len(files_content)} files ({total_lines} lines total)",
                int((time.time() - t0) * 1000),
            )

            # Steps 5-7 – analyzers
            analyzers = [
                (
                    "lint",
                    "Lint Analysis",
                    "Running Flake8 across all files...",
                    LintAnalyzer(),
                ),
                (
                    "static",
                    "Static Analysis",
                    "Computing complexity & code smells...",
                    StaticAnalyzer(),
                ),
                (
                    "security",
                    "Security Scan",
                    "Scanning all files for vulnerabilities...",
                    SecurityAnalyzer(),
                ),
            ]
            analyzer_results: list[AnalyzerResult] = []

            for step_id, label, msg, analyzer in analyzers:
                t0 = time.time()
                yield _step_event(step_id, "running", msg)
                await asyncio.sleep(0)
                try:
                    result = analyzer.analyze_multiple(files_content)
                    analyzer_results.append(result)
                    issue_count = len(result.issues)
                    yield _step_event(
                        step_id,
                        "completed",
                        f"{label}: {result.score}/10 — {issue_count} issue{'s' if issue_count != 1 else ''}",
                        int((time.time() - t0) * 1000),
                    )
                except Exception as exc:
                    logger.error(f"{label} failed: {exc}")
                    analyzer_results.append(
                        AnalyzerResult(
                            analyzer_name=analyzer.name,
                            score=0.0,
                            issues=[],
                            summary=f"Failed: {exc}",
                        )
                    )
                    yield _step_event(
                        step_id,
                        "failed",
                        f"{label} failed: {exc}",
                        int((time.time() - t0) * 1000),
                    )

            # Step 8 – build report
            t0 = time.time()
            yield _step_event(
                "report", "running", "Aggregating scores & building report..."
            )
            await asyncio.sleep(0)
            report = build_report(
                analyzer_results=analyzer_results,
                source="github",
                files_analyzed=len(files_content),
                threshold=request.threshold,
            )
            status_label = "PASSED" if report.passed else "FAILED"
            yield _step_event(
                "report",
                "completed",
                f"Quality Gate {status_label} — Score {report.overall_score}/10",
                int((time.time() - t0) * 1000),
            )

            # Final result
            yield _sse("result", report.model_dump())

        except HTTPException as he:
            yield _sse("error", {"message": he.detail})
        except Exception as exc:
            logger.error(f"Stream GitHub analysis failed: {exc}")
            yield _sse("error", {"message": str(exc)})
        finally:
            if repo_path:
                cleanup_repo(repo_path)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
