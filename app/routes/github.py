from fastapi import APIRouter, HTTPException
from app.models.request import GitHubAnalysisRequest
from app.services.github_handler import clone_repo, list_python_files, cleanup_repo
from app.analyzers import LintAnalyzer, StaticAnalyzer, SecurityAnalyzer
from app.services.report_builder import build_report
import logging

router = APIRouter(tags=["Analysis"])
logger = logging.getLogger(__name__)


@router.post("/analyze/github", summary="Analyze a GitHub repository")
async def analyze_github(request: GitHubAnalysisRequest):
    """
    Analyze a GitHub repository for code quality.

    Clones the repository, analyzes all Python files, and returns an
    aggregated quality report.
    """
    logger.info(f"Analyzing GitHub repo: {request.repo_url} (branch: {request.branch})")

    # Clone the repository
    repo_path = clone_repo(request.repo_url, request.branch)

    try:
        # List all Python files
        python_files = list_python_files(repo_path, request.file_extensions)

        if not python_files:
            raise HTTPException(
                status_code=404, detail="No Python files found in the repository"
            )

        logger.info(f"Found {len(python_files)} Python files to analyze")

        # Read all files
        files_content = {}
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    rel_path = str(file_path.relative_to(repo_path))
                    files_content[str(file_path)] = f.read()
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")

        # Run all analyzers across all files
        analyzers = [LintAnalyzer(), StaticAnalyzer(), SecurityAnalyzer()]
        analyzer_results = []

        for analyzer in analyzers:
            try:
                result = analyzer.analyze_multiple(files_content)
                analyzer_results.append(result)
            except Exception as e:
                logger.error(f"Analyzer {analyzer.name} failed: {str(e)}")
                from app.models.report import AnalyzerResult

                analyzer_results.append(
                    AnalyzerResult(
                        analyzer_name=analyzer.name,
                        score=0.0,
                        issues=[],
                        summary=f"Analyzer failed: {str(e)}",
                    )
                )

        # Build report
        report = build_report(
            analyzer_results=analyzer_results,
            source="github",
            files_analyzed=len(files_content),
            threshold=request.threshold,
        )

        logger.info(
            f"GitHub analysis complete: {request.repo_url} | "
            f"Files: {len(files_content)} | Score: {report.overall_score} | Passed: {report.passed}"
        )
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        cleanup_repo(repo_path)
