import pytest
from app.analyzers.lint_analyzer import LintAnalyzer

def test_lint_buggy_code(tmp_path):
    # Setup: Create a temporary file with bad formatting (e.g., long line, no spaces)
    bad_code = tmp_path / "bad_lint.py"
    bad_code.write_text("x=1\ny = 2\n" + "z" * 100) # Line too long, missing spaces

    analyzer = LintAnalyzer()
    results = analyzer.analyze(str(bad_code))

    # Assertions
    assert "violations" in results
    assert len(results["violations"]) > 0
    # Check if specific error types (like E501 for line length) are caught
    codes = [v['code'] for v in results["violations"]]
    assert any(c.startswith('E') for c in codes)

def test_lint_clean_code(tmp_path):
    clean_code = tmp_path / "clean_lint.py"
    clean_code.write_text("def my_function():\n    return True\n")

    analyzer = LintAnalyzer()
    results = analyzer.analyze(str(clean_code))
    
    assert results["score"] > 90
    assert len(results["violations"]) == 0