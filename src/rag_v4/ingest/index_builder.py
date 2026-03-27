"""Index builder for the greenfield RAG v4 pipeline."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag_v4 import config
from src.rag_v4.ingest.parser import parse_markdown_file
from src.rag_v4.models import ParsedDocument, SectionRecord
from src.rag_v4.normalization import build_retrieval_text
from src.rag_v4.retrieval.sparse_index import SparseSectionIndex

_ALL_COLLECTIONS = [
    config.DOCUMENT_DENSE_COLLECTION,
    config.SECTION_DENSE_COLLECTION,
    config.SECTION_SPARSE_DIRNAME,
]


def build_indices(force_rebuild: bool = False, collections: list[str] | None = None) -> dict[str, int]:
    """Build the v4 retrieval indices."""
    persist_dir = config.V4_PERSIST_DIR
    if force_rebuild and persist_dir.exists():
        shutil.rmtree(persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    target = set(collections or _ALL_COLLECTIONS)
    invalid = target - set(_ALL_COLLECTIONS)
    if invalid:
        raise ValueError(f"Unknown collections: {sorted(invalid)}")

    parsed_docs = _load_documents()
    section_records = _build_section_records(parsed_docs)
    counts: dict[str, int] = {}

    if config.DOCUMENT_DENSE_COLLECTION in target:
        counts[config.DOCUMENT_DENSE_COLLECTION] = _build_document_dense(parsed_docs, persist_dir)
    if config.SECTION_DENSE_COLLECTION in target:
        counts[config.SECTION_DENSE_COLLECTION] = _build_section_dense(section_records, persist_dir)
    if config.SECTION_SPARSE_DIRNAME in target:
        sparse_index = SparseSectionIndex(
            persist_dir / config.SECTION_SPARSE_DIRNAME / "index.json"
        )
        counts[config.SECTION_SPARSE_DIRNAME] = sparse_index.build(section_records)

    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "document_count": len(parsed_docs),
        "section_count": len(section_records),
        "collections": counts,
        "embedding_model": config.EMBEDDING_MODEL,
    }
    manifest_path = persist_dir / "ingest_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return counts


def _load_documents() -> list[ParsedDocument]:
    parsed_docs: list[ParsedDocument] = []
    for corpus_dir in config.CORPUS_DIRS:
        if not corpus_dir.exists():
            continue
        for file_path in sorted(corpus_dir.glob("*.md")):
            parsed_docs.append(parse_markdown_file(file_path))
    return parsed_docs


def _build_section_records(parsed_docs: list[ParsedDocument]) -> list[SectionRecord]:
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=config.SECTION_CHUNK_SIZE,
        chunk_overlap=config.SECTION_CHUNK_OVERLAP,
    )

    records: list[SectionRecord] = []
    for doc in parsed_docs:
        for section in doc.sections:
            section_body = section.content.strip()
            chunks = splitter.split_text(section_body) if section_body else [""]
            for chunk_index, chunk in enumerate(chunks):
                section_id = (
                    section.section_id
                    if len(chunks) == 1
                    else f"{section.section_id}::chunk::{chunk_index}"
                )
                content = chunk.strip() if chunk else section_body
                index_text = build_retrieval_text(
                    doc.title,
                    section.section_type,
                    section.heading,
                    content,
                )
                records.append(
                    SectionRecord(
                        section_id=section_id,
                        doc_id=doc.doc_id,
                        title=doc.title,
                        source_path=doc.source_path,
                        section_type=section.section_type,
                        heading=section.heading,
                        content=content,
                        index_text=index_text,
                    )
                )
    return records


def _build_document_dense(parsed_docs: list[ParsedDocument], persist_dir: Path) -> int:
    embeddings = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
    collection_dir = persist_dir / config.DOCUMENT_DENSE_COLLECTION
    documents: list[Document] = []
    for doc in parsed_docs:
        headings = " ".join(section.heading for section in doc.sections)
        snippets = "\n".join(section.content[:240] for section in doc.sections[:4])
        page_content = build_retrieval_text(doc.title, headings, snippets)
        documents.append(
            Document(
                page_content=page_content,
                metadata={
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "source_path": doc.source_path,
                },
            )
        )
    if documents:
        Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            collection_name=config.DOCUMENT_DENSE_COLLECTION,
            persist_directory=str(collection_dir),
        )
    return len(documents)


def _build_section_dense(section_records: list[SectionRecord], persist_dir: Path) -> int:
    embeddings = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
    collection_dir = persist_dir / config.SECTION_DENSE_COLLECTION
    documents: list[Document] = []
    for record in section_records:
        documents.append(
            Document(
                page_content=record.index_text,
                metadata={
                    "section_id": record.section_id,
                    "doc_id": record.doc_id,
                    "title": record.title,
                    "source_path": record.source_path,
                    "section_type": record.section_type,
                    "heading": record.heading,
                    "content": record.content,
                },
            )
        )
    if documents:
        Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            collection_name=config.SECTION_DENSE_COLLECTION,
            persist_directory=str(collection_dir),
        )
    return len(documents)

