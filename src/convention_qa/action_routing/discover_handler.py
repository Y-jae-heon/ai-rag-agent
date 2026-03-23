"""DiscoverHandler — 문서 발견 결과를 deterministic 포맷으로 반환하는 핸들러."""

from __future__ import annotations

import logging

from src.convention_qa.action_routing.base_handler import (
    BaseHandler,
    HandlerContext,
    HandlerResult,
)

logger = logging.getLogger(__name__)


class DiscoverHandler(BaseHandler):
    """문서 발견 결과를 LLM 없이 구조화된 포맷으로 반환하는 핸들러.

    resolved=True: 단일 문서 메타데이터 + 섹션 목록 반환.
    resolved=False: 복수 후보 clarify 메시지 반환.
    """

    def handle(self, context: HandlerContext) -> HandlerResult:
        from src.convention_qa.response.formatters import format_clarify, format_discover

        resolution = context.resolution

        if resolution.resolved:
            canonical_doc_id = resolution.canonical_doc_id or ""
            title = resolution.title or ""
            path = resolution.path or ""

            candidate = (resolution.candidates or [None])[0]
            domain = getattr(candidate, "domain", None) if candidate else None
            stack = getattr(candidate, "stack", None) if candidate else None

            section_headings = self._get_section_headings(canonical_doc_id)

            answer = format_discover(
                title=title,
                path=path,
                domain=domain,
                stack=stack,
                section_headings=section_headings,
            )
            return HandlerResult(
                answer=answer,
                answer_type="discover",
                sources=[{"path": path, "title": title}],
                resolved_document={
                    "canonical_doc_id": canonical_doc_id,
                    "title": title,
                    "path": path,
                },
            )
        else:
            candidates_data = [
                {"title": getattr(c, "title", str(c)), "domain": getattr(c, "domain", None)}
                for c in (resolution.candidates or [])
            ]
            answer = format_clarify(candidates_data, context.question)
            return HandlerResult(
                answer=answer,
                answer_type="clarify",
                sources=[],
            )

    def _get_section_headings(self, canonical_doc_id: str) -> list[str]:
        """section_index에서 canonical_doc_id에 해당하는 섹션 헤딩 목록을 가져온다."""
        if not canonical_doc_id:
            return []
        try:
            from langchain_chroma import Chroma
            from langchain_openai import OpenAIEmbeddings

            from src.convention_qa.indexing.config import (
                CHROMA_PERSIST_DIR,
                OPENAI_EMBEDDING_MODEL,
            )

            collection_dir = str(CHROMA_PERSIST_DIR / "section_index")
            embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
            vectorstore = Chroma(
                collection_name="section_index",
                persist_directory=collection_dir,
                embedding_function=embeddings,
            )
            result = vectorstore.get(where={"canonical_doc_id": canonical_doc_id})
            metadatas = result.get("metadatas") or []
            return [m.get("section_heading", "") for m in metadatas if m.get("section_heading")]
        except Exception as e:
            logger.warning("section_index 섹션 헤딩 조회 실패 (graceful 처리): %s", e)
            return []
