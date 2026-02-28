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
    def analyze(self, file_path: str, source_code: str = None) -> AnalyzerResult:
        """
        Analyze a single file and return results.
        """
        pass

    def analyze_multiple(self, files: dict[str, str]) -> AnalyzerResult:
        """
        Analyze multiple files and aggregate results.
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
