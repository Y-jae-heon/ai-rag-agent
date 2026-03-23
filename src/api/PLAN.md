# Module Plan: api

## 역할

FastAPI HTTP 레이어. 외부 요청을 받아 convention_qa 파이프라인에 위임하고 응답을 반환한다.

## 구현할 파일

| 파일 | 역할 |
|------|------|
| `__init__.py` | 모듈 export |
| `main.py` | FastAPI 앱 진입점, 라우터 등록 |
| `models.py` | QueryRequest, QueryResponse HTTP 모델 |
| `routes/query.py` | POST /api/v1/query 엔드포인트 |
| `routes/health.py` | GET /health 헬스체크 |
| `dependencies.py` | 의존성 주입 (IntentClassifier, DocumentResolver, ActionRouter 싱글톤) |

## API 명세

### POST /api/v1/query

Request:
```json
{
  "question": "파일 네이밍 컨벤션 전문 보여줘",
  "domain": "frontend",
  "stack": null,
  "intent_hint": null
}
```

Response:
```json
{
  "answer": "...",
  "answer_type": "fulltext",
  "intent": "fulltext",
  "resolved_document": {
    "canonical_doc_id": "325e63c6...",
    "title": "파일 네이밍 컨벤션",
    "path": "docs/fe_chunk_docs/..."
  },
  "sources": []
}
```

### GET /health

Response:
```json
{
  "status": "ok",
  "chroma_collections": ["document_index", "section_index", "chunk_index"]
}
```

## 파이프라인 실행 순서

```python
# routes/query.py
async def query(request: QueryRequest):
    # 1. intent classification
    understanding = intent_classifier.classify(request.question, request.dict())
    # 2. document resolution
    resolution = document_resolver.resolve(understanding.document_query, ...)
    # 3. action routing + execution
    response = action_router.route_and_execute(understanding, resolution, request.question)
    return response
```

## 관련 티켓

P0-TK-01 완료 후 기본 라우팅 연동 가능
