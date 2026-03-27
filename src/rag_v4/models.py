"""Core models used by the RAG v4 pipeline."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ParsedSection(BaseModel):
    section_id: str
    section_type: str
    heading: str
    content: str


class ParsedDocument(BaseModel):
    doc_id: str
    title: str
    source_path: str
    sections: list[ParsedSection]


class SectionRecord(BaseModel):
    section_id: str
    doc_id: str
    title: str
    source_path: str
    section_type: str
    heading: str
    content: str
    index_text: str


class NormalizedQuery(BaseModel):
    raw: str
    normalized: str
    expansions: list[str] = Field(default_factory=list)
    retrieval_text: str


class RetrievedDocument(BaseModel):
    doc_id: str
    title: str
    source_path: str
    score: float
    matched_by: list[str] = Field(default_factory=list)


class RetrievedSection(BaseModel):
    section_id: str
    doc_id: str
    title: str
    source_path: str
    section_type: str
    heading: str
    content: str
    score: float
    source: str
    rank: int


class Citation(BaseModel):
    title: str
    source_path: str
    section_id: str
    section_type: str
    excerpt: str


class QueryResult(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    top_documents: list[RetrievedDocument] = Field(default_factory=list)
    confidence: float = 0.0
    needs_clarification: bool = False
    trace_id: str | None = None
    debug: dict[str, Any] | None = None

