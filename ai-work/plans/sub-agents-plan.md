# Sub-Agent 구현 계획

작성일: 2026-03-23
관련 문서: ai-work/plans/architecture-v3.md

## 개요

v3 아키텍처는 복잡한 다단계 처리를 담당하는 전문 에이전트들로 구성된다.
이 문서는 각 Claude Code sub-agent의 역할, 책임, 입출력 계약을 정의한다.

기존 에이전트: `.claude/agents/rag-retriever.md` (chunk-level retrieval 전담, 유지)

---

## 에이전트 지도

```
User Query
    |
    v
[intent-classifier]       # 의도 분류 + 힌트 추출
    |
    v
[document-resolver]       # 문서 식별 및 경로 확정
    |
    v
[action-router]           # 핸들러 선택 + 실행 조율
    |
    ├── summarize → [rag-retriever (section mode)]
    ├── extract   → [rag-retriever (chunk mode)]
    ├── fulltext  → [fulltext-delivery]
    └── discover  → 결정적 포맷터 (에이전트 불필요)
```

---

## Agent 1: intent-classifier

**파일**: `.claude/agents/intent-classifier.md`
**Model**: `claude-haiku-4-5-20251001` (빠른 분류, 비용 효율)
**Color**: blue

### 역할
사용자 자연어 질문에서 intent, document_query, domain/stack/topic hints를 추출한다.

### 입력
```
question: str           # 사용자 원본 질문
domain_hint: str | None # 요청 메타데이터 domain
stack_hint: str | None  # 요청 메타데이터 stack
```

### 출력
```json
{
  "intent": "fulltext | summarize | extract | discover | compare",
  "document_query": "파일 네이밍 컨벤션",
  "domain": "frontend | backend | null",
  "stack": "react | spring | nestjs | null",
  "topic": "naming | testing | architecture | null",
  "confidence": 0.95
}
```

### 분류 기준
| 신호 | intent |
|------|--------|
| "전문", "원문", "전체 내용 보여줘" | fulltext |
| "내용 알려줘", "설명해줘", "뭐가 있어" | summarize |
| "~규칙만", "~방법", "~어떻게" | extract |
| "어떤 문서", "문서 있어?", "찾아줘" | discover |
| "차이", "비교", "vs" | compare |

### 한국어 alias 처리
- FE / 프론트 / 프론트엔드 → domain=frontend
- BE / 백 / 백엔드 → domain=backend
- 스프링 / Spring → stack=spring
- 네스트 / NestJS → stack=nestjs

---

## Agent 2: document-resolver

**파일**: `.claude/agents/document-resolver.md`
**Model**: `claude-haiku-4-5-20251001`
**Color**: green

### 역할
QueryUnderstandingResult의 document_query를 실제 문서 경로로 확정한다.
exact match → alias match → semantic search 순서로 시도한다.

### 입력
```
document_query: str
domain: str | None
stack: str | None
```

### 출력
```json
{
  "resolved": true,
  "canonical_doc_id": "325e63c6fa9780149d90e16c61f7f0e2",
  "title": "파일 네이밍 컨벤션",
  "path": "docs/fe_chunk_docs/파일 네이밍 컨벤션 325e63c6fa9780149d90e16c61f7f0e2.md",
  "confidence": 0.98,
  "resolution_strategy": "exact | alias | semantic | unresolved",
  "candidates": []
}
```

### Resolution 전략
1. **exact**: document_query를 정규화 후 document_index title과 완전 일치
2. **alias**: document_index의 aliases 필드에서 포함 여부
3. **semantic**: OpenAI embedding + ChromaDB similarity (threshold 0.75)
4. **다중 후보**: candidates 목록 반환 → action-router가 clarify 처리

### 에이전트 메모리 활용
- 자주 매핑되는 alias 패턴 기록
- 실패한 resolution 쿼리와 성공한 reformulation 기록
- domain별 문서 목록 캐시 패턴 기록

---

## Agent 3: action-router

**파일**: `.claude/agents/action-router.md`
**Model**: `claude-sonnet-4-6` (복잡한 핸들러 실행 조율)
**Color**: orange

### 역할
intent + DocumentResolutionResult를 받아 적절한 handler를 실행하고 최종 응답을 조합한다.

### 입력
```
query_understanding: QueryUnderstandingResult
document_resolution: DocumentResolutionResult
original_question: str
```

### 출력
```json
{
  "answer": "...",
  "answer_type": "fulltext | summary | extract | discover | clarify",
  "resolved_document": { "title": "...", "path": "..." },
  "sources": [{ "doc_id": "...", "section": "...", "excerpt": "..." }]
}
```

### 핸들러 실행 매핑
| intent | resolved | 실행 |
|--------|----------|------|
| fulltext | true (1개) | fulltext-delivery 에이전트 호출 |
| summarize | true | rag-retriever(section mode) → summarize LLMChain |
| extract | true | rag-retriever(chunk mode) → extract LLMChain |
| extract | false | rag-retriever(no filter) → extract LLMChain |
| discover | any | document_index 메타데이터 포맷 |
| compare | true (2개) | rag-retriever × 2 → compare LLMChain |
| any | false/multi | clarify 응답 생성 |

### Validation 책임
- wrong document: 응답 내 문서명 vs resolved_document 일치 검증
- insufficient evidence: score < threshold → clarify 처리
- fulltext path safety: corpus 허용 경로 외 접근 차단

---

## Agent 4: fulltext-delivery

**파일**: `.claude/agents/fulltext-delivery.md`
**Model**: `claude-haiku-4-5-20251001`
**Color**: yellow

### 역할
resolved_document_path의 파일을 안전하게 읽어 원문 그대로 반환한다.
LLM 생성 없이 file read만 수행한다.

### 입력
```
path: str               # resolved document path
canonical_doc_id: str   # 안전 검증용
```

### 출력
```json
{
  "success": true,
  "content": "# 파일 네이밍 컨벤션\n\n...",
  "title": "파일 네이밍 컨벤션",
  "path": "...",
  "byte_size": 4200
}
```

### 안전 정책
- `allowed_corpus_dirs`에 포함된 경로만 허용
  - `docs/fe_chunk_docs/`
  - `docs/be_chunk_docs/`
- path traversal 방지: `os.path.abspath` 후 prefix 확인
- 최대 파일 크기: 500KB (초과 시 경고와 함께 부분 반환)
- 바이너리 파일 거부 (`.md` only)

### LLM 사용 정책
이 에이전트는 LLM을 사용하지 않는다.
모든 응답은 파일 원문이며 어떤 변형도 가하지 않는다.

---

## 기존 에이전트 활용

### rag-retriever (기존 유지)

chunk-level retrieval 전담. action-router가 다음 두 모드로 호출한다:

**section mode** (SummarizeHandler):
```
query: "{doc_title} 전체 섹션 수집"
filter: {canonical_doc_id: "...", index: "section_index"}
k: 50
```

**chunk mode** (ExtractHandler):
```
query: "{original_question}"
filter: {canonical_doc_id: "...", index: "chunk_index"}
k: 6
search_type: "mmr"
```

---

## 에이전트 호출 순서 (정상 플로우)

```
1. intent-classifier.invoke(question, metadata)
   → QueryUnderstandingResult

2. document-resolver.invoke(document_query, domain, stack)
   → DocumentResolutionResult

3. action-router.invoke(understanding, resolution, question)
   → 내부적으로 필요한 에이전트 추가 호출
   → FinalResponse
```

---

## 에러 처리 전략

| 실패 지점 | 대응 |
|-----------|------|
| intent-classifier 파싱 실패 | intent=extract fallback (기존 QA 경로) |
| document-resolver unresolved | clarify 응답 |
| document-resolver 다중 후보 | 후보 목록과 함께 선택 요청 |
| fulltext-delivery 경로 차단 | "해당 문서는 전문 제공이 지원되지 않습니다" |
| rag-retriever score 미달 | clarify 또는 fallback |
