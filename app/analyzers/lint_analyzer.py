import subprocess
from .base import BaseAnalyzer

class LintAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("lint")

    def analyze(self, file_path: str) -> dict:
        # Run flake8 as a subprocess
        result = subprocess.run(
            ['flake8', file_path, '--format=%(code)s:%(text)s'], 
            capture_output=True, text=True
        )
        
        violations = []
        for line in result.stdout.splitlines():
            if ":" in line:
                code, text = line.split(":", 1)
                violations.append({"code": code, "message": text})

        score = max(0, 100 - len(violations) * 5)
        return {"score": score, "violations": violations}