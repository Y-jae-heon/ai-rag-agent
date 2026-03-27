import os

os.environ["SKIP_INDEX_CHECK"] = "1"

from fastapi.testclient import TestClient

from src.api.dependencies_v4 import get_rag_v4_service
from src.api.main import app
from src.rag_v4.models import Citation, QueryResult, RetrievedDocument, RetrievedSection
from src.rag_v4.service import RagV4Service


class StubService:
    def query(self, question: str, debug: bool = False) -> QueryResult:
        return QueryResult(
            answer=f"answer for {question}",
            citations=[
                Citation(
                    title="문서",
                    source_path="docs/example.md",
                    section_id="doc::section",
                    section_type="rule",
                    excerpt="근거",
                )
            ],
            top_documents=[
                RetrievedDocument(
                    doc_id="doc",
                    title="문서",
                    source_path="docs/example.md",
                    score=0.42,
                    matched_by=["section_dense", "section_sparse"],
                )
            ],
            confidence=0.42,
            needs_clarification=False,
            trace_id="trace-123",
            debug={"normalized_query": {"raw": question}} if debug else None,
        )


def test_query_v4_route_returns_new_response_shape():
    app.dependency_overrides[get_rag_v4_service] = lambda: StubService()
    client = TestClient(app)

    response = client.post("/api/v4/query", json={"question": "FSD 구조 규칙 알려줘", "debug": True})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_id"] == "trace-123"
    assert payload["citations"][0]["section_type"] == "rule"
    assert payload["top_documents"][0]["matched_by"] == ["section_dense", "section_sparse"]


def test_query_v4_route_survives_dense_failures_with_sparse_fallback(monkeypatch):
    class BrokenVectorstore:
        def similarity_search_with_score(self, *_args, **_kwargs):
            raise RuntimeError("dense backend unavailable")

    class StubSparseIndex:
        def search(self, query_text: str, limit: int) -> list[RetrievedSection]:
            assert "프론트엔드" in query_text
            assert limit > 0
            return [
                RetrievedSection(
                    section_id="doc-1::section::0",
                    doc_id="doc-1",
                    title="FSD 레이어드 아키텍처 개요",
                    source_path="docs/fe_chunk_docs/fsd.md",
                    section_type="rule",
                    heading="Rule",
                    content="프론트엔드 FSD 구조는 app, pages, widgets, features, entities, shared 레이어를 따른다.",
                    score=2.0,
                    source="section_sparse",
                    rank=1,
                )
            ]

    from src.rag_v4.retrieval import service as retrieval_service

    monkeypatch.setattr(retrieval_service, "_get_document_vectorstore", lambda: BrokenVectorstore())
    monkeypatch.setattr(retrieval_service, "_get_section_vectorstore", lambda: BrokenVectorstore())
    monkeypatch.setattr(retrieval_service, "_get_sparse_index", lambda: StubSparseIndex())

    service = RagV4Service()
    monkeypatch.setattr(
        service.answer_generator,
        "generate",
        lambda question, sections: "프론트엔드 FSD 구조는 레이어 기반으로 구성됩니다.",
    )

    app.dependency_overrides[get_rag_v4_service] = lambda: service
    client = TestClient(app)

    response = client.post("/api/v4/query", json={"question": "프론트엔드 FSD 구조 알려줘", "debug": True})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "프론트엔드 FSD 구조는 레이어 기반으로 구성됩니다."
    assert payload["top_documents"][0]["matched_by"] == ["section_sparse"]
    assert payload["debug"]["document_dense"] == []
    assert payload["debug"]["section_dense"] == []
    assert payload["debug"]["section_sparse"][0]["doc_id"] == "doc-1"
