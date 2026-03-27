"""Singleton dependencies for the RAG v4 API layer."""

from __future__ import annotations

from functools import lru_cache

from src.rag_v4.retrieval.service import ensure_v4_indices_exist
from src.rag_v4.service import RagV4Service


@lru_cache(maxsize=1)
def get_rag_v4_service() -> RagV4Service:
    return RagV4Service()


def check_v4_indices() -> None:
    ensure_v4_indices_exist()

