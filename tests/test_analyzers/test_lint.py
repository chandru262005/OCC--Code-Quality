from app.analyzers.lint_analyzer import LintAnalyzer


def test_lint_buggy_code(tmp_path):
    # Setup: Create a temporary file with bad formatting
    bad_code = tmp_path / "bad_lint.py"
    bad_source = "x=1\ny = 2\n" + "z" * 100
    bad_code.write_text(bad_source)

    analyzer = LintAnalyzer()
    results = analyzer.analyze(str(bad_code))

    # Assertions
    assert len(results.issues) > 0
    # Check if specific error types (like E501 for line length) are caught
    rules = [i.rule for i in results.issues]
    assert any(r.startswith("E") for r in rules if r)


def test_lint_clean_code(tmp_path):
    clean_code = tmp_path / "clean_lint.py"
    clean_code.write_text("def my_function():\n    return True\n")

    analyzer = LintAnalyzer()
    results = analyzer.analyze(str(clean_code))

    # On 0-10 scale, clean code should be high
    assert results.score >= 9.0
    assert len(results.issues) == 0
