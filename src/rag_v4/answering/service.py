"""Answer generation for RAG v4."""

from __future__ import annotations

import logging

from langsmith import traceable

from src.rag_v4 import config
from src.rag_v4.models import Citation, RetrievedSection

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "당신은 사내 개발 컨벤션 질의응답 도우미다. "
    "주어진 근거 섹션만 사용해 답변하고, 모르는 내용은 추측하지 마라. "
    "답변은 한국어로 작성하고 핵심 규칙 위주로 간결하게 정리하라."
)

HUMAN_PROMPT = (
    "질문:\n{question}\n\n"
    "근거 섹션:\n{context}\n\n"
    "위 근거만 사용해 답변해라. 근거가 직접 말하지 않는 내용은 추가하지 마라."
)


class AnswerGenerator:
    """Generate grounded answers from the top evidence sections."""

    @traceable(name="rag_v4.answer")
    def generate(self, question: str, sections: list[RetrievedSection]) -> str:
        if not sections:
            return "관련 근거를 찾지 못했습니다. 질문 표현을 조금 더 구체적으로 바꿔주세요."

        context = "\n\n---\n\n".join(
            f"[{index}] {section.title} / {section.section_type}\n{section.content}"
            for index, section in enumerate(sections, start=1)
        )
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", SYSTEM_PROMPT),
                    ("human", HUMAN_PROMPT),
                ]
            )
            llm = ChatOpenAI(model=config.ANSWER_MODEL, temperature=0)
            chain = prompt | llm
            result = chain.invoke({"question": question, "context": context})
            return result.content.strip()
        except Exception as exc:
            logger.warning("Falling back to deterministic answer due to LLM failure: %s", exc)
            bullet_lines = [
                f"- {section.title} / {section.section_type}: {section.content.splitlines()[0][:140]}"
                for section in sections
            ]
            return "\n".join(bullet_lines)

    @traceable(name="rag_v4.format_response")
    def build_citations(self, sections: list[RetrievedSection]) -> list[Citation]:
        citations: list[Citation] = []
        for section in sections:
            excerpt = " ".join(section.content.split())[:240]
            citations.append(
                Citation(
                    title=section.title,
                    source_path=section.source_path,
                    section_id=section.section_id,
                    section_type=section.section_type,
                    excerpt=excerpt,
                )
            )
        return citations

