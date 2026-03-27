"""Rank fusion helpers for RAG v4."""

from __future__ import annotations

from collections import defaultdict

from src.rag_v4.models import RetrievedDocument, RetrievedSection


def weighted_rrf(rankings: dict[str, list[str]], weights: dict[str, float], k: int) -> dict[str, float]:
    """Compute weighted reciprocal-rank-fusion scores."""
    scores: dict[str, float] = defaultdict(float)
    for source_name, keys in rankings.items():
        weight = weights.get(source_name, 0.0)
        for rank_index, key in enumerate(keys, start=1):
            scores[key] += weight / (k + rank_index)
    return dict(scores)


def fuse_documents(
    document_results: list[RetrievedDocument],
    dense_sections: list[RetrievedSection],
    sparse_sections: list[RetrievedSection],
    *,
    document_weight: float,
    section_dense_weight: float,
    section_sparse_weight: float,
    rrf_k: int,
) -> list[RetrievedDocument]:
    """Fuse document and section retrieval outputs at the document level."""
    document_by_id = {doc.doc_id: doc for doc in document_results}
    doc_dense_ranks = [doc.doc_id for doc in document_results]
    section_dense_ranks = _distinct_doc_ids(dense_sections)
    section_sparse_ranks = _distinct_doc_ids(sparse_sections)

    scores = weighted_rrf(
        {
            "document_dense": doc_dense_ranks,
            "section_dense": section_dense_ranks,
            "section_sparse": section_sparse_ranks,
        },
        {
            "document_dense": document_weight,
            "section_dense": section_dense_weight,
            "section_sparse": section_sparse_weight,
        },
        rrf_k,
    )

    for section in dense_sections + sparse_sections:
        document_by_id.setdefault(
            section.doc_id,
            RetrievedDocument(
                doc_id=section.doc_id,
                title=section.title,
                source_path=section.source_path,
                score=0.0,
                matched_by=[],
            ),
        )

    for doc_id, document in document_by_id.items():
        matched_by: list[str] = []
        if doc_id in doc_dense_ranks:
            matched_by.append("document_dense")
        if doc_id in section_dense_ranks:
            matched_by.append("section_dense")
        if doc_id in section_sparse_ranks:
            matched_by.append("section_sparse")
        document.score = scores.get(doc_id, 0.0)
        document.matched_by = matched_by

    fused = sorted(document_by_id.values(), key=lambda doc: doc.score, reverse=True)
    return fused


def rank_sections(
    dense_sections: list[RetrievedSection],
    sparse_sections: list[RetrievedSection],
    document_scores: dict[str, float],
    *,
    section_dense_weight: float,
    section_sparse_weight: float,
    rrf_k: int,
) -> list[RetrievedSection]:
    """Rank evidence sections after document-level fusion."""
    rankings = {
        "section_dense": [section.section_id for section in dense_sections],
        "section_sparse": [section.section_id for section in sparse_sections],
    }
    scores = weighted_rrf(
        rankings,
        {
            "section_dense": section_dense_weight,
            "section_sparse": section_sparse_weight,
        },
        rrf_k,
    )

    sections_by_id: dict[str, RetrievedSection] = {}
    for section in dense_sections + sparse_sections:
        section_score = scores.get(section.section_id, 0.0) + (document_scores.get(section.doc_id, 0.0) * 0.15)
        existing = sections_by_id.get(section.section_id)
        if existing is None or section_score > existing.score:
            section.score = section_score
            sections_by_id[section.section_id] = section

    return sorted(sections_by_id.values(), key=lambda section: section.score, reverse=True)


def _distinct_doc_ids(sections: list[RetrievedSection]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for section in sections:
        if section.doc_id not in seen:
            seen.add(section.doc_id)
            ordered.append(section.doc_id)
    return ordered

