from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from starlette.concurrency import run_in_threadpool
from app.services.file_handler import save_upload, cleanup_upload, validate_file
from app.services.orchestrator import AnalysisService
import logging

router = APIRouter(tags=["Analysis"])
logger = logging.getLogger(__name__)


@router.post("/analyze/file", summary="Analyze an uploaded file")
async def analyze_file(
    file: UploadFile = File(..., description="Source code file to analyze"),
    threshold: float = Form(6.0, description="Quality threshold (0-10)"),
    ai_model: str | None = Form(None, description="Optional AI model override"),
):
    """
    Upload a source code file for quality analysis.

    Returns a quality report with lint, static analysis, and security scan results.
    The report includes an overall score and pass/fail status based on the threshold.
    """
    # Validate file
    await run_in_threadpool(validate_file, file)

    # Save to temp
    file_path = await run_in_threadpool(save_upload, file)

    try:
        # Run orchestrator
        report = await run_in_threadpool(
            AnalysisService.process_file_analysis,
            file_path,
            file.filename or "unknown",
            threshold,
            ai_model,
        )
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        await run_in_threadpool(cleanup_upload, file_path)
