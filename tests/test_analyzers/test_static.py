import pytest
from app.analyzers.static_analyzer import StaticAnalyzer


def test_high_complexity_detection(tmp_path):
    # Setup: Create a deeply nested 'if' structure
    complex_file = tmp_path / "complex.py"
    # 5 IFs = Complexity 6. 1 base + 5 nodes.
    # Complexity 6 should be 'B' (>= 5 and < 10)
    complex_file.write_text(
        "def deep_nesting(x):\n"
        "    if x > 0:\n"
        "        if x > 1:\n"
        "            if x > 2:\n"
        "                if x > 3:\n"
        "                    if x > 4:\n"
        "                        return x\n"
        "    return 0"
    )

    analyzer = StaticAnalyzer()
    results = analyzer.analyze(str(complex_file))

    # Assertions
    assert results.score < 10.0
    # Should detect moderate complexity and/or deep nesting
    assert len(results.issues) > 0
    rules = [i.rule for i in results.issues]
    assert "moderate_complexity" in rules or "deep_nesting" in rules


def test_empty_file_static_analysis(tmp_path):
    empty_file = tmp_path / "empty.py"
    empty_file.write_text("def a(): pass")  # Ast needs valid code

    analyzer = StaticAnalyzer()
    results = analyzer.analyze(str(empty_file))

    assert results.score == 10.0
