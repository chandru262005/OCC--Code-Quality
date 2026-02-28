from .base import BaseAnalyzer
from app.models.report import AnalyzerResult, Issue
import subprocess
import os

class LintAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "lint"

    def analyze(self, file_path: str, source_code: str = None) -> AnalyzerResult:
        if source_code is None:
            with open(file_path, "r") as f:
                source_code = f.read()

        lines = source_code.splitlines()
        
        import sys
        # Try to find flake8 in the same directory as the python executable
        base_dir = os.path.dirname(sys.executable)
        flake8_bin = os.path.join(base_dir, 'flake8')
        if os.name == 'nt' and not flake8_bin.endswith('.exe'):
            flake8_bin += '.exe'
        
        # Fallback to simple 'flake8' if venv one isn't found
        cmd = flake8_bin if os.path.exists(flake8_bin) else 'flake8'
        
        result = subprocess.run(
            [cmd, file_path, '--format=%(row)d:%(col)d:%(code)s:%(text)s'], 
            capture_output=True, text=True
        )

        
        issues = []
        for output_line in result.stdout.splitlines():
            parts = output_line.split(":", 3)
            if len(parts) == 4:
                row, col, code, text = parts
                row_idx = int(row) - 1
                line_content = lines[row_idx] if 0 <= row_idx < len(lines) else None
                
                severity = "error" if any(code.startswith(p) for p in ['E', 'F']) else "warning"
                issues.append(Issue(
                    severity=severity,
                    message=text.strip(),
                    file=file_path,
                    line=int(row),
                    column=int(col),
                    line_content=line_content,
                    rule=code
                ))

        # Score on 0-10 scale (start at 10, deduct 0.5 per issue)
        score = max(0.0, 10.0 - len(issues) * 0.5)
        
        return AnalyzerResult(
            analyzer_name=self.name,
            score=round(score, 2),
            issues=issues,
            summary=self._build_summary(issues, score)
        )

