"""ExtractHandler — chunk_index MMR 검색 기반 QA 핸들러."""

from __future__ import annotations

import logging

from src.convention_qa.action_routing.base_handler import (
    BaseHandler,
    HandlerContext,
    HandlerResult,
)

logger = logging.getLogger(__name__)

EXTRACT_SYSTEM = (
    "당신은 개발 컨벤션 전문가입니다. "
    "주어진 컨텍스트를 기반으로 질문에 정확하고 간결하게 답변하세요. "
    "컨텍스트에 없는 내용은 추측하지 마세요."
)

EXTRACT_HUMAN = (
    "컨텍스트:\n{chunks_text}\n\n"
    "질문: {question}\n\n"
    "위 컨텍스트를 바탕으로 질문에 답변해주세요."
)


class ExtractHandler(BaseHandler):
    """chunk_index MMR 검색으로 관련 청크를 찾고 LLM으로 QA 답변을 생성하는 핸들러."""

    def handle(self, context: HandlerContext) -> HandlerResult:
        from src.convention_qa.response.formatters import format_extract, format_not_found

        resolution = context.resolution
        canonical_doc_id = resolution.canonical_doc_id or ""
        title = resolution.title or ""
        path = resolution.path or ""

        chunks = self._mmr_search(context.question, canonical_doc_id)

        if not chunks:
            answer = format_not_found(title or None)
            return HandlerResult(answer=answer, answer_type="not_found", sources=[])

        chunks_text = "\n\n---\n\n".join(c["content"] for c in chunks)
        answer_text = self._extract_answer(context.question, chunks_text)
        source_sections = [c["heading"] for c in chunks if c.get("heading")]
        answer = format_extract(title, answer_text, source_sections, path)

        return HandlerResult(
            answer=answer,
            answer_type="extract",
            sources=[{"path": path, "title": title}],
            resolved_document={
                "canonical_doc_id": canonical_doc_id,
                "title": title,
                "path": path,
            },
        )

    def _mmr_search(self, question: str, canonical_doc_id: str) -> list[dict]:
        """chunk_index에서 MMR로 관련 청크를 검색한다."""
        if not canonical_doc_id:
            return []
        try:
            from langchain_chroma import Chroma
            from langchain_openai import OpenAIEmbeddings

            from src.convention_qa.indexing.config import (
                CHROMA_PERSIST_DIR,
                OPENAI_EMBEDDING_MODEL,
            )

            collection_dir = str(CHROMA_PERSIST_DIR / "chunk_index")
            embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
            vectorstore = Chroma(
                collection_name="chunk_index",
                persist_directory=collection_dir,
                embedding_function=embeddings,
            )
            print(f"[ChromaDB] max_marginal_relevance_search() 호출 — canonical_doc_id={canonical_doc_id}, k=4, fetch_k=20, question={question!r}")
            docs = vectorstore.max_marginal_relevance_search(
                question,
                k=4,
                fetch_k=20,
                filter={"canonical_doc_id": canonical_doc_id},
            )
            print(f"[ChromaDB] max_marginal_relevance_search() 완료 — 청크 수={len(docs)}")
            chunks = [
                {
                    "content": doc.page_content,
                    "heading": doc.metadata.get("section_heading", ""),
                }
                for doc in docs
            ]
            logger.info(
                "[ExtractHandler._mmr_search] canonical_doc_id=%s | 질문=%r | 청크 %d건 반환",
                canonical_doc_id,
                question,
                len(chunks),
            )
            for i, chunk in enumerate(chunks):
                logger.info("  [%d] heading=%r  content_len=%d", i + 1, chunk["heading"], len(chunk["content"]))
            return chunks
        except Exception as e:
            logger.warning("chunk_index MMR 검색 실패 (graceful 처리): %s", e)
            return []

    def _extract_answer(self, question: str, chunks_text: str) -> str:
        """LLM을 이용해 청크 컨텍스트 기반 QA 답변을 생성한다."""
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI

            prompt = ChatPromptTemplate.from_messages([
                ("system", EXTRACT_SYSTEM),
                ("human", EXTRACT_HUMAN),
            ])
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            chain = prompt | llm
            result = chain.invoke({"chunks_text": chunks_text, "question": question})
            return result.content
        except Exception as e:
            logger.warning("QA LLM 호출 실패: %s", e)
            return "답변을 생성할 수 없습니다. 잠시 후 다시 시도해주세요."
