"""RAG v4 health route."""

import json
from typing import Any

from fastapi import APIRouter

from src.rag_v4.config import (
    DOCUMENT_DENSE_COLLECTION,
    SECTION_DENSE_COLLECTION,
    SECTION_SPARSE_DIRNAME,
    V4_PERSIST_DIR,
)

router = APIRouter()

_REQUIRED_INDICES = {
    DOCUMENT_DENSE_COLLECTION: V4_PERSIST_DIR / DOCUMENT_DENSE_COLLECTION,
    SECTION_DENSE_COLLECTION: V4_PERSIST_DIR / SECTION_DENSE_COLLECTION,
    SECTION_SPARSE_DIRNAME: V4_PERSIST_DIR / SECTION_SPARSE_DIRNAME / "index.json",
}
_MANIFEST_PATH = V4_PERSIST_DIR / "ingest_manifest.json"


@router.get("/health")
async def health() -> dict[str, Any]:
    """RAG v4 인덱스 상태 및 ingest_manifest.json 정보를 반환한다.

    인덱스가 없어도 200 OK를 반환하며, 누락된 인덱스가 있으면
    status를 "degraded"로 표시한다.

    Returns:
        status: "ok" 또는 "degraded"
        indices: 존재하는 인덱스 목록
        manifest: ingest_manifest.json 내용 (없으면 None)
    """
    existing_indices: list[str] = [
        name
        for name, path in _REQUIRED_INDICES.items()
        if path.exists()
    ]

    status = "ok" if len(existing_indices) == len(_REQUIRED_INDICES) else "degraded"

    manifest: dict[str, Any] | None = None
    if _MANIFEST_PATH.exists():
        try:
            with _MANIFEST_PATH.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            manifest = None

    return {
        "status": status,
        "indices": existing_indices,
        "manifest": manifest,
        "version": "v4",
    }
