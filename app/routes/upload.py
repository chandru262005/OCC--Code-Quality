from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.file_handler import save_upload, cleanup_upload, validate_file
from app.analyzers import LintAnalyzer, StaticAnalyzer, SecurityAnalyzer
from app.services.report_builder import build_report
import logging

router = APIRouter(tags=["Analysis"])
logger = logging.getLogger(__name__)


@router.post("/analyze/file", summary="Analyze an uploaded file")
async def analyze_file(
    file: UploadFile = File(..., description="Python file to analyze"),
    threshold: float = Form(6.0, description="Quality threshold (0-10)"),
):
    """
    Upload a Python file for quality analysis.

    Returns a quality report with lint, static analysis, and security scan results.
    The report includes an overall score and pass/fail status based on the threshold.
    """
    # Validate file
    validate_file(file)

    # Save to temp
    file_path = save_upload(file)
    logger.info(f"Analyzing uploaded file: {file.filename}")

    try:
        # Read source code
        with open(file_path, "r") as f:
            source_code = f.read()

        # Run all analyzers
        analyzers = [LintAnalyzer(), StaticAnalyzer(), SecurityAnalyzer()]
        analyzer_results = []

        for analyzer in analyzers:
            try:
                result = analyzer.analyze(str(file_path), source_code)
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
            source="upload",
            files_analyzed=1,
            threshold=threshold,
        )

        logger.info(
            f"Analysis complete: {file.filename} | "
            f"Score: {report.overall_score} | Passed: {report.passed}"
        )
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        cleanup_upload(file_path)
