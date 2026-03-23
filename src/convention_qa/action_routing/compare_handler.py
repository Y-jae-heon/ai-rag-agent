"""CompareHandler — 두 문서 비교 핸들러."""

from __future__ import annotations

import logging

from src.convention_qa.action_routing.base_handler import BaseHandler, HandlerContext, HandlerResult

logger = logging.getLogger(__name__)

COMPARE_SYSTEM = (
    "당신은 개발 컨벤션 전문가입니다. "
    "두 문서의 규칙을 비교하여 공통점, 차이점, 충돌 지점을 명확하게 분석해주세요."
)

COMPARE_HUMAN = (
    "문서 A — {title_a}:\n{sections_a}\n\n"
    "문서 B — {title_b}:\n{sections_b}\n\n"
    "질문: {question}\n\n"
    "두 문서를 비교하여 공통점, 차이점, 충돌 지점을 분석해주세요. "
    "가능하면 표나 항목 목록 형식으로 명확하게 정리해주세요."
)


class CompareHandler(BaseHandler):
    """두 문서를 각각 resolution하고 LLM으로 비교 분석하는 핸들러."""

    def handle(self, context: HandlerContext) -> HandlerResult:
        from src.convention_qa.response.formatters import format_compare, format_not_found

        understanding = context.understanding
        document_queries = getattr(understanding, "document_queries", None) if understanding else None

        if not document_queries or len(document_queries) < 2:
            answer = format_not_found(None)
            return HandlerResult(answer=answer, answer_type="not_found", sources=[])

        query_a, query_b = document_queries[0], document_queries[1]

        resolution_a = self._resolve(query_a, understanding)
        resolution_b = self._resolve(query_b, understanding)

        title_a = (resolution_a.title or query_a) if resolution_a else query_a
        title_b = (resolution_b.title or query_b) if resolution_b else query_b
        path_a = (resolution_a.path or "") if resolution_a else ""
        path_b = (resolution_b.path or "") if resolution_b else ""
        canonical_a = (resolution_a.canonical_doc_id or "") if resolution_a else ""
        canonical_b = (resolution_b.canonical_doc_id or "") if resolution_b else ""

        sections_a = self._get_sections(canonical_a)
        sections_b = self._get_sections(canonical_b)

        sections_text_a = self._format_sections(sections_a)
        sections_text_b = self._format_sections(sections_b)

        comparison_text = self._compare(
            title_a=title_a,
            title_b=title_b,
            sections_a=sections_text_a,
            sections_b=sections_text_b,
            question=context.question,
        )

        answer = format_compare(title_a, title_b, comparison_text, path_a, path_b)

        return HandlerResult(
            answer=answer,
            answer_type="compare",
            sources=[
                {"path": path_a, "title": title_a},
                {"path": path_b, "title": title_b},
            ],
        )

    def _resolve(self, document_query: str, understanding: object):
        """document_query를 DocumentResolver로 resolution한다."""
        try:
            from src.convention_qa.document_resolution.resolver import DocumentResolver

            domain = getattr(understanding, "domain", None)
            stack = getattr(understanding, "stack", None)
            resolver = DocumentResolver()
            return resolver.resolve(document_query, domain=domain, stack=stack)
        except Exception as e:
            logger.warning("DocumentResolver 호출 실패 (graceful 처리): %s", e)
            return None

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
            return sections
        except Exception as e:
            logger.warning("section_index 조회 실패 (graceful 처리): %s", e)
            return []

    def _format_sections(self, sections: list[dict]) -> str:
        """섹션 목록을 LLM 입력용 텍스트로 변환한다."""
        if not sections:
            return "(섹션 데이터 없음)"
        return "\n\n".join(
            f"### {s['heading']}\n{s['content']}" if s["content"] else f"### {s['heading']}"
            for s in sections
        )

    def _compare(
        self,
        title_a: str,
        title_b: str,
        sections_a: str,
        sections_b: str,
        question: str,
    ) -> str:
        """LLM을 이용해 두 문서의 비교 분석을 생성한다."""
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI

            prompt = ChatPromptTemplate.from_messages([
                ("system", COMPARE_SYSTEM),
                ("human", COMPARE_HUMAN),
            ])
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            chain = prompt | llm
            result = chain.invoke({
                "title_a": title_a,
                "title_b": title_b,
                "sections_a": sections_a,
                "sections_b": sections_b,
                "question": question,
            })
            return result.content
        except Exception as e:
            logger.warning("비교 LLM 호출 실패: %s", e)
            return "비교 분석을 생성할 수 없습니다. 잠시 후 다시 시도해주세요."
