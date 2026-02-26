import pytest
from app.analyzers.static_analyzer import StaticAnalyzer

def test_high_complexity_detection(tmp_path):
    # Setup: Create a deeply nested 'if' structure
    complex_file = tmp_path / "complex.py"
    complex_file.write_text(
        "def deep_nesting(x):\n"
        "    if x > 0:\n"
        "        if x > 1:\n"
        "            if x > 2:\n"
        "                return x\n"
        "    return 0"
    )

    analyzer = StaticAnalyzer()
    results = analyzer.analyze(str(complex_file))

    # Assertions
    assert results["complexity_score"] > 1
    assert "complexity_report" in results
    assert results["rating"] in ["B", "C", "D"] # Should not be 'A'

def test_empty_file_static_analysis(tmp_path):
    empty_file = tmp_path / "empty.py"
    empty_file.write_text("")

    analyzer = StaticAnalyzer()
    results = analyzer.analyze(str(empty_file))
    
    assert results["complexity_score"] == 1