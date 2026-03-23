"""싱글톤 의존성 주입 모듈.

lru_cache를 사용하여 IntentClassifier, DocumentResolver, ActionRouter를
애플리케이션 생명주기 동안 단일 인스턴스로 유지한다.
"""

from functools import lru_cache

from src.convention_qa.action_routing.router import ActionRouter
from src.convention_qa.document_resolution.resolver import DocumentResolver
from src.convention_qa.indexing.config import CHROMA_PERSIST_DIR
from src.convention_qa.query_understanding.intent_classifier import IntentClassifier


@lru_cache(maxsize=1)
def get_intent_classifier() -> IntentClassifier:
    """IntentClassifier 싱글톤 인스턴스를 반환한다."""
    return IntentClassifier()


@lru_cache(maxsize=1)
def get_document_resolver() -> DocumentResolver:
    """DocumentResolver 싱글톤 인스턴스를 반환한다."""
    return DocumentResolver()


@lru_cache(maxsize=1)
def get_action_router() -> ActionRouter:
    """ActionRouter 싱글톤 인스턴스를 반환한다."""
    return ActionRouter()


def get_chroma_client() -> None:
    """서버 기동 전 ChromaDB 인덱스 존재 여부를 확인한다.

    3개 컬렉션 경로(document_index, section_index, chunk_index)가
    모두 존재하는지 검사한다.

    Raises:
        RuntimeError: 필수 컬렉션 디렉토리가 존재하지 않는 경우.
    """
    required = ["document_index", "section_index", "chunk_index"]
    for name in required:
        collection_path = CHROMA_PERSIST_DIR / name
        if not collection_path.exists():
            raise RuntimeError(
                f"Index '{name}' not found. Run: python scripts/ingest.py"
            )
