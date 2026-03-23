"""DocumentResolver: 3단계 document resolution 로직."""

import logging
from pathlib import Path

from ..indexing.config import CHROMA_PERSIST_DIR, SIMILARITY_THRESHOLD
from ..indexing.manifest import load_alias_registry
from .exact_matcher import alias_match, exact_match
from .models import DocumentCandidate, DocumentResolutionResult
from .semantic_retriever import semantic_search

logger = logging.getLogger(__name__)

_ALIAS_REGISTRY_PATH = (
    Path(__file__).parent.parent / "indexing" / "alias_registry.json"
)


class DocumentResolver:
    """3단계 resolution을 통해 document_query를 canonical_doc_id로 해결한다.

    Resolution 순서:
    1. exact_match — title 정규화 완전/부분 일치
    2. alias_match — alias_registry 기반 alias 일치
    3. semantic_search — ChromaDB vector similarity search (domain/stack 필터 적용)
    4. semantic_search 재시도 — 필터 없이 재시도 (3단계에서 결과 없을 때)

    최종 평가:
    - 1개 후보 (confidence >= threshold): resolved=True
    - 2개+ 후보: resolved=False, candidates 반환 (clarification 필요)
    - 0개 후보: unresolved
    """

    def __init__(self) -> None:
        self._persist_dir: Path = CHROMA_PERSIST_DIR
        self._threshold: float = SIMILARITY_THRESHOLD
        self._alias_registry: dict[str, list[str]] = load_alias_registry(_ALIAS_REGISTRY_PATH)
        self._documents: list[dict] = self._load_documents()

    def _load_documents(self) -> list[dict]:
        """ChromaDB document_index 컬렉션에서 전체 문서 메타데이터를 로딩한다."""
        collection_persist_dir = self._persist_dir / "document_index"

        if not collection_persist_dir.exists():
            logger.info(
                "document_index 컬렉션 디렉토리가 없습니다 (ingest 미실행): %s",
                collection_persist_dir,
            )
            return []

        try:
            from langchain_chroma import Chroma
            from langchain_openai import OpenAIEmbeddings

            embeddings = OpenAIEmbeddings()
            vectorstore = Chroma(
                collection_name="document_index",
                persist_directory=str(collection_persist_dir),
                embedding_function=embeddings,
            )
            result = vectorstore.get()
            metadatas: list[dict] = result.get("metadatas") or []
            # None 항목 제거
            return [m for m in metadatas if m is not None]
        except Exception as e:
            logger.warning("document_index 전체 메타데이터 로딩 실패 (graceful 처리): %s", e)
            return []

    def resolve(
        self,
        document_query: str | None,
        domain: str | None = None,
        stack: str | None = None,
    ) -> DocumentResolutionResult:
        """document_query를 resolution하여 DocumentResolutionResult를 반환한다.

        Args:
            document_query: 검색할 문서명 또는 키워드. None이면 즉시 unresolved 반환.
            domain: 도메인 필터 (frontend/backend). None이면 필터 없음.
            stack: 기술 스택 필터. None이면 필터 없음.

        Returns:
            DocumentResolutionResult.
        """
        if document_query is None:
            return DocumentResolutionResult(
                resolved=False,
                resolution_strategy="unresolved",
            )

        # Step 1: exact_match
        exact_candidate = exact_match(document_query, self._documents)
        if exact_candidate is not None and exact_candidate.score >= self._threshold:
            return DocumentResolutionResult(
                resolved=True,
                canonical_doc_id=exact_candidate.canonical_doc_id,
                path=exact_candidate.path,
                title=exact_candidate.title,
                confidence=exact_candidate.score,
                resolution_strategy="exact",
                candidates=[exact_candidate],
            )

        # Step 2: alias_match
        alias_candidate = alias_match(document_query, self._documents, self._alias_registry)
        if alias_candidate is not None and alias_candidate.score >= self._threshold:
            return DocumentResolutionResult(
                resolved=True,
                canonical_doc_id=alias_candidate.canonical_doc_id,
                path=alias_candidate.path,
                title=alias_candidate.title,
                confidence=alias_candidate.score,
                resolution_strategy="alias",
                candidates=[alias_candidate],
            )

        # Step 3: semantic_search (domain/stack 필터 적용)
        semantic_candidates = semantic_search(
            document_query=document_query,
            persist_dir=self._persist_dir,
            domain=domain,
            stack=stack,
            threshold=self._threshold,
        )

        # Step 4: 필터 없이 재시도 (Step 3 결과가 없고 필터가 있었던 경우)
        if not semantic_candidates and (domain is not None or stack is not None):
            logger.info(
                "domain/stack 필터 적용 semantic search 결과 없음. 필터 없이 재시도합니다."
            )
            semantic_candidates = semantic_search(
                document_query=document_query,
                persist_dir=self._persist_dir,
                domain=None,
                stack=None,
                threshold=self._threshold,
            )

        # Step 5: 결과 평가
        return self._evaluate_candidates(semantic_candidates)

    def _evaluate_candidates(
        self, candidates: list[DocumentCandidate]
    ) -> DocumentResolutionResult:
        """semantic search 후보 목록을 평가하여 최종 결과를 반환한다."""
        if not candidates:
            return DocumentResolutionResult(
                resolved=False,
                resolution_strategy="unresolved",
                candidates=[],
            )

        if len(candidates) == 1:
            best = candidates[0]
            return DocumentResolutionResult(
                resolved=True,
                canonical_doc_id=best.canonical_doc_id,
                path=best.path,
                title=best.title,
                confidence=best.score,
                resolution_strategy="semantic",
                candidates=candidates,
            )

        # 2개 이상: 최상위 후보가 임계값을 훨씬 초과하고 2위와 격차가 크면 단독 resolved
        best = candidates[0]
        second = candidates[1]
        score_gap = best.score - second.score

        if best.score >= self._threshold and score_gap >= 0.15:
            return DocumentResolutionResult(
                resolved=True,
                canonical_doc_id=best.canonical_doc_id,
                path=best.path,
                title=best.title,
                confidence=best.score,
                resolution_strategy="semantic",
                candidates=candidates,
            )

        # 복수 후보 — clarification 필요
        return DocumentResolutionResult(
            resolved=False,
            resolution_strategy="semantic",
            confidence=best.score,
            candidates=candidates,
        )
