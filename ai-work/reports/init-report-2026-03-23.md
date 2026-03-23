# Init 보고서 — developer-chat-bot-v3

작성일: 2026-03-23
기반 문서: ai-docs/rag-init-document.md

---

## 1. 현황 요약

### 기존 자산 (v3 시작 시점)

| 자산 | 내용 |
|------|------|
| docs/fe_chunk_docs/ | 프론트엔드 컨벤션 문서 14개 |
| docs/be_chunk_docs/ | 백엔드 컨벤션 문서 (Java/Kotlin/NestJS) 41개 |
| requirements.txt | langchain, chromadb, fastapi, openai 등 기본 스택 정의 |
| .env | OPENAI_API_KEY 설정 |
| .claude/agents/rag-retriever.md | chunk-level retrieval 전담 에이전트 (유지) |

### 핵심 전환 결정

rag-init-document.md 분석 결과, v3의 핵심 전환은 기술 개선이 아니라 **제품 패러다임 전환**이다.

- v2: chunk retrieval 기반 규칙 QA 시스템
- v3: document-resolution + intent-specific execution 시스템

---

## 2. 생성된 산출물

### 계획 문서 (ai-work/plans/)

| 파일 | 내용 |
|------|------|
| `architecture-v3.md` | 6개 레이어 아키텍처 전체 설계. 레이어별 LangChain 구성, 데이터 플로우, 인덱스 구조, 성공 기준 포함 |
| `langchain-integration.md` | 각 레이어를 LangChain 컴포넌트로 구현하는 상세 계획. Chain 구조, ChromaDB 구성, FastAPI 연동 포함 |
| `sub-agents-plan.md` | 4개 신규 에이전트 설계 (intent-classifier, document-resolver, action-router, fulltext-delivery) + 기존 rag-retriever 활용 방안 |

### 티켓 (ai-work/tickets/)

| 티켓 | 우선순위 | 내용 |
|------|----------|------|
| P0-TK-01-intent-classification.md | P0 | intent 분류 + action routing 도입 |
| P0-TK-02-document-resolution.md | P0 | document_index 구축 + 3단계 resolution |
| P0-TK-03-fulltext-delivery.md | P0 | fulltext = file read 경로 |
| P1-TK-04-document-index-alias.md | P1 | alias registry + section_index + SummarizeHandler |
| P1-TK-05-response-format-split.md | P1 | intent별 응답 포맷 분리 |
| P2-TK-06-compare-intent.md | P2 | compare intent 도입 |

### 제품 계약 (ai-docs/rules/)

| 파일 | 내용 |
|------|------|
| `product-contract.md` | 5개 intent 지원 명세, clarify 정책, 응답 품질 기준 |

### 에이전트 정의 (.claude/agents/)

| 파일 | 역할 | 모델 |
|------|------|------|
| `intent-classifier.md` | 의도 분류 | haiku |
| `document-resolver.md` | 문서 식별 | haiku |
| `action-router.md` | 핸들러 실행 조율 | sonnet |
| `fulltext-delivery.md` | 파일 직접 전달 | haiku |
| `rag-retriever.md` | chunk 검색 (기존 유지) | haiku |

### 모듈 폴더 구조 (src/)

```
src/
  convention_qa/
    query_understanding/    PLAN.md  ← IntentClassifier
    document_resolution/    PLAN.md  ← DocumentResolver
    action_routing/         PLAN.md  ← ActionRouter + handlers
    indexing/               PLAN.md  ← 3개 ChromaDB 인덱스 빌더
    response/               PLAN.md  ← 포맷터 + LLM chains + 프롬프트
  api/                      PLAN.md  ← FastAPI 레이어
```

---

## 3. 아키텍처 요약

```
User Query
    │
    ▼
[1] QueryUnderstanding     → intent + document_query + domain/stack/topic
    │                         (ChatOpenAI + PydanticOutputParser)
    ▼
[2] DocumentResolution     → canonical_doc_id + path + confidence
    │                         (exact → alias → ChromaDB semantic)
    ▼
[3] ActionRouting          → handler 선택
    │                         (dispatch dict, LangChain 불필요)
    ▼
[4] EvidenceLoading        → intent별 다른 전략
    │                         fulltext: file read
    │                         summarize: section_index 전체
    │                         extract: chunk_index MMR
    ▼
[5] ResponseGeneration     → intent별 다른 응답
    │                         fulltext: 원문 그대로
    │                         summarize/extract: LLMChain
    │                         discover: 결정적 포맷터
    ▼
[6] Validation             → path safety, evidence threshold, doc match
    │
    ▼
HTTP Response
```

---

## 4. 구현 우선순위

### P0 (핵심 기능 — 먼저 구현)

1. **P0-TK-01**: intent_classifier.py + action router dispatch
2. **P0-TK-02**: document_index 구축 + DocumentResolver
3. **P0-TK-03**: FulltextHandler (file read)

P0 완료 기준: 케이스 B ("전문 보여줘") E2E 통과

### P1 (품질 개선)

4. **P1-TK-04**: alias_registry.json + section_index + SummarizeHandler
5. **P1-TK-05**: 응답 포맷 분리

P1 완료 기준: 케이스 A ("내용 알려줘") + 케이스 C ("규칙만 알려줘") E2E 통과

### P2 (확장)

6. **P2-TK-06**: compare intent

---

## 5. 핵심 결정 사항

### 결정 1: fulltext는 LLM 미사용

fulltext = `open(path).read()`. 모델 호출 없음.
이유: 원문 변형 방지 + 비용 절감 + rag-init-document.md 원칙 4 준수.

### 결정 2: document_index는 chunk_index와 별도 컬렉션

chunk_index와 혼용하면 문서 단위 resolution이 불안정해진다.
ChromaDB 컬렉션 3개 분리: document_index / section_index / chunk_index.

### 결정 3: ActionRouter는 LangChain Agent 아님

LangChain AgentExecutor가 아니라 Python dispatch dict.
이유: 예측 불가능한 tool 선택 방지. 라우팅 로직이 코드로 명시적으로 표현.
복잡도가 높아지면 P2 이후 LangChain Tools 전환 고려.

### 결정 4: intent-classifier는 haiku 사용

분류 작업이므로 haiku로 충분. 응답 시간 단축.
action-router는 핸들러 조율이 복잡하므로 sonnet 사용.

### 결정 5: 기존 rag-retriever 에이전트 유지

extract intent와 summarize의 section assembly에서 활용.
chunk retrieval 전담 역할은 그대로 유지하고 action-router가 호출.

---

## 6. 다음 단계

P0-TK-01부터 순서대로 구현을 시작할 준비가 되었다.

구현 시작 전 확인 사항:
- [ ] OPENAI_API_KEY 유효성 확인 (.env)
- [ ] Python 가상환경 세팅 및 requirements.txt 설치
- [ ] ChromaDB persist_directory (.chroma/) 경로 확인
- [ ] alias_registry.json 초안 작성 (P1-TK-04 전에 draft 가능)
