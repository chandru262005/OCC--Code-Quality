import ast
from .base import BaseAnalyzer

class SecurityAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("security")

    def analyze(self, file_path: str) -> dict:
        with open(file_path, "r") as f:
            content = f.read()
            tree = ast.parse(content)

        issues = []
        danger_calls = ['eval', 'exec', 'system']

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, 'id', '') in danger_calls:
                issues.append({"type": f"{node.func.id}_use", "severity": "HIGH"})

        return {
            "vulnerabilities_found": len(issues) > 0,
            "issues": issues,
            "security_level": "SECURE" if not issues else "CRITICAL"
        }