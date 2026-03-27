"""FastAPI request and response models for RAG v4."""

from __future__ import annotations

from pydantic import BaseModel


class QueryRequestV4(BaseModel):
    question: str
    debug: bool = False


class CitationV4(BaseModel):
    title: str
    source_path: str
    section_id: str
    section_type: str
    excerpt: str


class TopDocumentV4(BaseModel):
    doc_id: str
    title: str
    source_path: str
    score: float
    matched_by: list[str]


class QueryResponseV4(BaseModel):
    answer: str
    citations: list[CitationV4]
    top_documents: list[TopDocumentV4]
    confidence: float
    needs_clarification: bool
    trace_id: str | None = None
    debug: dict | None = None

