from app.analyzers.security_analyzer import SecurityAnalyzer


def test_security_vulnerabilities(tmp_path):
    vuln_code = tmp_path / "vuln.py"
    # Contains 2 dangerous patterns
    source = "eval('import os')\npassword = '123'"
    vuln_code.write_text(source)

    analyzer = SecurityAnalyzer()
    results = analyzer.analyze(str(vuln_code), source)

    assert results.score < 10.0
    assert len(results.issues) == 2
    rules = [i.rule for i in results.issues]
    assert "eval_usage" in rules
    assert "hardcoded_password" in rules


def test_security_clean_code(tmp_path):
    clean_code = tmp_path / "clean.py"
    source = "def safe(): return True"
    clean_code.write_text(source)

    analyzer = SecurityAnalyzer()
    results = analyzer.analyze(str(clean_code), source)

    assert results.score == 10.0
    assert len(results.issues) == 0
