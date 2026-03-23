# SPEC.md — developer-chat-bot-v3 기술 명세

버전: v3.0 (P2 완료)
작성일: 2026-03-23

---

## 1. 시스템 개요

개발 컨벤션 문서(FE/BE)에 대한 자연어 질의를 처리하는 QA API 서버.

**v2와의 차이점**: v2는 chunk retrieval 기반의 단일 경로 시스템이었다. v3는 사용자 의도(intent)를 먼저 분류한 후 의도별로 최적화된 실행 경로를 선택하는 **intent-specific execution 시스템**이다.

---

## 2. 아키텍처

### 전체 파이프라인

```
User Query (자연어)
    │
    ▼
[1] QueryUnderstanding      intent + document_query + domain/stack/topic 추출
    │                        (gpt-4o-mini + PydanticOutputParser, LCEL chain)
    ▼
[2] DocumentResolution      document_query → canonical_doc_id + path + confidence
    │                        (exact match → alias match → semantic search)
    ▼
[3] ActionRouting           (intent, resolved) 키 → Handler 선택
    │                        (Python dispatch dict, LangChain Agent 아님)
    ▼
[4] EvidenceLoading         Handler별 다른 전략
    │                        fulltext   : file read only
    │                        summarize  : section_index.get()
    │                        extract    : chunk_index MMR
    │                        discover   : section_index headings
    │                        compare    : section_index.get() × 2
    ▼
[5] ResponseGeneration      Handler별 다른 출력
    │                        fulltext/discover : 결정적 포맷터 (LLM 없음)
    │                        summarize/extract/compare : gpt-4o-mini LLMChain
    ▼
[6] Validation              path safety, evidence threshold, doc match
    │
    ▼
HTTP Response (QueryResponse JSON)
```

### ChromaDB 컬렉션 구조

| 컬렉션 | 용도 | 빌드 방식 |
|--------|------|-----------|
| `document_index` | 문서 단위 semantic search (resolution용) | 문서 전체 텍스트 임베딩 |
| `section_index` | 섹션(`##`~`######`) 단위 저장 | 섹션 헤딩 + 내용 임베딩 |
| `chunk_index` | RecursiveCharacterTextSplitter 500/50 | chunk 임베딩 |

---

## 3. 모듈 명세

### 3.1 query_understanding

**위치**: `src/convention_qa/query_understanding/`

#### IntentClassifier

```python
class IntentClassifier:
    def classify(self, question: str, context: dict) -> QueryUnderstandingResult
```

- LCEL chain: `CLASSIFICATION_PROMPT | ChatOpenAI(gpt-4o-mini, temperature=0) | PydanticOutputParser`
- `alias_normalizer`를 보조 수단으로 사용 (LLM 결과가 None일 때만 보강)

#### QueryUnderstandingResult (Pydantic v2)

```python
class QueryUnderstandingResult(BaseModel):
    intent: Literal["fulltext", "summarize", "extract", "discover", "compare", "clarify"]
    document_query: str | None          # 단일 문서 intent용
    document_queries: list[str] | None  # compare intent용 (2개)
    domain: Literal["frontend", "backend"] | None
    stack: str | None                   # "react", "spring", "kotlin", "nestjs", ...
    topic: str | None
```

---

### 3.2 document_resolution

**위치**: `src/convention_qa/document_resolution/`

#### DocumentResolver

```python
class DocumentResolver:
    def resolve(
        self,
        document_query: str | None,
        domain: str | None,
        stack: str | None,
    ) -> DocumentResolutionResult
```

**5단계 resolution 흐름:**

```
1. document_query=None → 즉시 unresolved 반환
2. exact_match()    — 완전 일치(1.0) + 부분 일치(0.9)
3. alias_match()    — alias_registry.json 기반 (score=0.85)
4. semantic_search() — document_index + domain/stack 필터
5. semantic_search() — document_index 필터 없이 재시도
결과 평가: 1위-2위 score 격차 ≥ 0.15 → resolved, 미만 → clarify
```

#### DocumentResolutionResult (Pydantic v2)

```python
class DocumentResolutionResult(BaseModel):
    resolved: bool
    canonical_doc_id: str | None
    title: str | None
    path: str | None
    confidence: float
    candidates: list[DocumentCandidate]  # clarify 시 다중 후보
```

---

### 3.3 action_routing

**위치**: `src/convention_qa/action_routing/`

#### ActionRouter

dispatch table (`HANDLER_MAP`):

| key | Handler |
|-----|---------|
| `("fulltext", True)` | FulltextHandler |
| `("summarize", True)` | SummarizeHandler |
| `("extract", True)` | ExtractHandler |
| `("extract", False)` | ExtractHandler |
| `("discover", True)` | DiscoverHandler |
| `("discover", False)` | DiscoverHandler |
| `("compare", True)` | CompareHandler |
| `("compare", False)` | CompareHandler |
| `(*, False)` (default) | ClarifyHandler |

```python
class ActionRouter:
    def route_and_execute(
        self,
        understanding: QueryUnderstandingResult,
        resolution: DocumentResolutionResult,
        question: str,
    ) -> HandlerResult
```

#### HandlerContext / HandlerResult (Pydantic v2)

```python
class HandlerContext(BaseModel):
    resolution: Any           # DocumentResolutionResult
    question: str
    understanding: Any = None # QueryUnderstandingResult (compare용)

class HandlerResult(BaseModel):
    answer: str
    answer_type: str
    resolved_document: dict | None
    sources: list[dict]
```

#### 핸들러별 동작

| Handler | LLM | Evidence Source | answer_type |
|---------|-----|-----------------|-------------|
| FulltextHandler | 없음 | `open(path).read()` | `"fulltext"` |
| SummarizeHandler | gpt-4o-mini | section_index.get() | `"summary"` |
| ExtractHandler | gpt-4o-mini | chunk_index MMR (k=4, fetch_k=20) | `"extract"` |
| DiscoverHandler | 없음 | section_index headings | `"discover"` |
| CompareHandler | gpt-4o-mini | section_index.get() × 2 | `"compare"` |
| ClarifyHandler | 없음 | resolution.candidates | `"clarify"` |

**FulltextHandler 안전 정책:**
- `ALLOWED_CORPUS_DIRS`: `docs/fe_chunk_docs`, `docs/be_chunk_docs`
- `os.path.abspath()` 정규화 후 `os.sep` suffix 추가로 prefix 오탐 방지
- path traversal 공격 차단
- 500KB 초과 파일: 앞부분만 반환

---

### 3.4 indexing

**위치**: `src/convention_qa/indexing/`

#### 파일명 규칙

인덱싱 대상 문서 파일명 형식: `{제목} {UUID}.md`

UUID는 정규식 `[0-9a-f]{32}$`로 추출하여 `canonical_doc_id`로 사용한다.

#### stack 자동 감지

| 디렉터리/파일명 패턴 | domain | stack |
|----------------------|--------|-------|
| `fe_chunk_docs/` | frontend | react |
| `Java(Spring)` | backend | spring/java |
| `Kotlin(Spring)` | backend | spring/kotlin |
| `Typescript(NestJS)` | backend | nestjs/typescript |

#### alias_registry.json 구조

```json
{
  "{UUID-32자}": {
    "title": "파일 네이밍 컨벤션",
    "aliases": ["file naming", "파일명 규칙", "..."],
    "domain": "frontend",
    "stack": "react",
    "topic": "naming"
  }
}
```

커버리지: FE 16개 + Java 17개 + Kotlin 10개 + NestJS 11개 = **54개 문서**

topic 분류: `naming` / `architecture` / `pattern` / `git` / `fsd` / `database` / `logging` / `security` / `testing` / `dependency` / `transaction` / `exception` / `datetime` / `api` / `workflow` / `overview` / `utility`

---

### 3.5 response

**위치**: `src/convention_qa/response/`

#### 포맷터 목록

| 함수 | 출력 구조 |
|------|-----------|
| `format_fulltext(title, content, path)` | `## {title}\n> 경로: ...\n\n---\n\n{원문}` |
| `format_summarize(title, summary, path)` | `## {title} 요약\n\n{summary}\n\n> 출처: ...` |
| `format_extract(title, answer_text, source_sections, path)` | `{answer_text}\n\n> 근거: {title} §섹션1, §섹션2` |
| `format_discover(title, path, domain, stack, section_headings)` | `## 문서 발견 결과\n\n**제목**: ...\n**경로**: ...\n...` |
| `format_compare(title_a, title_b, comparison_text, path_a, path_b)` | `## {title_a} vs {title_b} 비교\n\n{comparison_text}\n\n> 출처: ...` |
| `format_clarify(candidates)` | 후보 문서 목록 안내 텍스트 |
| `format_not_found()` | 문서 미발견 안내 텍스트 |

---

### 3.6 API 레이어

**위치**: `src/api/`

#### 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/api/v1/query` | 질의 처리 메인 엔드포인트 |
| `GET` | `/health` | 서버 및 인덱스 상태 확인 |

#### POST /api/v1/query

**Request Body (QueryRequest)**

```json
{
  "question": "string (required)",
  "domain": "frontend | backend | null",
  "stack": "string | null",
  "intent_hint": "string | null"
}
```

**Response Body (QueryResponse)**

```json
{
  "answer": "string",
  "answer_type": "fulltext | summary | extract | discover | clarify",
  "intent": "string",
  "resolved_document": {
    "canonical_doc_id": "string",
    "title": "string",
    "path": "string"
  } | null,
  "sources": [
    {
      "title": "string",
      "path": "string",
      "domain": "string"
    }
  ]
}
```

**Error Response**

```json
{
  "detail": "질의 처리 중 오류가 발생했습니다: {error message}"
}
```

HTTP 500 반환.

#### GET /health

**Response**

```json
{
  "status": "ok | degraded",
  "index_exists": true,
  "ingest_manifest": { ... }
}
```

#### 싱글톤 의존성 (`src/api/dependencies.py`)

`@lru_cache` 패턴으로 다음 객체를 앱 생명주기 동안 단일 인스턴스로 유지:

- `get_intent_classifier()` → `IntentClassifier`
- `get_document_resolver()` → `DocumentResolver`
- `get_action_router()` → `ActionRouter`
- `get_chroma_client()` → ChromaDB Client

#### 인덱스 검증 (lifespan)

앱 시작 시 `.chroma/` 인덱스 존재 여부를 검증한다.
`SKIP_INDEX_CHECK=true` 환경 변수로 우회 가능 (개발 모드).

---

## 4. 환경 변수

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `OPENAI_API_KEY` | 필수 | - | OpenAI API 키 |
| `SKIP_INDEX_CHECK` | 선택 | `false` | `true`로 설정 시 인덱스 없이 서버 시작 |

---

## 5. 의존성 스택

| 패키지 | 버전 | 용도 |
|--------|------|------|
| langchain | >=0.2.0 | LCEL chain, prompt template |
| langchain-openai | >=0.1.0 | ChatOpenAI, OpenAIEmbeddings |
| langchain-chroma | >=0.1.0 | ChromaDB vectorstore 래퍼 |
| langchain-text-splitters | >=0.2.0 | RecursiveCharacterTextSplitter |
| chromadb | >=0.5.0 | 벡터 DB (로컬 영속 스토리지) |
| fastapi | >=0.111.0 | HTTP API 서버 |
| uvicorn[standard] | >=0.29.0 | ASGI 서버 |
| pydantic | >=2.0.0 | 데이터 모델 검증 |
| openai | >=1.30.0 | OpenAI Python SDK |
| python-dotenv | >=1.0.0 | .env 파일 로딩 |
| pytest | >=8.0.0 | 단위 테스트 |

---

## 6. 테스트

**위치**: `tests/`

| 파일 | 테스트 수 | 대상 |
|------|-----------|------|
| `test_summarize_handler.py` | 6 | SummarizeHandler |
| `test_extract_handler.py` | 8 | ExtractHandler |
| `test_discover_handler.py` | 11 | DiscoverHandler |
| `test_compare_handler.py` | 16 | CompareHandler |

**총 41개 단위 테스트**

모든 외부 의존(ChromaDB, OpenAI API)은 `unittest.mock.patch`로 대체.

```bash
python -m pytest tests/ -v
```

---

## 7. 구현 이력

| 단계 | 티켓 | 내용 |
|------|------|------|
| P0 | TK-01 | IntentClassifier + ActionRouter dispatch base |
| P0 | TK-02 | DocumentResolver (exact/alias/semantic 3단계) |
| P0 | TK-03 | FulltextHandler + FastAPI 레이어 |
| P1 | TK-04 | alias_registry 포맷 업그레이드 + SummarizeHandler |
| P1 | TK-05 | ExtractHandler + DiscoverHandler + 응답 포맷 분리 |
| P2 | TK-06 | CompareHandler + 단위 테스트 41개 |

---

## 8. 주요 설계 결정

| 결정 | 내용 | 이유 |
|------|------|------|
| fulltext는 LLM 미사용 | `open(path).read()` 직접 반환 | 원문 변형 방지, 비용 절감 |
| ActionRouter는 dispatch dict | LangChain AgentExecutor 불사용 | 라우팅 로직 명시성, 예측 가능성 확보 |
| ChromaDB 3컬렉션 분리 | document/section/chunk 각자 별도 컬렉션 | 혼용 시 document resolution 불안정 |
| IntentClassifier는 gpt-4o-mini | haiku 상당 경량 모델 | 분류 작업에는 충분, 응답 시간 단축 |
| alias_normalizer는 LLM 보조 | LLM 결과 없을 때만 보강 | LLM 정확도 우선, normalizer는 fallback |
| document_queries 필드 추가 | compare intent용 list[str] | 기존 document_query와 공존, 하위 호환 유지 |
