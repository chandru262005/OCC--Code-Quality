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
    # Use "*" to allow any file extension.
    ALLOWED_EXTENSIONS: List[str] = ["*"]

    # Analysis
    QUALITY_THRESHOLD: float = 6.0
    ANALYZER_TIMEOUT_SECONDS: int = 30

    # Optional AI integrations
    AI_INTEGRATIONS_ENABLED: bool = True
    AI_PROVIDERS: List[str] = ["openrouter"]
    AI_REQUEST_TIMEOUT_SECONDS: int = 20
    AI_MAX_FILES: int = 30
    AI_MAX_CHARS_PER_FILE: int = 20000
    AI_CODERABBIT_API_URL: str = ""
    AI_CODERABBIT_API_KEY: str = ""
    AI_GREPTILE_API_URL: str = ""
    AI_GREPTILE_API_KEY: str = ""
    AI_OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    AI_OPENROUTER_API_KEY: str = ""
    AI_OPENROUTER_MODEL: str = "openai/gpt-oss-120b:free"
    AI_OPENROUTER_FREE_MODELS: List[str] = [
        "openai/gpt-oss-120b:free",
        "arcee-ai/trinity-large-preview:free",
        "z-ai/glm-4.5-air:free",
        "stepfun/step-3.5-flash:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
    ]
    AI_OPENROUTER_HTTP_REFERER: str = ""
    AI_OPENROUTER_APP_TITLE: str = "Code Quality Gate"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
