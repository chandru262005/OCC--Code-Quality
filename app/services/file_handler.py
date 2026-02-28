from pathlib import Path
from fastapi import UploadFile, HTTPException
import uuid
import os

UPLOAD_DIR = Path("/tmp/cqg_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = [".py"]
MAX_FILE_SIZE_MB = 10


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file extension and size."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )

    # Check file size (read content and check)
    content = file.file.read()
    file.file.seek(0)  # Reset file position
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE_MB}MB",
        )


def save_upload(file: UploadFile) -> Path:
    """Save uploaded file to temp directory with UUID prefix."""
    file_id = f"{uuid.uuid4()}_{file.filename}"
    path = UPLOAD_DIR / file_id

    with open(path, "wb") as f:
        f.write(file.file.read())

    return path


def cleanup_upload(path: Path) -> None:
    """Delete temp file."""
    if path.exists():
        path.unlink()
