import ast
from .base import BaseAnalyzer

class StaticAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("static")

    def analyze(self, file_path: str) -> dict:
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())
        
        
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                complexity += 1

        rating = "A" if complexity < 5 else "B" if complexity < 10 else "C"
        return {"complexity_score": complexity, "rating": rating}