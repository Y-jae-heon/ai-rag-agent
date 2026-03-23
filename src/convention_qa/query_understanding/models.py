"""QueryUnderstandingResult Pydantic 모델 정의.

사용자 질문을 분류한 결과를 구조화하여 표현한다.
intent, document_query, domain, stack, topic, raw_question, confidence 필드를 포함한다.
"""

from typing import Literal
from pydantic import BaseModel, Field


class QueryUnderstandingResult(BaseModel):
    """사용자 질문 분류 결과 모델."""

    intent: Literal["discover", "summarize", "extract", "fulltext", "compare"] = Field(
        description=(
            "분류된 의도. "
            "discover=문서 목록 요청, summarize=문서 요약 요청, "
            "extract=특정 규칙/정보 추출, fulltext=문서 원문 전체 요청, "
            "compare=두 항목 비교"
        )
    )
    document_query: str | None = Field(
        default=None,
        description="검색할 문서명 또는 문서 키워드. 특정 문서를 지칭하지 않으면 null.",
    )
    document_queries: list[str] | None = Field(
        default=None,
        description="compare intent에서 비교할 두 문서의 키워드 목록. compare 외에는 null.",
    )
    domain: Literal["frontend", "backend"] | None = Field(
        default=None,
        description="질문이 특정 도메인(frontend/backend)에 한정된 경우. 불명확하면 null.",
    )
    stack: str | None = Field(
        default=None,
        description="특정 기술 스택 (spring, kotlin, nestjs, react 등). 불명확하면 null.",
    )
    topic: str | None = Field(
        default=None,
        description="extract intent일 때 추출 대상 주제/규칙. 그 외에는 null.",
    )
    raw_question: str = Field(
        description="사용자가 입력한 원본 질문 문자열."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="분류 신뢰도 (0.0 ~ 1.0).",
    )
