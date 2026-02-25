from pydantic import BaseModel
from typing import List


class GitHubAnalysisRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    threshold: float = 6.0
    file_extensions: List[str] = [".py"]
