import sys
import os
from app.analyzers.static_analyzer import StaticAnalyzer
from app.analyzers.lint_analyzer import LintAnalyzer
from app.analyzers.security_analyzer import SecurityAnalyzer

def run_all(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    print(f"\n{'='*50}")
    print(f"ANALYZING: {file_path}")
    print(f"{'='*50}")

    analyzers = [
        StaticAnalyzer(),
        LintAnalyzer(),
        SecurityAnalyzer()
    ]

    for analyzer in analyzers:
        try:
            result = analyzer.analyze(file_path)
            print(f"\n[ {analyzer.name.upper()} ]")
            print(f"Score: {result.score}/10")
            print(f"Summary: {result.summary}")
            if result.issues:
                print("Issues Found:")
                for issue in result.issues:
                    loc = f"L{issue.line}" if issue.line else "???"
                    if issue.column:
                        loc += f":C{issue.column}"
                    
                    print(f"  - [{issue.severity.upper()}] {loc}: {issue.message} (Rule: {issue.rule})")
                    if issue.line_content:
                        print(f"    > {issue.line_content.strip()}")

        except Exception as e:
            print(f"Error in {analyzer.name}: {str(e)}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "sample_files/buggy_code.py"
    run_all(target)
