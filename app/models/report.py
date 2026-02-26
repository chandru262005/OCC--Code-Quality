from pydantic import BaseModel
from typing import List, Optional


class Issue(BaseModel):
    severity: str
    message: str
    file: str
    line: Optional[int] = None
    rule: Optional[str] = None


class AnalyzerResult(BaseModel):
    analyzer_name: str
    score: float
    issues: List[Issue]
    summary: str


class QualityReport(BaseModel):
    report_id: str
    timestamp: str
    source: str
    files_analyzed: int
    overall_score: float
    threshold: float
    passed: bool
    results: List[AnalyzerResult]
    summary: str
