"""BaseHandler 추상 클래스 및 공유 컨텍스트/결과 모델 정의.

모든 intent handler는 BaseHandler를 상속하고 handle() 메서드를 구현해야 한다.
HandlerContext는 handler 실행에 필요한 입력 데이터를 담고,
HandlerResult는 handler의 출력 결과를 담는다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class HandlerContext(BaseModel):
    """Handler 실행에 필요한 입력 컨텍스트.

    Attributes:
        question: 사용자가 입력한 원본 질문.
        intent: 분류된 intent 문자열 (discover/summarize/extract/fulltext/compare).
        resolution: DocumentResolutionResult 인스턴스 (forward reference, Any 타입).
    """

    question: str = Field(description="사용자 원본 질문.")
    intent: str = Field(description="분류된 intent.")
    resolution: Any = Field(
        description="DocumentResolutionResult 인스턴스. TK-02에서 타입 구체화 예정."
    )

    model_config = {"arbitrary_types_allowed": True}


class HandlerResult(BaseModel):
    """Handler 실행 결과.

    Attributes:
        answer: 사용자에게 반환할 최종 응답 문자열.
        answer_type: 응답 유형 식별자 (fulltext/summary/extract/clarify/discover 등).
        sources: 참조한 문서 소스 목록.
        resolved_document: 해결된 문서 메타데이터 (없으면 None).
    """

    answer: str = Field(description="사용자에게 반환할 최종 응답.")
    answer_type: str = Field(description="응답 유형 식별자.")
    sources: list[dict] = Field(default_factory=list, description="참조 소스 목록.")
    resolved_document: dict | None = Field(
        default=None, description="해결된 문서 메타데이터."
    )


class BaseHandler(ABC):
    """모든 intent handler의 추상 기반 클래스.

    Subclass는 반드시 handle() 메서드를 구현해야 한다.
    """

    @abstractmethod
    def handle(self, context: HandlerContext) -> HandlerResult:
        """HandlerContext를 받아 HandlerResult를 반환한다.

        Args:
            context: handler 실행에 필요한 입력 데이터.

        Returns:
            처리 결과를 담은 HandlerResult 인스턴스.
        """
        ...
