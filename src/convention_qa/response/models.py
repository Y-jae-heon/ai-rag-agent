"""QueryResponse 및 SourceRef Pydantic v2 모델 정의."""

from typing import Literal

from pydantic import BaseModel


class SourceRef(BaseModel):
    """참조 문서 소스 정보 모델.

    Attributes:
        canonical_doc_id: 문서의 정규화된 식별자.
        title: 문서 제목.
        section: 참조한 섹션명 (없으면 None).
        excerpt: 참조한 발췌 텍스트 (없으면 None).
    """

    canonical_doc_id: str
    title: str
    section: str | None = None
    excerpt: str | None = None


class QueryResponse(BaseModel):
    """사용자 질의에 대한 최종 응답 모델.

    Attributes:
        answer: 사용자에게 반환할 응답 텍스트.
        answer_type: 응답 유형 식별자.
        intent: 분류된 사용자 의도.
        resolved_document: 해결된 문서 메타데이터 (없으면 None).
        sources: 참조한 문서 소스 목록.
    """

    answer: str
    answer_type: Literal["fulltext", "summary", "extract", "discover", "clarify"]
    intent: str
    resolved_document: dict | None = None
    sources: list[SourceRef] = []
