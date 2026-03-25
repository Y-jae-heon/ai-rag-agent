"""SummarizeHandler — section_index 기반 문서 요약 핸들러."""

from __future__ import annotations

import logging

from src.convention_qa.action_routing.base_handler import (
    BaseHandler,
    HandlerContext,
    HandlerResult,
)

logger = logging.getLogger(__name__)

SUMMARIZE_SYSTEM = (
    "당신은 개발 컨벤션 전문가입니다. "
    "주어진 문서의 섹션들을 분석하여 핵심 규칙을 3~6개 항목으로 요약하세요. "
    "각 항목은 명확하고 실용적인 규칙 형태로 작성하세요."
)

SUMMARIZE_HUMAN = (
    "문서: {title}\n\n"
    "섹션 내용:\n{sections_text}\n\n"
    "위 문서의 핵심 규칙을 3~6개 항목으로 요약해주세요. "
    "번호 목록 형식(1. 2. 3. ...)으로 작성하고, 각 항목은 굵은 글씨 제목과 간략한 설명을 포함하세요."
)


class SummarizeHandler(BaseHandler):
    """section_index에서 섹션을 수집하고 LLM으로 요약하는 핸들러.

    section_index를 canonical_doc_id로 필터링하여 전체 섹션을 가져온 뒤,
    gpt-4o-mini LLM에 전달하여 3~6개 핵심 항목 요약을 생성한다.
    """

    def handle(self, context: HandlerContext) -> HandlerResult:
        from src.convention_qa.response.formatters import format_summarize

        resolution = context.resolution
        canonical_doc_id = resolution.canonical_doc_id or ""
        title = resolution.title or ""
        path = resolution.path or ""

        sections = self._get_sections(canonical_doc_id)

        if sections:
            sections_text = "\n\n".join(
                f"### {s['heading']}\n{s['content']}" if s["content"] else f"### {s['heading']}"
                for s in sections
            )
        else:
            sections_text = "(섹션 데이터 없음)"

        summary = self._summarize(title, sections_text)
        answer = format_summarize(title, summary, path)

        return HandlerResult(
            answer=answer,
            answer_type="summary",
            sources=[{"path": path, "title": title}],
            resolved_document={
                "canonical_doc_id": canonical_doc_id,
                "title": title,
                "path": path,
            },
        )

    def _get_sections(self, canonical_doc_id: str) -> list[dict]:
        """section_index에서 canonical_doc_id에 해당하는 섹션을 가져온다."""
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

            sections: list[dict] = []
            docs = result.get("documents") or []
            metadatas = result.get("metadatas") or []
            for i, doc_text in enumerate(docs):
                metadata = metadatas[i] if i < len(metadatas) else {}
                heading = metadata.get("section_heading", "")
                content = doc_text.replace(heading, "", 1).strip() if heading else doc_text
                sections.append({"heading": heading, "content": content})

            logger.info(
                "[SummarizeHandler._get_sections] canonical_doc_id=%s | 섹션 %d건 반환",
                canonical_doc_id,
                len(sections),
            )
            for i, s in enumerate(sections):
                logger.info("  [%d] heading=%r  content_len=%d", i + 1, s["heading"], len(s["content"]))
            return sections
        except Exception as e:
            logger.warning("section_index 조회 실패 (graceful 처리): %s", e)
            return []

    def _summarize(self, title: str, sections_text: str) -> str:
        """LLM을 이용해 섹션 텍스트를 요약한다."""
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI

            prompt = ChatPromptTemplate.from_messages([
                ("system", SUMMARIZE_SYSTEM),
                ("human", SUMMARIZE_HUMAN),
            ])
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            chain = prompt | llm
            result = chain.invoke({"title": title, "sections_text": sections_text})
            return result.content
        except Exception as e:
            logger.warning("요약 LLM 호출 실패: %s", e)
            return "요약을 생성할 수 없습니다. 잠시 후 다시 시도해주세요."
