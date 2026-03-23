"""HTTP 요청/응답 Pydantic v2 모델 정의."""

from typing import Literal

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """사용자 질의 요청 모델.

    Attributes:
        question: 사용자가 입력한 자연어 질문.
        domain: 도메인 힌트 (frontend/backend). None이면 자동 감지.
        stack: 기술 스택 힌트. None이면 자동 감지.
        intent_hint: 클라이언트가 제공하는 intent 힌트 (선택적).
    """

    question: str
    domain: Literal["frontend", "backend"] | None = None
    stack: str | None = None
    intent_hint: str | None = None


class ResolvedDocumentInfo(BaseModel):
    """해결된 문서 정보 모델.

    Attributes:
        canonical_doc_id: 문서의 정규화된 식별자.
        title: 문서 제목.
        path: 문서 파일 경로.
    """

    canonical_doc_id: str
    title: str
    path: str


class QueryResponse(BaseModel):
    """사용자 질의에 대한 HTTP 응답 모델.

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
    resolved_document: ResolvedDocumentInfo | None = None
    sources: list[dict] = []
