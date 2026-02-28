from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool
from app.models.request import GitHubAnalysisRequest
from app.services.github_handler import clone_repo, list_python_files, cleanup_repo
from app.services.orchestrator import AnalysisService
import logging

router = APIRouter(tags=["Analysis"])
logger = logging.getLogger(__name__)


@router.post("/analyze/github", summary="Analyze a GitHub repository")
async def analyze_github(request: GitHubAnalysisRequest):
    """
    Analyze a GitHub repository for code quality.

    Clones the repository, analyzes all matching source files, and returns an
    aggregated quality report.
    """
    logger.info(f"Analyzing GitHub repo: {request.repo_url} (branch: {request.branch})")

    # Clone the repository
    repo_path = await run_in_threadpool(clone_repo, request.repo_url, request.branch)

    try:
        # List all matching source files
        source_files = await run_in_threadpool(
            list_python_files, repo_path, request.file_extensions
        )

        if not source_files:
            raise HTTPException(
                status_code=404,
                detail="No files found in the repository for the selected extensions",
            )

        # Run orchestrator
        report = await run_in_threadpool(
            AnalysisService.process_github_analysis,
            request.repo_url,
            request.branch,
            source_files,
            request.threshold,
            request.ai_model,
        )
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        await run_in_threadpool(cleanup_repo, repo_path)
