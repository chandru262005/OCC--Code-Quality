from pathlib import Path
from fastapi import UploadFile
import uuid

UPLOAD_DIR = Path("/tmp/cqg_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_upload(file: UploadFile) -> Path:
    file_id = f"{uuid.uuid4()}_{file.filename}"
    path = UPLOAD_DIR / file_id

    with open(path, "wb") as f:
        f.write(file.file.read())

    return path

def cleanup_upload(path: Path):
    if path.exists():
        path.unlink()