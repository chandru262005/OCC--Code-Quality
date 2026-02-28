import pytest
from fastapi.testclient import TestClient
from app.main import app
import os

client = TestClient(app)


def test_health_check():
    """Test health endpoint returns 200 with expected data."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


def test_root_redirects_to_docs():
    """Test root endpoint redirects to /docs."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 302, 301)


def test_upload_python_file(tmp_path):
    """Test uploading a valid Python file for analysis."""
    # Create a temp Python file
    test_file = tmp_path / "test_code.py"
    test_file.write_text(
        'def add(a, b):\n    """Add two numbers."""\n    return a + b\n'
    )

    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/analyze/file",
            files={"file": ("test_code.py", f, "text/x-python")},
            data={"threshold": "6.0"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert "passed" in data
    assert "results" in data
    assert data["source"] == "upload"
    assert data["files_analyzed"] == 1
    assert isinstance(data["overall_score"], (int, float))


def test_upload_rejects_non_python_file(tmp_path):
    """Test that non-Python files are rejected."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("This is not a Python file")

    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/analyze/file",
            files={"file": ("test.txt", f, "text/plain")},
            data={"threshold": "6.0"},
        )

    assert response.status_code == 400


def test_upload_clean_code_high_score(tmp_path):
    """Test that clean code gets a high score."""
    test_file = tmp_path / "clean.py"
    test_file.write_text(
        "def add(a: int, b: int) -> int:\n"
        '    """Add two numbers and return the result."""\n'
        "    return a + b\n"
    )

    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/analyze/file",
            files={"file": ("clean.py", f, "text/x-python")},
            data={"threshold": "5.0"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["overall_score"] >= 5.0
    assert data["passed"] is True


def test_upload_insecure_code_detects_issues(tmp_path):
    """Test that insecure code triggers security issues."""
    test_file = tmp_path / "insecure.py"
    test_file.write_text(
        "import os\n"
        'password = "secret123"\n'
        'eval("dangerous code")\n'
        'os.system("rm -rf /")\n'
    )

    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/analyze/file",
            files={"file": ("insecure.py", f, "text/x-python")},
            data={"threshold": "8.0"},
        )

    assert response.status_code == 200
    data = response.json()
    # Should have security issues detected
    security_result = next(
        (r for r in data["results"] if r["analyzer_name"] == "security"), None
    )
    assert security_result is not None
    assert len(security_result["issues"]) > 0


def test_report_not_found():
    """Test that non-existent report returns 404."""
    response = client.get("/api/v1/reports/non-existent-id")
    assert response.status_code == 404
