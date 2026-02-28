from .base import BaseAnalyzer
from .static_analyzer import StaticAnalyzer
from .lint_analyzer import LintAnalyzer
from .security_analyzer import SecurityAnalyzer
from app.models.report import AnalyzerResult


def get_all_analyzers() -> list[BaseAnalyzer]:
    """Return instances of all available analyzers."""
    return [LintAnalyzer(), StaticAnalyzer(), SecurityAnalyzer()]


def run_all_analyzers(files: dict[str, str]) -> list[AnalyzerResult]:
    """
    Run all analyzers on multiple files.

    Args:
        files: dict mapping file_path -> source_code

    Returns:
        List of AnalyzerResult, one per analyzer
    """
    results = []
    for analyzer in get_all_analyzers():
        try:
            result = analyzer.analyze_multiple(files)
            results.append(result)
        except Exception as e:
            results.append(
                AnalyzerResult(
                    analyzer_name=analyzer.name,
                    score=0.0,
                    issues=[],
                    summary=f"Analyzer failed: {str(e)}",
                )
            )
    return results
