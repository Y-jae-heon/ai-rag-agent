"""Exact match 및 alias match를 통한 문서 후보 검색 모듈."""

import re

from .models import DocumentCandidate


def normalize_text(text: str) -> str:
    """소문자 변환 + 공백 정규화 + 특수문자 제거."""
    text = text.lower()
    # 특수문자 제거 (괄호 포함 내용은 유지)
    text = re.sub(r"[^\w\s가-힣]", " ", text)
    # 공백 정규화
    text = re.sub(r"\s+", " ", text).strip()
    return text


def exact_match(
    document_query: str,
    documents: list[dict],
) -> DocumentCandidate | None:
    """document_query를 정규화 후 title과 완전/부분 일치 확인.

    Args:
        document_query: 사용자가 요청한 문서 쿼리 문자열.
        documents: document_index 메타데이터 목록. 각 항목은 title, path, canonical_doc_id 등을 포함.

    Returns:
        일치하는 DocumentCandidate 또는 None.
        완전 일치(score=1.0) 우선, 그 다음 부분 일치(score=0.9).
    """
    normalized_query = normalize_text(document_query)

    exact_candidates: list[DocumentCandidate] = []
    partial_candidates: list[DocumentCandidate] = []

    for doc in documents:
        title = doc.get("title", "")
        normalized_title = normalize_text(title)

        if normalized_query == normalized_title:
            exact_candidates.append(
                DocumentCandidate(
                    canonical_doc_id=doc.get("canonical_doc_id", ""),
                    title=title,
                    path=doc.get("path", ""),
                    score=1.0,
                    domain=doc.get("domain"),
                    stack=doc.get("stack"),
                )
            )
        elif normalized_query in normalized_title or normalized_title in normalized_query:
            partial_candidates.append(
                DocumentCandidate(
                    canonical_doc_id=doc.get("canonical_doc_id", ""),
                    title=title,
                    path=doc.get("path", ""),
                    score=0.9,
                    domain=doc.get("domain"),
                    stack=doc.get("stack"),
                )
            )

    if exact_candidates:
        return exact_candidates[0]
    if partial_candidates:
        return partial_candidates[0]
    return None


def alias_match(
    document_query: str,
    documents: list[dict],
    alias_registry: dict[str, list[str]],
) -> DocumentCandidate | None:
    """document_query가 alias_registry의 aliases 중 하나와 일치하는지 확인.

    Args:
        document_query: 사용자가 요청한 문서 쿼리 문자열.
        documents: document_index 메타데이터 목록.
        alias_registry: {canonical_doc_id: [alias, ...]} 형태의 딕셔너리.

    Returns:
        일치하는 DocumentCandidate 또는 None.
    """
    normalized_query = normalize_text(document_query)

    # canonical_doc_id -> document 메타데이터 매핑 생성
    doc_map: dict[str, dict] = {}
    for doc in documents:
        doc_id = doc.get("canonical_doc_id", "")
        if doc_id:
            doc_map[doc_id] = doc

    for canonical_doc_id, aliases in alias_registry.items():
        for alias in aliases:
            normalized_alias = normalize_text(alias)
            if normalized_query == normalized_alias or normalized_query in normalized_alias or normalized_alias in normalized_query:
                doc = doc_map.get(canonical_doc_id)
                if doc:
                    return DocumentCandidate(
                        canonical_doc_id=canonical_doc_id,
                        title=doc.get("title", ""),
                        path=doc.get("path", ""),
                        score=0.95,
                        domain=doc.get("domain"),
                        stack=doc.get("stack"),
                    )
                else:
                    # documents에 없더라도 alias_registry 기반으로 후보 반환
                    return DocumentCandidate(
                        canonical_doc_id=canonical_doc_id,
                        title=alias,
                        path="",
                        score=0.85,
                        domain=None,
                        stack=None,
                    )

    return None
