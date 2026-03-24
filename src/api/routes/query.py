"""질의 처리 라우터.

사용자 질문을 받아 intent 분류 → document resolution → action routing
파이프라인을 실행하고 QueryResponse를 반환한다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import (
    get_action_router,
    get_document_resolver,
    get_intent_classifier,
)
from src.api.models import QueryRequest, QueryResponse, ResolvedDocumentInfo
from src.convention_qa.action_routing.base_handler import HandlerResult
from src.convention_qa.action_routing.router import ActionRouter
from src.convention_qa.document_resolution.resolver import DocumentResolver
from src.convention_qa.query_understanding.intent_classifier import IntentClassifier

router = APIRouter()


def _build_response(
    handler_result: HandlerResult,
    intent: str,
) -> QueryResponse:
    """HandlerResult를 QueryResponse로 변환한다.

    Args:
        handler_result: ActionRouter가 반환한 handler 실행 결과.
        intent: IntentClassifier가 분류한 intent 문자열.

    Returns:
        HTTP 응답용 QueryResponse 인스턴스.
    """
    resolved_document: ResolvedDocumentInfo | None = None
    if handler_result.resolved_document is not None:
        doc = handler_result.resolved_document
        resolved_document = ResolvedDocumentInfo(
            canonical_doc_id=doc.get("canonical_doc_id", ""),
            title=doc.get("title", ""),
            path=doc.get("path", ""),
        )

    # answer_type이 QueryResponse의 Literal에 포함되지 않는 값이면 "clarify"로 fallback
    valid_answer_types = {"fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"}
    answer_type = handler_result.answer_type if handler_result.answer_type in valid_answer_types else "clarify"

    return QueryResponse(
        answer=handler_result.answer,
        answer_type=answer_type,  # type: ignore[arg-type]
        intent=intent,
        resolved_document=resolved_document,
        sources=handler_result.sources,
    )


@router.post("/api/v1/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    intent_classifier: IntentClassifier = Depends(get_intent_classifier),
    document_resolver: DocumentResolver = Depends(get_document_resolver),
    action_router: ActionRouter = Depends(get_action_router),
) -> QueryResponse:
    """사용자 질문을 처리하여 QueryResponse를 반환한다.

    파이프라인:
    1. IntentClassifier.classify() — 질문을 QueryUnderstandingResult로 분류
    2. DocumentResolver.resolve() — document_query를 canonical_doc_id로 해결
    3. ActionRouter.route_and_execute() — intent + resolution 기반 handler 실행
    4. HandlerResult → QueryResponse 변환 후 반환

    Args:
        request: 사용자 질의 요청 모델.
        intent_classifier: 싱글톤 IntentClassifier 인스턴스.
        document_resolver: 싱글톤 DocumentResolver 인스턴스.
        action_router: 싱글톤 ActionRouter 인스턴스.

    Returns:
        처리 결과를 담은 QueryResponse.

    Raises:
        HTTPException(500): 파이프라인 실행 중 예외가 발생한 경우.
    """
    try:
        # Step 1: Intent 분류
        understanding = intent_classifier.classify(
            request.question,
            request.model_dump(),
        )

        # Step 2: Document resolution
        resolution = document_resolver.resolve(
            understanding.document_query,
            understanding.domain,
            understanding.stack,
            topic=understanding.topic,
            raw_question=understanding.raw_question,
        )
        print(f"\nquestion = {request.question}")
        print(f"\nunderstanding = {understanding}")
        print(f"\nresolution = {resolution}")

        # Step 3: Action routing + handler 실행
        handler_result: HandlerResult = action_router.route_and_execute(
            understanding,
            resolution,
            request.question,
        )

        print(f"\nhandler_result = {handler_result}")

        # Step 4: HandlerResult → QueryResponse 변환
        return _build_response(handler_result, understanding.intent)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"질의 처리 중 오류가 발생했습니다: {exc}",
        ) from exc
