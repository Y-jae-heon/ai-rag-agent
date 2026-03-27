"""Hybrid retrieval for RAG v4."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from langsmith import traceable

from src.rag_v4 import config
from src.rag_v4.models import NormalizedQuery, RetrievedDocument, RetrievedSection
from src.rag_v4.retrieval.fusion import fuse_documents, rank_sections
from src.rag_v4.retrieval.sparse_index import SparseSectionIndex

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_document_vectorstore():
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings

    return Chroma(
        collection_name=config.DOCUMENT_DENSE_COLLECTION,
        persist_directory=str(config.V4_PERSIST_DIR / config.DOCUMENT_DENSE_COLLECTION),
        embedding_function=OpenAIEmbeddings(model=config.EMBEDDING_MODEL),
    )


@lru_cache(maxsize=1)
def _get_section_vectorstore():
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings

    return Chroma(
        collection_name=config.SECTION_DENSE_COLLECTION,
        persist_directory=str(config.V4_PERSIST_DIR / config.SECTION_DENSE_COLLECTION),
        embedding_function=OpenAIEmbeddings(model=config.EMBEDDING_MODEL),
    )


@lru_cache(maxsize=1)
def _get_sparse_index() -> SparseSectionIndex:
    index_path = config.V4_PERSIST_DIR / config.SECTION_SPARSE_DIRNAME / "index.json"
    return SparseSectionIndex(index_path=index_path)


class HybridRetriever:
    """Dense + sparse hybrid retrieval with Python-side RRF fusion."""

    @traceable(name="rag_v4.retrieve_dense_doc")
    def retrieve_dense_documents(self, normalized_query: NormalizedQuery) -> list[RetrievedDocument]:
        try:
            vectorstore = _get_document_vectorstore()
            results = vectorstore.similarity_search_with_score(
                normalized_query.retrieval_text,
                k=config.DOCUMENT_TOP_K,
            )
        except Exception as exc:
            logger.warning("document_dense retrieval failed, falling back to remaining retrievers: %s", exc)
            return []
        documents: list[RetrievedDocument] = []
        for doc, distance in results:
            metadata = doc.metadata or {}
            documents.append(
                RetrievedDocument(
                    doc_id=metadata.get("doc_id", ""),
                    title=metadata.get("title", ""),
                    source_path=metadata.get("source_path", ""),
                    score=1.0 / (1.0 + distance),
                    matched_by=["document_dense"],
                )
            )
        return documents

    @traceable(name="rag_v4.retrieve_dense_section")
    def retrieve_dense_sections(self, normalized_query: NormalizedQuery) -> list[RetrievedSection]:
        try:
            vectorstore = _get_section_vectorstore()
            results = vectorstore.similarity_search_with_score(
                normalized_query.retrieval_text,
                k=config.SECTION_DENSE_TOP_K,
            )
        except Exception as exc:
            logger.warning("section_dense retrieval failed, falling back to remaining retrievers: %s", exc)
            return []
        sections: list[RetrievedSection] = []
        for rank_index, (doc, distance) in enumerate(results, start=1):
            metadata = doc.metadata or {}
            sections.append(
                RetrievedSection(
                    section_id=metadata.get("section_id", ""),
                    doc_id=metadata.get("doc_id", ""),
                    title=metadata.get("title", ""),
                    source_path=metadata.get("source_path", ""),
                    section_type=metadata.get("section_type", "body"),
                    heading=metadata.get("heading", ""),
                    content=metadata.get("content", ""),
                    score=1.0 / (1.0 + distance),
                    source="section_dense",
                    rank=rank_index,
                )
            )
        return sections

    @traceable(name="rag_v4.retrieve_sparse_section")
    def retrieve_sparse_sections(self, normalized_query: NormalizedQuery) -> list[RetrievedSection]:
        try:
            return _get_sparse_index().search(
                query_text=normalized_query.retrieval_text,
                limit=config.SECTION_SPARSE_TOP_K,
            )
        except Exception as exc:
            logger.warning("section_sparse retrieval failed: %s", exc)
            return []

    @traceable(name="rag_v4.fuse")
    def retrieve(self, normalized_query: NormalizedQuery) -> tuple[list[RetrievedDocument], list[RetrievedSection], dict]:
        document_results = self.retrieve_dense_documents(normalized_query)
        dense_sections = self.retrieve_dense_sections(normalized_query)
        sparse_sections = self.retrieve_sparse_sections(normalized_query)

        fused_docs = fuse_documents(
            document_results,
            dense_sections,
            sparse_sections,
            document_weight=config.DOCUMENT_DENSE_WEIGHT,
            section_dense_weight=config.SECTION_DENSE_WEIGHT,
            section_sparse_weight=config.SECTION_SPARSE_WEIGHT,
            rrf_k=config.RRF_K,
        )
        fused_docs = fused_docs[: config.TOP_DOCUMENTS_LIMIT]
        doc_scores = {doc.doc_id: doc.score for doc in fused_docs}

        fused_sections = rank_sections(
            dense_sections,
            sparse_sections,
            doc_scores,
            section_dense_weight=config.SECTION_DENSE_WEIGHT,
            section_sparse_weight=config.SECTION_SPARSE_WEIGHT,
            rrf_k=config.RRF_K,
        )
        filtered_sections = [section for section in fused_sections if section.doc_id in doc_scores]
        filtered_sections = filtered_sections[: config.TOP_EVIDENCE_LIMIT]

        debug = {
            "document_dense": [doc.model_dump() for doc in document_results],
            "section_dense": [section.model_dump() for section in dense_sections],
            "section_sparse": [section.model_dump() for section in sparse_sections],
            "fused_documents": [doc.model_dump() for doc in fused_docs],
            "fused_sections": [section.model_dump() for section in filtered_sections],
        }
        return fused_docs, filtered_sections, debug


def ensure_v4_indices_exist() -> None:
    """Raise if the required v4 indices are missing."""
    required_paths = [
        config.V4_PERSIST_DIR / config.DOCUMENT_DENSE_COLLECTION,
        config.V4_PERSIST_DIR / config.SECTION_DENSE_COLLECTION,
        config.V4_PERSIST_DIR / config.SECTION_SPARSE_DIRNAME / "index.json",
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise RuntimeError(
            "RAG v4 index is missing. Run: python scripts/ingest_v4.py"
        )
