from .base import BaseAnalyzer
from app.models.report import AnalyzerResult, Issue
import re

class SecurityAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "security"

    DANGEROUS_PATTERNS = {
        "eval_usage": {
            "pattern": r"\beval\s*\(|\bexec\s*\(",
            "severity": "error",
            "message": "Use of eval/exec is dangerous"
        },
        "hardcoded_password": {
            "pattern": r"(password|passwd|pwd|secret|token)\s*=\s*['\"][^'\"]+['\"]",
            "severity": "error",
            "message": "Potential hardcoded credential detected"
        },
        "shell_injection": {
            "pattern": r"os\.system\s*\(|subprocess\.call\s*\(.*shell\s*=\s*True",
            "severity": "error",
            "message": "Potential shell injection vulnerability"
        }
    }

    def analyze(self, file_path: str, source_code: str = None) -> AnalyzerResult:
        if source_code is None:
            with open(file_path, "r") as f:
                source_code = f.read()

        lines = source_code.splitlines()
        issues = []
        
        for rule, data in self.DANGEROUS_PATTERNS.items():
            pattern = re.compile(data["pattern"])
            for match in pattern.finditer(source_code):
                # Calculate line number
                start_pos = match.start()
                line_no = source_code.count('\n', 0, start_pos) + 1
                col_no = start_pos - source_code.rfind('\n', 0, start_pos)
                
                line_content = lines[line_no-1] if 0 < line_no <= len(lines) else None
                
                issues.append(Issue(
                    severity=data["severity"],
                    message=data["message"],
                    file=file_path,
                    line=line_no,
                    column=col_no,
                    line_content=line_content.strip() if line_content else None,
                    rule=rule
                ))

        # Start at 10.0, deduct 2.0 per security error
        score = max(0.0, 10.0 - len(issues) * 2.0)
        
        return AnalyzerResult(
            analyzer_name=self.name,
            score=round(score, 2),
            issues=issues,
            summary=self._build_summary(issues, score)
        )
