from src.rag_v4.models import RetrievedDocument, RetrievedSection
from src.rag_v4.retrieval.fusion import fuse_documents
from src.rag_v4.retrieval.service import HybridRetriever
from src.rag_v4.normalization import normalize_query


def _section(section_id: str, doc_id: str, title: str, source: str, rank: int) -> RetrievedSection:
    return RetrievedSection(
        section_id=section_id,
        doc_id=doc_id,
        title=title,
        source_path=f"docs/{title}.md",
        section_type="rule",
        heading="Rule",
        content="내용",
        score=1.0,
        source=source,
        rank=rank,
    )


def test_fuse_documents_prefers_docs_supported_by_dense_and_sparse_sections():
    documents = [
        RetrievedDocument(doc_id="doc-a", title="A", source_path="docs/a.md", score=0.9, matched_by=["document_dense"]),
        RetrievedDocument(doc_id="doc-b", title="B", source_path="docs/b.md", score=0.8, matched_by=["document_dense"]),
    ]
    dense_sections = [
        _section("a-1", "doc-a", "A", "section_dense", 1),
        _section("b-1", "doc-b", "B", "section_dense", 2),
    ]
    sparse_sections = [
        _section("b-2", "doc-b", "B", "section_sparse", 1),
        _section("a-2", "doc-a", "A", "section_sparse", 2),
    ]

    fused = fuse_documents(
        documents,
        dense_sections,
        sparse_sections,
        document_weight=0.15,
        section_dense_weight=0.50,
        section_sparse_weight=0.35,
        rrf_k=60,
    )

    assert fused[0].doc_id == "doc-a"
    assert set(fused[0].matched_by) == {"document_dense", "section_dense", "section_sparse"}


def test_hybrid_retriever_survives_dense_failures(monkeypatch):
    retriever = HybridRetriever()

    monkeypatch.setattr(
        retriever,
        "retrieve_dense_documents",
        lambda normalized_query: [],
    )
    monkeypatch.setattr(
        retriever,
        "retrieve_dense_sections",
        lambda normalized_query: [],
    )
    monkeypatch.setattr(
        retriever,
        "retrieve_sparse_sections",
        lambda normalized_query: [
            RetrievedSection(
                section_id="doc-1::rule",
                doc_id="doc-1",
                title="FSD 레이어드 아키텍처 개요",
                source_path="docs/fsd-overview.md",
                section_type="rule",
                heading="Rule",
                content="FSD 구조 규칙",
                score=1.0,
                source="section_sparse",
                rank=1,
            )
        ],
    )

    documents, sections, debug = retriever.retrieve(normalize_query("프론트엔드 FSD 구조 알려줘"))

    assert documents
    assert sections
    assert debug["section_sparse"][0]["doc_id"] == "doc-1"
