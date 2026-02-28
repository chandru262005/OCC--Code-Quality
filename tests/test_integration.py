"""
End-to-end integration tests for the Code Quality Gate API.
Tests the full flow: upload -> analyze -> report.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ---------- Health & Basic Tests ----------


class TestHealthEndpoints:
    """Test health and basic endpoints."""

    def test_health_returns_healthy(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_redirects(self):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (301, 302, 307)


# ---------- File Upload Flow ----------


class TestFileUploadFlow:
    """End-to-end tests for the file upload analysis flow."""

    def test_upload_clean_file_passes_gate(self, tmp_path, sample_clean_code):
        """Clean code should pass the quality gate."""
        test_file = tmp_path / "clean.py"
        test_file.write_text(sample_clean_code)

        with open(test_file, "rb") as f:
            response = client.post(
                "/api/v1/analyze/file",
                files={"file": ("clean.py", f, "text/x-python")},
                data={"threshold": "5.0"},
            )

        assert response.status_code == 200
        data = response.json()

        # Verify report structure
        assert "report_id" in data
        assert "timestamp" in data
        assert "overall_score" in data
        assert "passed" in data
        assert "results" in data
        assert "summary" in data
        assert data["source"] == "upload"
        assert data["files_analyzed"] == 1

        # Clean code should pass
        assert data["passed"] is True
        assert data["overall_score"] >= 5.0

    def test_upload_buggy_file_has_issues(self, tmp_path, sample_buggy_code):
        """Buggy code should have lint and static analysis issues."""
        test_file = tmp_path / "buggy.py"
        test_file.write_text(sample_buggy_code)

        with open(test_file, "rb") as f:
            response = client.post(
                "/api/v1/analyze/file",
                files={"file": ("buggy.py", f, "text/x-python")},
                data={"threshold": "9.0"},
            )

        assert response.status_code == 200
        data = response.json()

        # Should have issues detected
        total_issues = sum(len(r["issues"]) for r in data["results"])
        assert total_issues > 0

        # With a high threshold, buggy code should fail
        assert data["passed"] is False

    def test_upload_insecure_file_detects_vulnerabilities(
        self, tmp_path, sample_insecure_code
    ):
        """Insecure code should trigger security findings."""
        test_file = tmp_path / "insecure.py"
        test_file.write_text(sample_insecure_code)

        with open(test_file, "rb") as f:
            response = client.post(
                "/api/v1/analyze/file",
                files={"file": ("insecure.py", f, "text/x-python")},
                data={"threshold": "8.0"},
            )

        assert response.status_code == 200
        data = response.json()

        # Find the security analyzer result
        security_result = next(
            (r for r in data["results"] if r["analyzer_name"] == "security"), None
        )
        assert security_result is not None
        assert len(security_result["issues"]) > 0

        # Check specific security issues were detected
        security_rules = [i["rule"] for i in security_result["issues"]]
        assert "hardcoded_password" in security_rules or "eval_usage" in security_rules

    def test_upload_rejects_non_python(self, tmp_path):
        """Non-Python files should be rejected with 400."""
        test_file = tmp_path / "readme.txt"
        test_file.write_text("This is not Python code")

        with open(test_file, "rb") as f:
            response = client.post(
                "/api/v1/analyze/file",
                files={"file": ("readme.txt", f, "text/plain")},
                data={"threshold": "6.0"},
            )

        assert response.status_code == 400

    def test_threshold_pass_fail_logic(self, tmp_path, sample_clean_code):
        """Same file should pass with low threshold and could fail with very high threshold."""
        test_file = tmp_path / "code.py"
        test_file.write_text(sample_clean_code)

        # Test with low threshold - should pass
        with open(test_file, "rb") as f:
            response_low = client.post(
                "/api/v1/analyze/file",
                files={"file": ("code.py", f, "text/x-python")},
                data={"threshold": "1.0"},
            )

        assert response_low.status_code == 200
        assert response_low.json()["passed"] is True


# ---------- Report Structure Validation ----------


class TestReportStructure:
    """Validate the quality report structure and content."""

    def test_report_has_all_three_analyzers(self, tmp_path, sample_clean_code):
        """Report should contain results from lint, static, and security analyzers."""
        test_file = tmp_path / "code.py"
        test_file.write_text(sample_clean_code)

        with open(test_file, "rb") as f:
            response = client.post(
                "/api/v1/analyze/file",
                files={"file": ("code.py", f, "text/x-python")},
                data={"threshold": "6.0"},
            )

        data = response.json()
        analyzer_names = [r["analyzer_name"] for r in data["results"]]
        assert "lint" in analyzer_names
        assert "static" in analyzer_names
        assert "security" in analyzer_names

    def test_scores_are_within_valid_range(self, tmp_path, sample_clean_code):
        """All scores should be between 0 and 10."""
        test_file = tmp_path / "code.py"
        test_file.write_text(sample_clean_code)

        with open(test_file, "rb") as f:
            response = client.post(
                "/api/v1/analyze/file",
                files={"file": ("code.py", f, "text/x-python")},
                data={"threshold": "6.0"},
            )

        data = response.json()
        assert 0 <= data["overall_score"] <= 10

        for result in data["results"]:
            assert 0 <= result["score"] <= 10

    def test_report_not_found_returns_404(self):
        """Non-existent report should return 404."""
        response = client.get("/api/v1/reports/nonexistent-report-id")
        assert response.status_code == 404


# ---------- GitHub Endpoint Validation ----------


class TestGitHubEndpoint:
    """Test GitHub analysis endpoint validation."""

    def test_invalid_github_url_rejected(self):
        """Invalid GitHub URLs should be rejected."""
        response = client.post(
            "/api/v1/analyze/github",
            json={
                "repo_url": "not-a-valid-url",
                "branch": "main",
                "threshold": 6.0,
            },
        )
        assert response.status_code == 400

    def test_missing_repo_url_returns_422(self):
        """Missing required field should return validation error."""
        response = client.post(
            "/api/v1/analyze/github",
            json={"branch": "main", "threshold": 6.0},
        )
        assert response.status_code == 422
