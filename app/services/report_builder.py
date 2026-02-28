import uuid
from datetime import datetime, timezone
from app.models.report import AnalyzerResult, QualityReport

# Analyzer weights for overall score calculation
ANALYZER_WEIGHTS = {
    "lint": 0.40,
    "static": 0.35,
    "security": 0.25,
}


def build_report(
    analyzer_results: list[AnalyzerResult],
    source: str,
    files_analyzed: int,
    threshold: float = 6.0,
) -> QualityReport:
    """
    Aggregate analyzer results into a final quality report.

    Args:
        analyzer_results: List of results from each analyzer
        source: "upload" or "github"
        files_analyzed: Number of files analyzed
        threshold: Minimum passing score (0-10)

    Returns:
        QualityReport with overall score, pass/fail, and all details
    """
    # Calculate weighted overall score
    overall_score = _calculate_overall_score(analyzer_results)

    # Determine pass/fail
    passed = overall_score >= threshold

    # Generate summary
    summary = _generate_summary(analyzer_results, overall_score, threshold, passed)

    return QualityReport(
        report_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        source=source,
        files_analyzed=files_analyzed,
        overall_score=round(overall_score, 2),
        threshold=threshold,
        passed=passed,
        results=analyzer_results,
        summary=summary,
    )


def _calculate_overall_score(results: list[AnalyzerResult]) -> float:
    """Calculate weighted average score from all analyzers."""
    if not results:
        return 0.0

    weighted_sum = 0.0
    total_weight = 0.0

    for result in results:
        weight = ANALYZER_WEIGHTS.get(result.analyzer_name, 0.0)
        weighted_sum += result.score * weight
        total_weight += weight

    if total_weight == 0:
        # Fallback: simple average if analyzer names don't match known weights
        return sum(r.score for r in results) / len(results)

    return weighted_sum / total_weight


def _generate_summary(
    results: list[AnalyzerResult],
    overall_score: float,
    threshold: float,
    passed: bool,
) -> str:
    """Generate a human-readable summary of the analysis."""
    status = "PASSED" if passed else "FAILED"
    parts = [
        f"Quality Gate {status} | Overall Score: {overall_score:.1f}/10 (threshold: {threshold})"
    ]

    total_issues = sum(len(r.issues) for r in results)
    total_errors = sum(1 for r in results for i in r.issues if i.severity == "error")
    total_warnings = sum(
        1 for r in results for i in r.issues if i.severity == "warning"
    )

    parts.append(
        f"Total issues: {total_issues} ({total_errors} errors, {total_warnings} warnings)"
    )

    for result in results:
        parts.append(f"  - {result.analyzer_name}: {result.score:.1f}/10")

    return " | ".join(parts)
