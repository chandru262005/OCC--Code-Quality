import logging
from typing import Dict, List
from pathlib import Path
from fastapi import HTTPException

from app.models.report import AnalyzerResult, QualityReport
from app.analyzers import LintAnalyzer, StaticAnalyzer, SecurityAnalyzer
from app.services.report_builder import build_report

logger = logging.getLogger(__name__)


class AnalysisService:
    @staticmethod
    def get_analyzers():
        return [
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

    @staticmethod
    def run_analyzers_single_file(
        file_path: str, source_code: str
    ) -> List[AnalyzerResult]:
        """Run all analyzers on a single file synchronously."""
        analyzers = [LintAnalyzer(), StaticAnalyzer(), SecurityAnalyzer()]
        analyzer_results = []
        for analyzer in analyzers:
            try:
                result = analyzer.analyze(file_path, source_code)
                analyzer_results.append(result)
            except Exception as e:
                logger.error(f"Analyzer {analyzer.name} failed: {str(e)}")
                analyzer_results.append(
                    AnalyzerResult(
                        analyzer_name=analyzer.name,
                        score=0.0,
                        issues=[],
                        summary=f"Analyzer failed: {str(e)}",
                    )
                )
        return analyzer_results

    @staticmethod
    def run_analyzers_multiple_files(
        files_content: Dict[str, str],
    ) -> List[AnalyzerResult]:
        """Run all analyzers on multiple files synchronously."""
        analyzers = [LintAnalyzer(), StaticAnalyzer(), SecurityAnalyzer()]
        analyzer_results = []
        for analyzer in analyzers:
            try:
                result = analyzer.analyze_multiple(files_content)
                analyzer_results.append(result)
            except Exception as e:
                logger.error(f"Analyzer {analyzer.name} failed: {str(e)}")
                analyzer_results.append(
                    AnalyzerResult(
                        analyzer_name=analyzer.name,
                        score=0.0,
                        issues=[],
                        summary=f"Analyzer failed: {str(e)}",
                    )
                )
        return analyzer_results

    @staticmethod
    def process_file_analysis(
        file_path: Path, filename: str, threshold: float
    ) -> QualityReport:
        """Process a single file analysis end-to-end synchronously."""
        logger.info(f"Analyzing uploaded file: {filename}")
        try:
            with open(file_path, "r") as f:
                source_code = f.read()

            analyzer_results = AnalysisService.run_analyzers_single_file(
                str(file_path), source_code
            )

            report = build_report(
                analyzer_results=analyzer_results,
                source="upload",
                files_analyzed=1,
                threshold=threshold,
            )

            logger.info(
                f"Analysis complete: {filename} | "
                f"Score: {report.overall_score} | Passed: {report.passed}"
            )
            return report
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    @staticmethod
    def process_github_analysis(
        repo_url: str, branch: str, python_files: List[Path], threshold: float
    ) -> QualityReport:
        """Process a github analysis end-to-end synchronously, assuming files are listed."""
        logger.info(f"Found {len(python_files)} Python files to analyze")
        try:
            files_content = {}
            for file_path in python_files:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        files_content[str(file_path)] = f.read()
                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {e}")

            analyzer_results = AnalysisService.run_analyzers_multiple_files(
                files_content
            )

            report = build_report(
                analyzer_results=analyzer_results,
                source="github",
                files_analyzed=len(files_content),
                threshold=threshold,
            )

            logger.info(
                f"GitHub analysis complete: {repo_url} | "
                f"Files: {len(files_content)} | Score: {report.overall_score} | Passed: {report.passed}"
            )
            return report
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"GitHub analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
