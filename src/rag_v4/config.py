"""Configuration for the greenfield RAG v4 pipeline."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

V4_PERSIST_DIR = Path(os.getenv("RAG_V4_PERSIST_DIR", ".chroma_v4"))
CORPUS_DIRS = [
    Path("docs/fe_chunk_docs"),
    Path("docs/be_chunk_docs"),
]

EMBEDDING_MODEL = os.getenv("RAG_V4_EMBEDDING_MODEL", "text-embedding-3-small")
ANSWER_MODEL = os.getenv("RAG_V4_ANSWER_MODEL", "gpt-4o-mini")

SECTION_CHUNK_SIZE = 800
SECTION_CHUNK_OVERLAP = 120

DOCUMENT_DENSE_COLLECTION = "document_dense"
SECTION_DENSE_COLLECTION = "section_dense"
SECTION_SPARSE_DIRNAME = "section_sparse"

DOCUMENT_DENSE_WEIGHT = 0.15
SECTION_DENSE_WEIGHT = 0.50
SECTION_SPARSE_WEIGHT = 0.35
RRF_K = 60

DOCUMENT_TOP_K = 6
SECTION_DENSE_TOP_K = 10
SECTION_SPARSE_TOP_K = 10
TOP_DOCUMENTS_LIMIT = 5
TOP_EVIDENCE_LIMIT = 4

LANGSMITH_PROJECT = os.getenv("LANGCHAIN_PROJECT", "developer-chat-bot-v4")
