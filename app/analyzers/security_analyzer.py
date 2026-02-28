from .base import BaseAnalyzer
from app.models.report import AnalyzerResult, Issue
import re


class SecurityAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "security"

    DANGEROUS_PATTERNS = {
        "hardcoded_password": {
            "pattern": r"(password|passwd|pwd|secret|api_key|apikey|token)\s*=\s*['\"][^'\"]+['\"]",
            "severity": "error",
            "message": "Potential hardcoded credential detected",
        },
        "sql_injection": {
            "pattern": r"(execute|cursor\.execute)\s*\(\s*['\"].*%[sd]",
            "severity": "error",
            "message": "Potential SQL injection - use parameterized queries",
        },
        "shell_injection": {
            "pattern": r"os\.system\s*\(|subprocess\.call\s*\(.*shell\s*=\s*True",
            "severity": "error",
            "message": "Potential shell injection vulnerability",
        },
        "eval_usage": {
            "pattern": r"\beval\s*\(|\bexec\s*\(",
            "severity": "error",
            "message": "Use of eval/exec is dangerous - avoid dynamic code execution",
        },
        "debug_flag": {
            "pattern": r"DEBUG\s*=\s*True|debug\s*=\s*True",
            "severity": "warning",
            "message": "Debug flag enabled - ensure this is not in production",
        },
        "insecure_hash": {
            "pattern": r"hashlib\.(md5|sha1)\s*\(",
            "severity": "warning",
            "message": "Weak hashing algorithm - use SHA-256 or bcrypt",
        },
        "pickle_usage": {
            "pattern": r"pickle\.loads?\s*\(",
            "severity": "warning",
            "message": "Pickle can execute arbitrary code - use JSON for untrusted data",
        },
        "http_url": {
            "pattern": r"http://(?!localhost|127\.0\.0\.1)",
            "severity": "info",
            "message": "Non-HTTPS URL detected - consider using HTTPS",
        },
    }

    def analyze(self, file_path: str, source_code: str = None) -> AnalyzerResult:
        if source_code is None:
            with open(file_path, "r") as f:
                source_code = f.read()

        lines = source_code.splitlines()
        issues = []

        for rule_name, data in self.DANGEROUS_PATTERNS.items():
            pattern = re.compile(data["pattern"])
            for match in pattern.finditer(source_code):
                start_pos = match.start()
                line_no = source_code.count("\n", 0, start_pos) + 1
                col_no = start_pos - source_code.rfind("\n", 0, start_pos)

                line_content = lines[line_no - 1] if 0 < line_no <= len(lines) else None

                issues.append(
                    Issue(
                        severity=data["severity"],
                        message=data["message"],
                        file=file_path,
                        line=line_no,
                        column=col_no,
                        line_content=line_content.strip() if line_content else None,
                        rule=rule_name,
                    )
                )

        # Start at 10.0, deduct based on severity
        score = 10.0
        for issue in issues:
            if issue.severity == "error":
                score -= 2.0
            elif issue.severity == "warning":
                score -= 0.8
            elif issue.severity == "info":
                score -= 0.2
        score = max(0.0, score)

        return AnalyzerResult(
            analyzer_name=self.name,
            score=round(score, 2),
            issues=issues,
            summary=self._build_summary(issues, score),
        )
