"""DocumentResolutionResult 및 DocumentCandidate Pydantic 모델 정의."""

from typing import Literal

from pydantic import BaseModel


class DocumentCandidate(BaseModel):
    canonical_doc_id: str
    title: str
    path: str
    score: float
    domain: str | None = None
    stack: str | None = None


class DocumentResolutionResult(BaseModel):
    resolved: bool
    canonical_doc_id: str | None = None
    path: str | None = None
    title: str | None = None
    confidence: float = 0.0
    resolution_strategy: Literal["exact", "alias", "semantic", "keyword_tiebreak", "unresolved"]
    candidates: list[DocumentCandidate] = []
