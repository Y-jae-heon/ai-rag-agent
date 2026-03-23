# Architecture Plan v3

작성일: 2026-03-23
기반 문서: ai-docs/rag-init-document.md

## 핵심 설계 전환

v2에서 v3로의 전환은 기술 개선이 아니라 제품 패러다임 전환이다.

| 항목 | v2 | v3 |
|------|----|----|
| 제품 정의 | 규칙 QA 시스템 | 문서 탐색 + 의도별 실행 시스템 |
| 검색 단위 | chunk | document > section > chunk |
| 의도 처리 | 단일 QA 파이프라인 | intent-specific handler 분기 |
| fulltext | LLM 생성 시도 (실패) | file read 직접 반환 |
| gate 역할 | termination 판정기 | recovery strategy 조정기 |

---

## 레이어 구조

```
HTTP Request
     |
     v
[1] Query Understanding
     |
     v
[2] Document Resolution
     |
     v
[3] Action Routing
     |
     v
[4] Evidence Loading
     |
     v
[5] Response Generation / Delivery
     |
     v
[6] Validation
     |
     v
HTTP Response
```

---

## 레이어별 상세 설계

### [1] Query Understanding

**목적**: 자연어 쿼리에서 intent, document_query, domain/stack/topic hints를 추출한다.

**입력**: 사용자 자연어 질문 + request metadata

**출력**:
```python
class QueryUnderstandingResult:
    intent: Literal["discover", "summarize", "extract", "fulltext", "compare"]
    document_query: str | None      # 문서명 후보 ("파일 네이밍 컨벤션")
    domain: Literal["frontend", "backend"] | None
    stack: str | None               # "react", "spring", "nestjs", ...
    topic: str | None               # "naming", "testing", "architecture", ...
    raw_question: str               # 원본 질문 (변형 없음)
```

**LangChain 구성**:
- `ChatOpenAI` (gpt-4o-mini) + `PydanticOutputParser`
- LCEL: `prompt | llm | parser`
- 프롬프트에 intent 정의와 예시를 포함
- 한국어 alias 처리 포함 (FE/BE, 프론트/백)

**핵심 결정**: `question` 하나에 모든 의미를 과적재하지 않는다. 구조화된 필드로 분리 전달.

---

### [2] Document Resolution

**목적**: QueryUnderstandingResult의 document_query를 실제 문서 경로로 확정한다.

**입력**: QueryUnderstandingResult

**출력**:
```python
class DocumentResolutionResult:
    resolved: bool
    canonical_doc_id: str | None
    path: str | None
    title: str | None
    confidence: float               # 0.0 ~ 1.0
    resolution_strategy: Literal["exact", "alias", "semantic", "unresolved"]
    candidates: list[DocumentCandidate]  # 다중 후보일 때
```

**Resolution 순서 (gate 재설계 원칙 5 적용)**:
1. exact title match (document_index 문서명 검색)
2. alias match (문서별 aliases 필드 매칭)
3. domain/stack 필터 + semantic search (document_index)
4. candidates가 2개 이상이면 clarify 요청

**LangChain 구성**:
- ChromaDB `document_index` 컬렉션 (별도 구성)
- `Chroma.similarity_search_with_score` + metadata filter
- exact/alias match는 Python 문자열 처리 (LLM 불필요)
- semantic fallback만 embedding 사용

---

### [3] Action Routing

**목적**: intent + DocumentResolutionResult를 기반으로 올바른 handler를 선택한다.

**입력**: QueryUnderstandingResult + DocumentResolutionResult

**라우팅 테이블**:
| intent | resolved | handler |
|--------|----------|---------|
| discover | any | DiscoverHandler |
| summarize | true | SummarizeHandler |
| summarize | false | ClarifyHandler |
| extract | true | ExtractHandler |
| extract | false | ExtractHandler (general) |
| fulltext | true (1개) | FulltextHandler |
| fulltext | false / 다중 | ClarifyHandler |
| compare | true (2개) | CompareHandler |

**구현 방식**: Python dispatch dict (LangChain 불필요, 단순 조건 분기)

---

### [4] Evidence Loading

**목적**: handler에 필요한 실제 컨텍스트를 로딩한다. handler별로 다른 로딩 전략 사용.

| handler | 로딩 전략 |
|---------|-----------|
| DiscoverHandler | document_index 메타데이터만 |
| SummarizeHandler | section_index 전체 섹션 (resolved doc) |
| ExtractHandler | chunk_index 검색 (section-aware) |
| FulltextHandler | 파일 직접 read (LLM 없음) |
| CompareHandler | 두 문서의 section_index 로딩 |

**LangChain 구성**:
- `Chroma` retriever with metadata filter (`canonical_doc_id`)
- SummarizeHandler: `doc_id` filter로 모든 섹션 수집
- ExtractHandler: `MMRRetriever` or `SelfQueryRetriever`
- FulltextHandler: Python `open(path).read()` — LangChain 사용 안 함

---

### [5] Response Generation / Delivery

**목적**: 로딩된 evidence를 기반으로 intent에 맞는 응답을 생성하거나 전달한다.

| handler | 응답 방식 |
|---------|-----------|
| DiscoverHandler | 결정적 포맷터 (문서명 + 경로 + 관련 문서) |
| SummarizeHandler | LLMChain (intent-specific system prompt) |
| ExtractHandler | LLMChain (기존 QA prompt 유지) |
| FulltextHandler | 파일 원문 직접 반환 (포맷 래핑만) |
| CompareHandler | LLMChain (diff-focused prompt) |

**LangChain 구성**:
- `ChatPromptTemplate` + `ChatOpenAI` + `StrOutputParser`
- LCEL chain per handler
- 각 handler는 독립적인 system prompt를 가짐 (Phase 6)

---

### [6] Validation

**목적**: 응답 전 최종 안전성 검증.

검증 항목:
- wrong document suppression: resolved doc과 응답 내 문서명 일치 확인
- insufficient evidence: evidence가 없거나 score가 threshold 미달이면 clarify
- unsupported fulltext: resolved doc이 corpus 허용 경로 외부면 거부
- multi-candidate clarify: 후보가 2개 이상이면 사용자에게 선택 요청

---

## 데이터 플로우 요약

```
User: "프론트엔드 파일 네이밍 컨벤션 문서 전문 보여줘"

[1] QueryUnderstanding
    → intent=fulltext, document_query="파일 네이밍 컨벤션", domain=frontend

[2] DocumentResolution
    → exact match: "파일 네이밍 컨벤션 325e63c6..."
    → path: docs/fe_chunk_docs/파일 네이밍 컨벤션 325e63c6fa9780149d90e16c61f7f0e2.md
    → confidence=0.98, strategy=exact

[3] ActionRouting
    → intent=fulltext + resolved=true → FulltextHandler

[4] EvidenceLoading
    → open(path).read() → raw_content

[5] ResponseDelivery
    → fulltext response: raw_content 직접 반환

[6] Validation
    → path in corpus_allowed_paths: OK
    → return response
```

---

## 인덱스 구조

### document_index (ChromaDB collection)
문서 단위 인덱스. 각 문서가 1개의 벡터로 표현.

```python
{
    "id": "canonical_doc_id",
    "embedding": embed(title + aliases + section_headings),
    "metadata": {
        "canonical_doc_id": str,
        "title": str,
        "aliases": list[str],         # JSON 직렬화
        "path": str,
        "domain": str,                # "frontend" | "backend"
        "stack": str,                 # "react" | "spring" | "nestjs" | ...
        "topic": str,
        "doc_type": str,
        "section_headings": list[str], # JSON 직렬화
        "language": str
    }
}
```

### section_index (ChromaDB collection)
섹션 단위 인덱스. 문서의 각 ## 섹션이 1개의 벡터.

```python
{
    "id": "doc_id::section_slug",
    "embedding": embed(section_heading + section_content),
    "metadata": {
        "canonical_doc_id": str,
        "section_heading": str,
        "section_summary": str,
        "rule_type": str,
        "content_span": str,   # "lines 10-45"
        "path": str
    }
}
```

### chunk_index (ChromaDB collection)
기존 chunk 단위 인덱스 유지. ExtractHandler 전용.

---

## 기술 스택

| 역할 | 라이브러리 |
|------|-----------|
| LLM | langchain-openai (ChatOpenAI) |
| Embedding | langchain-openai (OpenAIEmbeddings) |
| Vector DB | chromadb (langchain-community Chroma) |
| Chain composition | langchain-core (LCEL) |
| Structured output | pydantic v2 + PydanticOutputParser |
| HTTP API | fastapi + uvicorn |
| Text splitting | langchain-text-splitters |
| Config | python-dotenv |

---

## 성공 기준 (rag-init-document.md §12 기준)

| 케이스 | 질문 | 기대 동작 |
|--------|------|-----------|
| A | 프론트엔드 파일 네이밍 컨벤션 문서 안의 내용을 알려줘 | SummarizeHandler → 구조 + 핵심 규칙 3~6항목 |
| B | 프론트엔드 파일 네이밍 컨벤션 문서 전문 보여줘 | FulltextHandler → 원문 그대로 반환 |
| C | 프론트엔드 파일 네이밍 컨벤션에서 Test 파일 규칙만 알려줘 | ExtractHandler → Test 섹션 근거 추출 |
