"""헬스 체크 라우터.

ChromaDB 컬렉션 상태 및 ingest_manifest.json 정보를 반환한다.
인덱스가 없어도 200 OK를 반환하며 status를 "degraded"로 표시한다.
"""

import json
from typing import Any

from fastapi import APIRouter

from src.convention_qa.indexing.config import CHROMA_PERSIST_DIR

router = APIRouter()

_REQUIRED_COLLECTIONS = ["document_index", "section_index", "chunk_index"]
_MANIFEST_PATH = CHROMA_PERSIST_DIR / "ingest_manifest.json"


@router.get("/health")
async def health() -> dict[str, Any]:
    """ChromaDB 컬렉션 상태 및 ingest_manifest.json 정보를 반환한다.

    인덱스가 없어도 200 OK를 반환하며, 누락된 컬렉션이 있으면
    status를 "degraded"로 표시한다.

    Returns:
        status: "ok" 또는 "degraded"
        chroma_collections: 존재하는 컬렉션 목록
        manifest: ingest_manifest.json 내용 (없으면 None)
    """
    existing_collections: list[str] = [
        name
        for name in _REQUIRED_COLLECTIONS
        if (CHROMA_PERSIST_DIR / name).exists()
    ]

    status = "ok" if len(existing_collections) == len(_REQUIRED_COLLECTIONS) else "degraded"

    manifest: dict[str, Any] | None = None
    if _MANIFEST_PATH.exists():
        try:
            with _MANIFEST_PATH.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            manifest = None

    return {
        "status": status,
        "chroma_collections": existing_collections,
        "manifest": manifest,
    }
