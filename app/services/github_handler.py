from pathlib import Path
from fastapi import HTTPException
import shutil
import re
import os
from app.config import settings

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
    """Clone a GitHub repository to a temporary directory.

    Tries to clone the specified branch, with fallbacks to common default branches
    if the specified branch doesn't exist.
    """
    if not validate_github_url(url):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid GitHub URL: {url}. Expected format: https://github.com/user/repo",
        )

    from git import Repo

    repo_dir = Path(settings.REPO_DIR) / f"repo_{os.urandom(8).hex()}"
    repo_dir.parent.mkdir(parents=True, exist_ok=True)

    # List of branches to try in order
    branches_to_try = [branch]
    if branch != "main":
        branches_to_try.append("main")
    if branch != "master":
        branches_to_try.append("master")
    if branch != "develop":
        branches_to_try.append("develop")

    last_error = None

    for branch_name in branches_to_try:
        try:
            Repo.clone_from(url, str(repo_dir), branch=branch_name, depth=1)
            if branch_name != branch:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Failed to clone branch '{branch}', successfully cloned '{branch_name}' instead")
            return repo_dir
        except Exception as e:
            last_error = e
            # Clean up failed clone attempt
            if repo_dir.exists():
                shutil.rmtree(repo_dir, ignore_errors=True)
                repo_dir = Path(settings.REPO_DIR) / f"repo_{os.urandom(8).hex()}"
                repo_dir.parent.mkdir(parents=True, exist_ok=True)

    # All branch attempts failed
    raise HTTPException(
        status_code=400,
        detail=(
            f"Failed to clone repository: Could not find any of the branches "
            f"{branches_to_try}. Last error: {str(last_error)}"
        ),
    )


def list_python_files(
    repo_path: Path, extensions: list[str] | None = None
) -> list[Path]:
    """Walk directory and return all matching files, skipping hidden/venv dirs."""
    if extensions is None:
        extensions = settings.ALLOWED_EXTENSIONS

    normalized_extensions = []
    for ext in extensions:
        item = ext.strip().lower()
        if not item:
            continue
        if item == "*":
            normalized_extensions = ["*"]
            break
        if not item.startswith("."):
            item = f".{item}"
        normalized_extensions.append(item)

    if not normalized_extensions:
        normalized_extensions = ["*"]

    allow_all_extensions = "*" in normalized_extensions

    source_files = []
    for root, dirs, files in os.walk(repo_path):
        # Skip unwanted directories (modify dirs in-place to prevent os.walk from descending)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

        for f in files:
            file_name = f.lower()
            if allow_all_extensions or any(
                file_name.endswith(ext) for ext in normalized_extensions
            ):
                source_files.append(Path(root) / f)

    return source_files


def cleanup_repo(path: Path) -> None:
    """Remove cloned repo directory."""
    if path.exists() and path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
