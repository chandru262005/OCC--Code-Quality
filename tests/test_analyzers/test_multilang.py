from app.analyzers.lint_analyzer import LintAnalyzer
from app.analyzers.static_analyzer import StaticAnalyzer
from app.analyzers.security_analyzer import SecurityAnalyzer


def test_lint_non_python_generic_rules(tmp_path):
    rust_file = tmp_path / "main.rs"
    rust_file.write_text("fn main() {\n\tprintln!(\"hello\");   \n" + "a" * 130 + "\n}\n")

    analyzer = LintAnalyzer()
    result = analyzer.analyze(str(rust_file))

    assert result.score < 10.0
    rules = [issue.rule for issue in result.issues]
    assert "generic_line_length" in rules


def test_static_non_python_nesting_detection(tmp_path):
    cpp_file = tmp_path / "main.cpp"
    cpp_file.write_text(
        "int main(){\n"
        "if(1){ if(1){ if(1){ if(1){ if(1){ if(1){ if(1){ return 0; } } } } } } }\n"
        "}\n"
    )

    analyzer = StaticAnalyzer()
    result = analyzer.analyze(str(cpp_file))

    assert result.score < 10.0
    rules = [issue.rule for issue in result.issues]
    assert "deep_nesting_non_python" in rules


def test_security_non_python_c_and_rust_patterns(tmp_path):
    mixed_file = tmp_path / "unsafe.c"
    source = "char buf[8]; strcpy(buf, input); system(\"ls\"); unsafe { let x = 1; }"
    mixed_file.write_text(source)

    analyzer = SecurityAnalyzer()
    result = analyzer.analyze(str(mixed_file), source)

    rules = [issue.rule for issue in result.issues]
    assert "c_unsafe_functions" in rules
    assert "c_command_execution" in rules
    assert "rust_unsafe_block" in rules
