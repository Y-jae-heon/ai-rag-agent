"""Top-level query service for RAG v4."""

from __future__ import annotations

from langsmith.run_helpers import trace

from src.rag_v4 import config
from src.rag_v4.answering.service import AnswerGenerator
from src.rag_v4.models import QueryResult
from src.rag_v4.normalization import normalize_query
from src.rag_v4.retrieval.service import HybridRetriever


class RagV4Service:
    """Coordinate normalization, retrieval, answer generation, and tracing."""

    def __init__(self) -> None:
        self.retriever = HybridRetriever()
        self.answer_generator = AnswerGenerator()

    def query(self, question: str, debug: bool = False) -> QueryResult:
        with trace(
            "rag_v4.query",
            run_type="chain",
            inputs={"question": question, "debug": debug},
            project_name=config.LANGSMITH_PROJECT,
        ) as run:
            normalized = normalize_query(question)
            top_documents, evidence_sections, retrieval_debug = self.retriever.retrieve(normalized)

            citations = self.answer_generator.build_citations(evidence_sections)
            answer = self.answer_generator.generate(question, evidence_sections)

            confidence = top_documents[0].score if top_documents else 0.0
            needs_clarification = not bool(citations)
            response_debug = None
            if debug:
                response_debug = {
                    "normalized_query": normalized.model_dump(),
                    **retrieval_debug,
                }

            result = QueryResult(
                answer=answer,
                citations=citations,
                top_documents=top_documents,
                confidence=confidence,
                needs_clarification=needs_clarification,
                trace_id=str(run.id),
                debug=response_debug,
            )
            run.end(outputs=result.model_dump())
            return result
