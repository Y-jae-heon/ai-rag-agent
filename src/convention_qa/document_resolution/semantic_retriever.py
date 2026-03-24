"""ChromaDB document_index 컬렉션을 사용한 semantic search 모듈."""

import logging
from pathlib import Path

from .models import DocumentCandidate

logger = logging.getLogger(__name__)


def semantic_search(
    document_query: str,
    persist_dir: Path,
    domain: str | None = None,
    stack: str | None = None,
    k: int = 5,
    threshold: float = 0.75,
) -> list[DocumentCandidate]:
    """ChromaDB document_index에서 semantic search를 수행한다.

    Args:
        document_query: 검색할 문서 쿼리 문자열.
        persist_dir: ChromaDB persist 디렉토리 경로.
        domain: 필터링할 도메인 (frontend/backend). None이면 필터 없음.
        stack: 필터링할 기술 스택. None이면 필터 없음.
        k: 반환할 최대 결과 수.
        threshold: confidence 최소 임계값 (이 값 미만 결과 제외).

    Returns:
        DocumentCandidate 목록 (score 내림차순). 컬렉션이 없거나 오류 시 빈 리스트.
    """

    print("\nSEMANTIC SEARCH START")
    try:
        from langchain_chroma import Chroma
        from langchain_openai import OpenAIEmbeddings
    except ImportError as e:
        logger.warning("langchain_chroma 또는 langchain_openai를 import할 수 없습니다: %s", e)
        return []

    collection_persist_dir = persist_dir / "document_index"

    if not collection_persist_dir.exists():
        logger.info("document_index 컬렉션 디렉토리가 없습니다 (ingest 미실행): %s", collection_persist_dir)
        return []

    try:
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma(
            collection_name="document_index",
            persist_directory=str(collection_persist_dir),
            embedding_function=embeddings,
        )
    except Exception as e:
        logger.warning("ChromaDB 초기화 실패 (graceful 처리): %s", e)
        return []

    # domain, stack 필터 구성
    where_filter: dict | None = None
    conditions: list[dict] = []
    if domain is not None:
        conditions.append({"domain": {"$eq": domain}})
    if stack is not None:
        conditions.append({"stack": {"$eq": stack}})

    if len(conditions) == 1:
        where_filter = conditions[0]
    elif len(conditions) > 1:
        where_filter = {"$and": conditions}

    try:
        print(f"[ChromaDB] similarity_search_with_score() 호출 — query={document_query!r}, k={k}, filter={where_filter}")
        if where_filter:
            results = vectorstore.similarity_search_with_score(
                document_query, k=k, filter=where_filter
            )
        else:
            results = vectorstore.similarity_search_with_score(document_query, k=k)
        print(f"[ChromaDB] similarity_search_with_score() 완료 — 결과 수={len(results)}")
    except Exception as e:
        logger.info("semantic search 실행 중 오류 (graceful 처리): %s", e)
        return []

    candidates: list[DocumentCandidate] = []
    for doc, distance in results:
        # L2 distance를 confidence로 변환: confidence = 1 / (1 + distance)
        confidence = 1.0 / (1.0 + distance)

        if confidence < threshold:
            logger.debug(
                "[semantic_search] 임계값 미달 제외 — title=%s, confidence=%.4f (threshold=%.2f)",
                (doc.metadata or {}).get("title", ""),
                confidence,
                threshold,
            )
            continue

        metadata = doc.metadata or {}
        candidates.append(
            DocumentCandidate(
                canonical_doc_id=metadata.get("canonical_doc_id", ""),
                title=metadata.get("title", ""),
                path=metadata.get("path", ""),
                score=confidence,
                domain=metadata.get("domain"),
                stack=metadata.get("stack"),
            )
        )

    # score 내림차순 정렬
    candidates.sort(key=lambda c: c.score, reverse=True)

    logger.info(
        "[semantic_search] query=%r | 필터=(domain=%s, stack=%s) | 결과 %d건",
        document_query,
        domain,
        stack,
        len(candidates),
    )
    for i, c in enumerate(candidates):
        logger.info(
            "  [%d] title=%r  canonical_doc_id=%s  score=%.4f  domain=%s  stack=%s",
            i + 1,
            c.title,
            c.canonical_doc_id,
            c.score,
            c.domain,
            c.stack,
        )

    return candidates
