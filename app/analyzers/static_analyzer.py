from .base import BaseAnalyzer
from app.models.report import AnalyzerResult, Issue
import ast

class StaticAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "static"

    def analyze(self, file_path: str, source_code: str = None) -> AnalyzerResult:
        if source_code is None:
            with open(file_path, "r") as f:
                source_code = f.read()
                
        lines = source_code.splitlines()
        tree = ast.parse(source_code)
        
        issues = []
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                complexity += 1
                lineno = getattr(node, 'lineno', None)
                line_content = lines[lineno-1] if lineno and 0 < lineno <= len(lines) else None
                
                if complexity > 10:
                    issues.append(Issue(
                        severity="error",
                        message=f"High cyclomatic complexity: {complexity}",
                        file=file_path,
                        line=lineno,
                        line_content=line_content,
                        rule="complexity"
                    ))
                elif complexity > 5:
                    issues.append(Issue(
                        severity="warning",
                        message=f"Moderate cyclomatic complexity: {complexity}",
                        file=file_path,
                        line=lineno,
                        line_content=line_content,
                        rule="complexity"
                    ))

        rating = "A" if complexity < 5 else "B" if complexity < 10 else "C"
        # Deduct from 10.0 scale
        score = max(0.0, 10.0 - (complexity - 1) * 0.5)

        return AnalyzerResult(
            analyzer_name=self.name,
            score=round(score, 2),
            issues=issues,
            summary=f"Complexity: {complexity} ({rating})"
        )

