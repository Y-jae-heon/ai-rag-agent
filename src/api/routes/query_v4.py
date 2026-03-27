"""FastAPI route for the greenfield RAG v4 endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies_v4 import get_rag_v4_service
from src.api.models_v4 import (
    CitationV4,
    QueryRequestV4,
    QueryResponseV4,
    TopDocumentV4,
)
from src.rag_v4.service import RagV4Service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/v4/query", response_model=QueryResponseV4)
async def query_v4(
    request: QueryRequestV4,
    service: RagV4Service = Depends(get_rag_v4_service),
) -> QueryResponseV4:
    try:
        result = service.query(request.question, debug=request.debug)
        return QueryResponseV4(
            answer=result.answer,
            citations=[CitationV4(**citation.model_dump()) for citation in result.citations],
            top_documents=[TopDocumentV4(**document.model_dump()) for document in result.top_documents],
            confidence=result.confidence,
            needs_clarification=result.needs_clarification,
            trace_id=result.trace_id,
            debug=result.debug,
        )
    except Exception as exc:
        logger.exception("RAG v4 query failed for question=%r", request.question)
        raise HTTPException(
            status_code=500,
            detail=f"질의 처리 중 오류가 발생했습니다: {exc}",
        ) from exc
