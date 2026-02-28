from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application configuration via environment variables."""

    APP_NAME: str = "Code Quality Gate"
    DEBUG: bool = False
    LOG_LEVEL: str = "info"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # File handling
    UPLOAD_DIR: str = "/tmp/cqg_uploads"
    REPO_DIR: str = "/tmp/cqg_repos"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".py"]

    # Analysis
    QUALITY_THRESHOLD: float = 6.0
    ANALYZER_TIMEOUT_SECONDS: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
