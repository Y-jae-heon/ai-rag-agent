"""Local BM25-style sparse index built with Chroma tokenizer semantics."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from chromadb.utils.embedding_functions import ChromaBm25EmbeddingFunction
from chromadb.utils.embedding_functions.schemas.bm25_tokenizer import (
    Bm25Tokenizer,
    get_english_stemmer,
)

from src.rag_v4.models import RetrievedSection, SectionRecord


class SparseSectionIndex:
    """Persisted local sparse index using Chroma's BM25 tokenization semantics.

    Local Chroma 1.5.x exposes sparse search APIs but does not execute them for
    local collections. This index keeps the Chroma BM25 tokenizer/config and
    performs the final ranking in Python.
    """

    def __init__(self, index_path: Path) -> None:
        self.index_path = index_path
        self._bm25 = ChromaBm25EmbeddingFunction()
        self._tokenizer = Bm25Tokenizer(
            get_english_stemmer(),
            self._bm25._stopword_list,
            self._bm25.token_max_length,
        )

    def build(self, records: list[SectionRecord]) -> int:
        total_docs = len(records)
        avg_doc_length = (
            sum(len(self._tokenizer.tokenize(record.index_text)) for record in records) / total_docs
            if total_docs
            else 0.0
        )

        payload_records: list[dict] = []
        doc_freqs: Counter[str] = Counter()

        for record in records:
            tokens = self._tokenizer.tokenize(record.index_text)
            counts = Counter(tokens)
            doc_freqs.update(counts.keys())
            payload_records.append(
                {
                    "section_id": record.section_id,
                    "doc_id": record.doc_id,
                    "title": record.title,
                    "source_path": record.source_path,
                    "section_type": record.section_type,
                    "heading": record.heading,
                    "content": record.content,
                    "token_counts": dict(counts),
                    "doc_len": len(tokens),
                }
            )

        payload = {
            "config": self._bm25.get_config(),
            "avg_doc_length": avg_doc_length,
            "document_count": total_docs,
            "doc_freqs": dict(doc_freqs),
            "records": payload_records,
        }
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return total_docs

    def search(self, query_text: str, limit: int) -> list[RetrievedSection]:
        if not self.index_path.exists():
            return []

        payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        query_tokens = self._tokenizer.tokenize(query_text)
        if not query_tokens:
            return []

        doc_freqs: dict[str, int] = payload["doc_freqs"]
        total_docs: int = max(payload["document_count"], 1)
        avg_doc_length: float = max(payload["avg_doc_length"], 1.0)

        scored: list[tuple[float, dict]] = []
        for record in payload["records"]:
            score = 0.0
            token_counts: dict[str, int] = record["token_counts"]
            doc_len: int = max(record["doc_len"], 1)

            for token in set(query_tokens):
                tf = token_counts.get(token)
                if not tf:
                    continue
                df = doc_freqs.get(token, 0)
                idf = math.log(1 + ((total_docs - df + 0.5) / (df + 0.5)))
                numerator = tf * (self._bm25.k + 1)
                denominator = tf + self._bm25.k * (1 - self._bm25.b + self._bm25.b * (doc_len / avg_doc_length))
                score += idf * (numerator / denominator)

            if score > 0:
                scored.append((score, record))

        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[RetrievedSection] = []
        for rank_index, (score, record) in enumerate(scored[:limit], start=1):
            results.append(
                RetrievedSection(
                    section_id=record["section_id"],
                    doc_id=record["doc_id"],
                    title=record["title"],
                    source_path=record["source_path"],
                    section_type=record["section_type"],
                    heading=record["heading"],
                    content=record["content"],
                    score=score,
                    source="section_sparse",
                    rank=rank_index,
                )
            )
        return results

