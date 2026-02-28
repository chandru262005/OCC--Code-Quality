from .base import BaseAnalyzer
from app.models.report import AnalyzerResult, Issue
import ast
from pathlib import Path


class StaticAnalyzer(BaseAnalyzer):
    PYTHON_EXTENSIONS = {".py", ".pyi"}

    @property
    def name(self) -> str:
        return "static"

    def analyze(self, file_path: str, source_code: str = None) -> AnalyzerResult:
        if source_code is None:
            with open(file_path, "r") as f:
                source_code = f.read()

        extension = Path(file_path).suffix.lower()
        if extension not in self.PYTHON_EXTENSIONS:
            return self._analyze_generic(file_path, source_code)

        issues = []

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return AnalyzerResult(
                analyzer_name=self.name,
                score=0.0,
                issues=[
                    Issue(
                        severity="error",
                        message=f"Syntax error: {str(e)}",
                        file=file_path,
                        line=e.lineno,
                        rule="syntax_error",
                    )
                ],
                summary="Could not parse file due to syntax error",
            )

        lines = source_code.splitlines()

        # Check complexity using radon
        issues.extend(self._check_complexity(file_path, source_code, lines))

        # Check maintainability
        issues.extend(self._check_maintainability(file_path, source_code))

        # Check code smells via AST
        issues.extend(self._check_code_smells(file_path, tree, lines))

        # Calculate score
        score = self._calculate_score(issues)

        return AnalyzerResult(
            analyzer_name=self.name,
            score=round(score, 2),
            issues=issues,
            summary=self._build_summary(issues, score),
        )

    def _check_complexity(
        self, file_path: str, source_code: str, lines: list
    ) -> list[Issue]:
        """Use radon to check cyclomatic complexity."""
        issues = []
        try:
            from radon.complexity import cc_visit

            blocks = cc_visit(source_code)
            for block in blocks:
                line_content = (
                    lines[block.lineno - 1] if 0 < block.lineno <= len(lines) else None
                )
                if block.complexity > 10:
                    issues.append(
                        Issue(
                            severity="error",
                            message=f"High cyclomatic complexity ({block.complexity}) in '{block.name}'",
                            file=file_path,
                            line=block.lineno,
                            line_content=line_content,
                            rule="high_complexity",
                        )
                    )
                elif block.complexity > 5:
                    issues.append(
                        Issue(
                            severity="warning",
                            message=f"Moderate cyclomatic complexity ({block.complexity}) in '{block.name}'",
                            file=file_path,
                            line=block.lineno,
                            line_content=line_content,
                            rule="moderate_complexity",
                        )
                    )
        except Exception:
            pass
        return issues

    def _check_maintainability(self, file_path: str, source_code: str) -> list[Issue]:
        """Use radon to check maintainability index."""
        issues = []
        try:
            from radon.metrics import mi_visit

            mi_score = mi_visit(source_code, True)
            if mi_score < 10:
                issues.append(
                    Issue(
                        severity="error",
                        message=f"Very low maintainability index: {mi_score:.1f} (threshold: 10)",
                        file=file_path,
                        line=1,
                        rule="low_maintainability",
                    )
                )
            elif mi_score < 20:
                issues.append(
                    Issue(
                        severity="warning",
                        message=f"Moderate maintainability index: {mi_score:.1f} (threshold: 20)",
                        file=file_path,
                        line=1,
                        rule="moderate_maintainability",
                    )
                )
        except Exception:
            pass
        return issues

    def _check_code_smells(
        self, file_path: str, tree: ast.AST, lines: list
    ) -> list[Issue]:
        """AST-based code smell detection."""
        issues = []

        # Large file check
        if len(lines) > 300:
            issues.append(
                Issue(
                    severity="info",
                    message=f"Large file: {len(lines)} lines (threshold: 300)",
                    file=file_path,
                    line=1,
                    rule="large_file",
                )
            )

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Too many arguments
                num_args = len(node.args.args)
                if num_args > 5:
                    line_content = (
                        lines[node.lineno - 1]
                        if 0 < node.lineno <= len(lines)
                        else None
                    )
                    issues.append(
                        Issue(
                            severity="warning",
                            message=f"Too many arguments ({num_args}) in function '{node.name}'",
                            file=file_path,
                            line=node.lineno,
                            line_content=line_content,
                            rule="too_many_args",
                        )
                    )

                # Long function
                if hasattr(node, "end_lineno") and node.end_lineno:
                    func_length = node.end_lineno - node.lineno + 1
                    if func_length > 50:
                        line_content = (
                            lines[node.lineno - 1]
                            if 0 < node.lineno <= len(lines)
                            else None
                        )
                        issues.append(
                            Issue(
                                severity="warning",
                                message=f"Long function '{node.name}': {func_length} lines (threshold: 50)",
                                file=file_path,
                                line=node.lineno,
                                line_content=line_content,
                                rule="long_function",
                            )
                        )

                # Too many return statements
                return_count = sum(
                    1 for child in ast.walk(node) if isinstance(child, ast.Return)
                )
                if return_count > 4:
                    line_content = (
                        lines[node.lineno - 1]
                        if 0 < node.lineno <= len(lines)
                        else None
                    )
                    issues.append(
                        Issue(
                            severity="info",
                            message=f"Too many return statements ({return_count}) in '{node.name}'",
                            file=file_path,
                            line=node.lineno,
                            line_content=line_content,
                            rule="too_many_returns",
                        )
                    )

                # Deep nesting
                max_depth = self._get_max_nesting(node)
                if max_depth > 4:
                    line_content = (
                        lines[node.lineno - 1]
                        if 0 < node.lineno <= len(lines)
                        else None
                    )
                    issues.append(
                        Issue(
                            severity="warning",
                            message=f"Deep nesting (depth {max_depth}) in '{node.name}'",
                            file=file_path,
                            line=node.lineno,
                            line_content=line_content,
                            rule="deep_nesting",
                        )
                    )

        return issues

    def _get_max_nesting(self, node: ast.AST, depth: int = 0) -> int:
        """Calculate maximum nesting depth of a function."""
        max_depth = depth
        nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, nesting_nodes):
                child_depth = self._get_max_nesting(child, depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._get_max_nesting(child, depth)
                max_depth = max(max_depth, child_depth)
        return max_depth

    def _calculate_score(self, issues: list[Issue]) -> float:
        """Start at 10.0, deduct based on severity."""
        score = 10.0
        for issue in issues:
            if issue.severity == "error":
                score -= 1.5
            elif issue.severity == "warning":
                score -= 0.5
            elif issue.severity == "info":
                score -= 0.1
        return max(0.0, score)

    def _analyze_generic(self, file_path: str, source_code: str) -> AnalyzerResult:
        """Language-agnostic static checks for non-Python files."""
        issues: list[Issue] = []
        lines = source_code.splitlines()

        if not source_code.strip():
            issues.append(
                Issue(
                    severity="error",
                    message="Empty source file",
                    file=file_path,
                    line=1,
                    rule="empty_file",
                )
            )

        if len(lines) > 600:
            issues.append(
                Issue(
                    severity="warning",
                    message=f"Very large file: {len(lines)} lines (threshold: 600)",
                    file=file_path,
                    line=1,
                    rule="large_file_non_python",
                )
            )

        max_brace_depth = 0
        current_depth = 0
        for idx, line in enumerate(lines, start=1):
            for ch in line:
                if ch == "{":
                    current_depth += 1
                    max_brace_depth = max(max_brace_depth, current_depth)
                elif ch == "}":
                    current_depth = max(0, current_depth - 1)

            if len(line) > 240:
                issues.append(
                    Issue(
                        severity="info",
                        message="Very long line may hurt readability",
                        file=file_path,
                        line=idx,
                        line_content=line,
                        rule="very_long_line_non_python",
                    )
                )

        if max_brace_depth > 6:
            issues.append(
                Issue(
                    severity="warning",
                    message=f"Deep block nesting detected (depth {max_brace_depth})",
                    file=file_path,
                    line=1,
                    rule="deep_nesting_non_python",
                )
            )

        score = self._calculate_score(issues)
        return AnalyzerResult(
            analyzer_name=self.name,
            score=round(score, 2),
            issues=issues,
            summary=self._build_summary(issues, score),
        )
