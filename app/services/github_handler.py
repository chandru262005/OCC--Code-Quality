from pathlib import Path
from fastapi import HTTPException
import tempfile
import shutil
import re
import os

REPO_DIR = Path("/tmp/cqg_repos")
REPO_DIR.mkdir(parents=True, exist_ok=True)

SKIP_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "node_modules",
    ".tox",
    "build",
    "dist",
    ".eggs",
}


def validate_github_url(url: str) -> bool:
    """Validate that the URL looks like a GitHub repository URL."""
    pattern = r"^https?://github\.com/[\w\-\.]+/[\w\-\.]+/?$"
    return bool(re.match(pattern, url))


def clone_repo(url: str, branch: str = "main") -> Path:
    """Clone a GitHub repository to a temporary directory."""
    if not validate_github_url(url):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid GitHub URL: {url}. Expected format: https://github.com/user/repo",
        )

    try:
        from git import Repo

        repo_dir = REPO_DIR / f"repo_{os.urandom(8).hex()}"
        Repo.clone_from(url, str(repo_dir), branch=branch, depth=1)
        return repo_dir
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to clone repository: {str(e)}"
        )


def list_python_files(repo_path: Path, extensions: list[str] = None) -> list[Path]:
    """Walk directory and return all matching Python files, skipping hidden/venv dirs."""
    if extensions is None:
        extensions = [".py"]

    python_files = []
    for root, dirs, files in os.walk(repo_path):
        # Skip unwanted directories (modify dirs in-place to prevent os.walk from descending)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

        for f in files:
            if any(f.endswith(ext) for ext in extensions):
                python_files.append(Path(root) / f)

    return python_files


def cleanup_repo(path: Path) -> None:
    """Remove cloned repo directory."""
    if path.exists() and path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
