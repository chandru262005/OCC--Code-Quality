from pydantic import BaseModel, field_validator
from typing import List


class GitHubAnalysisRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    threshold: float = 6.0
    file_extensions: List[str] = ["*"]
    ai_model: str | None = None

    @field_validator("file_extensions")
    @classmethod
    def normalize_file_extensions(cls, value: List[str]) -> List[str]:
        if not value:
            return ["*"]

        normalized: List[str] = []
        for ext in value:
            item = ext.strip().lower()
            if not item:
                continue
            if item == "*":
                return ["*"]
            if not item.startswith("."):
                item = f".{item}"
            normalized.append(item)

        return list(dict.fromkeys(normalized)) or ["*"]

    @field_validator("ai_model")
    @classmethod
    def normalize_ai_model(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None
