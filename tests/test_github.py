from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_github_invalid_url():
    """Test that invalid GitHub URLs are rejected."""
    response = client.post(
        "/api/v1/analyze/github",
        json={
            "repo_url": "not-a-valid-url",
            "branch": "main",
            "threshold": 6.0,
        },
    )
    assert response.status_code == 400


def test_github_request_accepts_valid_schema():
    """Test that the endpoint accepts a valid request schema (even if clone fails)."""
    response = client.post(
        "/api/v1/analyze/github",
        json={
            "repo_url": "https://github.com/nonexistent/nonexistent-repo-12345",
            "branch": "main",
            "threshold": 6.0,
        },
    )
    # Should fail with 400 (clone failure) not 422 (validation error)
    assert response.status_code == 400


def test_github_missing_repo_url():
    """Test that missing repo_url returns 422 validation error."""
    response = client.post(
        "/api/v1/analyze/github",
        json={
            "branch": "main",
            "threshold": 6.0,
        },
    )
    assert response.status_code == 422
