# Module Plan: document_resolution

## 역할

document_query를 실제 문서 경로(canonical_doc_id + path)로 확정한다.
exact → alias → semantic 3단계 resolution 수행.

## 구현할 파일

| 파일 | 역할 |
|------|------|
| `__init__.py` | 모듈 export |
| `models.py` | DocumentResolutionResult, DocumentCandidate Pydantic 모델 |
| `resolver.py` | DocumentResolver 클래스 — 3단계 resolution 로직 |
| `exact_matcher.py` | 정규화 기반 exact/alias match |
| `semantic_retriever.py` | ChromaDB document_index semantic search |

## 핵심 클래스

```python
# models.py
class DocumentCandidate(BaseModel):
    canonical_doc_id: str
    title: str
    path: str
    score: float

class DocumentResolutionResult(BaseModel):
    resolved: bool
    canonical_doc_id: str | None
    path: str | None
    title: str | None
    confidence: float
    resolution_strategy: Literal["exact", "alias", "semantic", "unresolved"]
    candidates: list[DocumentCandidate]

# resolver.py
class DocumentResolver:
    def resolve(self, document_query: str, domain: str | None, stack: str | None) -> DocumentResolutionResult: ...
```

## LangChain 컴포넌트

- `Chroma(collection_name="document_index", persist_directory=".chroma/document_index")`
- `OpenAIEmbeddings()`
- `Chroma.similarity_search_with_score(query, k=5, filter={...})`

## 테스트 위치

`tests/test_document_resolver.py`

## 관련 티켓

P0-TK-02, P1-TK-04
