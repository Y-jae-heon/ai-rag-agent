"""Lightweight lexical normalization for RAG v4."""

from __future__ import annotations

import re
import unicodedata

from .models import NormalizedQuery

_NORMALIZATION_GROUPS: dict[str, list[str]] = {
    "frontend": ["frontend", "front-end", "front end", "프론트엔드", "프론트", "fe"],
    "backend": ["backend", "back-end", "back end", "백엔드", "백", "be"],
    "feature sliced design": ["fsd", "feature sliced design", "feature-sliced design"],
    "pull request": ["pr", "pull request", "pull-request"],
    "readme": ["readme", "read me"],
    "nestjs": ["nestjs", "nest js"],
    "typescript": ["typescript", "type script"],
}


def normalize_text(text: str) -> str:
    """Normalize punctuation, whitespace, and casing without classifying intent."""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.lower()
    normalized = normalized.replace("/", " ")
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace("(", " ")
    normalized = normalized.replace(")", " ")
    normalized = re.sub(r"[^\w\s가-힣]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def expand_terms(text: str) -> list[str]:
    """Append equivalent lexical variants without turning them into hard filters."""
    normalized = normalize_text(text)
    tokens = set(normalized.split())
    expansions: list[str] = []
    for canonical, aliases in _NORMALIZATION_GROUPS.items():
        alias_hits = {normalize_text(alias) for alias in aliases}
        if any(_contains_alias(normalized, tokens, alias) for alias in alias_hits):
            expansions.append(canonical)
            expansions.extend(sorted(alias_hits))
    # Preserve order while deduplicating.
    deduped: list[str] = []
    seen: set[str] = set()
    for term in expansions:
        if term and term not in seen:
            seen.add(term)
            deduped.append(term)
    return deduped


def build_retrieval_text(*parts: str) -> str:
    """Build a retrieval-friendly text representation from raw text parts."""
    raw = " ".join(part for part in parts if part).strip()
    normalized = normalize_text(raw)
    expansions = expand_terms(raw)
    merged_parts = [raw, normalized, " ".join(expansions)]
    return "\n".join(part for part in merged_parts if part).strip()


def normalize_query(question: str) -> NormalizedQuery:
    """Normalize a user query for dense and sparse retrieval."""
    normalized = normalize_text(question)
    expansions = expand_terms(question)
    retrieval_text = "\n".join(
        part for part in [question.strip(), normalized, " ".join(expansions)] if part
    )
    return NormalizedQuery(
        raw=question,
        normalized=normalized,
        expansions=expansions,
        retrieval_text=retrieval_text,
    )


def _contains_alias(normalized_text: str, tokens: set[str], alias: str) -> bool:
    if not alias:
        return False
    if " " in alias:
        return alias in normalized_text
    return alias in tokens
