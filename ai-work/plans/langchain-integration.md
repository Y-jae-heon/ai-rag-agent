# LangChain Integration Plan

작성일: 2026-03-23
관련 문서: ai-work/plans/architecture-v3.md

## 개요

이 문서는 v3 아키텍처의 각 레이어를 LangChain 컴포넌트로 어떻게 구현할지를 정의한다.
코드는 구현 단계에서 작성한다. 이 문서는 컴포넌트 선택과 연결 방식 계획이다.

---

## 1. Query Understanding — LangChain 구성

### 사용 컴포넌트

| 컴포넌트 | 역할 |
|---------|------|
| `ChatOpenAI(model="gpt-4o-mini")` | intent + hint 추출 LLM |
| `ChatPromptTemplate` | few-shot 예시 포함 system prompt |
| `PydanticOutputParser(pydantic_object=QueryUnderstandingResult)` | 구조화 출력 파싱 |
| LCEL pipe (`|`) | prompt → llm → parser 연결 |

### Chain 구조

```
intent_chain = (
    ChatPromptTemplate.from_messages([...])
    | ChatOpenAI(model="gpt-4o-mini", temperature=0)
    | PydanticOutputParser(pydantic_object=QueryUnderstandingResult)
)
```

### 프롬프트 설계 원칙
- System: intent 정의 5개 + 분류 기준 + 한국어 alias 목록
- Human: 자연어 질문
- Few-shot: 케이스 A/B/C 예시 포함
- Output format: Pydantic JSON schema 자동 주입

---

## 2. Document Resolution — LangChain 구성

### 사용 컴포넌트

| 컴포넌트 | 역할 |
|---------|------|
| `Chroma(collection_name="document_index")` | 문서 단위 벡터 스토어 |
| `OpenAIEmbeddings` | 문서 및 쿼리 임베딩 |
| `Chroma.similarity_search_with_score` | semantic fallback 검색 |
| Python str matching | exact / alias match (LLM 없음) |

### Resolution 알고리즘

```
Step 1: exact_match(document_query, document_index.titles)
  → 정규화 후 완전 일치 확인

Step 2: alias_match(document_query, document_index.aliases)
  → aliases 필드에 포함 여부 확인

Step 3: semantic_search(document_query, document_index, filter={domain, stack})
  → Chroma similarity_search_with_score(k=5)
  → score threshold: 0.75 이상만 후보 채택

Step 4: 후보 평가
  → 1개: confirmed (confidence = score)
  → 2개 이상: clarify 요청
  → 0개: unresolved → 전체 인덱스 재시도 (domain filter 제거)
```

### 인덱스 초기화 방식
- `Chroma.from_documents()` 로 초기 빌드
- `persist_directory` 로 로컬 저장 (`.chroma/`)
- manifest.json 기반 증분 업데이트 지원

**중요: 인덱스 빌드는 서버 기동과 분리된다.**
- 인덱스 빌드: `python scripts/ingest.py` (수동, 문서 변경 시)
- 서버 기동: `uvicorn src.api.main:app` (인덱스 존재 시에만 정상 기동)
- 서버 lifespan 이벤트에서 `.chroma/` 존재 여부를 검증하며, 없으면 즉시 종료
- `Chroma.from_documents()`는 서버 코드에서 절대 호출하지 않는다

관련 상세: `ai-work/plans/ingest-separation.md`

---

## 3. Action Routing — LangChain 구성

LangChain 불필요. Python dispatch dict로 구현.

```python
HANDLER_MAP = {
    ("fulltext", True): FulltextHandler,
    ("summarize", True): SummarizeHandler,
    ("extract", True): ExtractHandler,
    ("extract", False): GeneralExtractHandler,
    ("discover", True): DiscoverHandler,
    ("discover", False): DiscoverHandler,
    ("compare", True): CompareHandler,
}

def route(intent, resolved) -> BaseHandler:
    return HANDLER_MAP.get((intent, resolved), ClarifyHandler)()
```

---

## 4. Evidence Loading — LangChain 구성

### SummarizeHandler 로딩

```python
# section_index에서 canonical_doc_id 필터로 전체 섹션 수집
retriever = Chroma(collection_name="section_index").as_retriever(
    search_kwargs={"filter": {"canonical_doc_id": doc_id}, "k": 50}
)
sections = retriever.get_relevant_documents("*")  # 전체 수집
```

### ExtractHandler 로딩

```python
# chunk_index에서 MMR retrieval (diversity + relevance 균형)
retriever = Chroma(collection_name="chunk_index").as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 6,
        "fetch_k": 20,
        "filter": {"canonical_doc_id": doc_id}
    }
)
chunks = retriever.get_relevant_documents(question)
```

### FulltextHandler 로딩

```python
# LangChain 사용 안 함
with open(resolved_path, "r", encoding="utf-8") as f:
    raw_content = f.read()
```

---

## 5. Response Generation — LangChain 구성

### SummarizeHandler Chain

```python
summarize_chain = (
    ChatPromptTemplate.from_messages([
        ("system", SUMMARIZE_SYSTEM_PROMPT),
        ("human", "{question}\n\n## 섹션 목록\n{sections}")
    ])
    | ChatOpenAI(model="gpt-4o", temperature=0)
    | StrOutputParser()
)
```

### ExtractHandler Chain

```python
extract_chain = (
    ChatPromptTemplate.from_messages([
        ("system", EXTRACT_SYSTEM_PROMPT),
        ("human", "{question}\n\n## 검색된 컨텍스트\n{chunks}")
    ])
    | ChatOpenAI(model="gpt-4o", temperature=0)
    | StrOutputParser()
)
```

### DiscoverHandler — 결정적 포맷터 (LLM 없음)

```python
def format_discover(doc_metadata: dict) -> str:
    return f"""
## 문서 정보
- 제목: {doc_metadata['title']}
- 경로: {doc_metadata['path']}
- 도메인: {doc_metadata['domain']} / {doc_metadata['stack']}
- 주요 섹션: {', '.join(doc_metadata['section_headings'])}
"""
```

---

## 6. LangChain Tools (옵션 — Phase 2 이후 고려)

intent 분류가 복잡해지거나 multi-step reasoning이 필요할 경우 LangChain Tools로 전환 고려.

### 계획된 Tools

| Tool 이름 | 설명 |
|-----------|------|
| `DocumentLookupTool` | 문서명으로 document_index 검색 |
| `SectionSearchTool` | 섹션 키워드로 section_index 검색 |
| `FulltextReadTool` | 허용 경로 내 파일 읽기 |
| `DocumentListTool` | domain/stack 필터로 문서 목록 반환 |

각 Tool은 `langchain_core.tools.BaseTool` 상속, `_run` 메서드 구현.
AgentExecutor 또는 LCEL `RunnableWithMessageHistory`와 연동 가능.

---

## 7. ChromaDB 컬렉션 구성

| 컬렉션 | 용도 | 벡터 대상 |
|--------|------|----------|
| `document_index` | 문서 단위 식별 | title + aliases + section_headings |
| `section_index` | 섹션 단위 탐색 | section_heading + section_content |
| `chunk_index` | chunk 단위 QA | chunk_text (기존 방식 유지) |

persist_directory 권장 구조:
```
.chroma/
  document_index/
  section_index/
  chunk_index/
```

---

## 8. FastAPI 연동

```
POST /api/v1/query
  body: QueryRequest
    - question: str
    - domain: str | None
    - stack: str | None
    - intent_hint: str | None   # 클라이언트 hint (선택)

  response: QueryResponse
    - intent: str
    - resolved_document: DocumentInfo | None
    - answer: str
    - answer_type: Literal["fulltext", "summary", "extract", "discover", "clarify"]
    - sources: list[SourceRef]
```

---

## 의존성 요약

requirements.txt 기존 항목으로 모두 커버됨:
- `langchain>=0.2.0` — LCEL, chains
- `langchain-openai>=0.1.0` — ChatOpenAI, OpenAIEmbeddings
- `langchain-community>=0.2.0` — Chroma wrapper
- `langchain-core>=0.2.0` — BaseTool, Runnable
- `chromadb>=0.5.0` — vector store
- `pydantic>=2.0.0` — 구조화 출력
- `fastapi>=0.111.0` — HTTP API
