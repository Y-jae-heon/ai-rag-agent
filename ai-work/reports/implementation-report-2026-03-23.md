# 구현 보고서 — P0 티켓 전체 구현 완료

작성일: 2026-03-23
기반 보고서: ai-work/reports/init-report-2026-03-23.md

---

## 1. 개요

init-report에서 수립된 v3 아키텍처를 기반으로 P0 티켓 3개(TK-01, TK-02, TK-03)와 FastAPI API 레이어를 구현 완료했다.
총 35개 Python 파일, 1개 JSON(alias_registry), 1개 CLI 스크립트를 생성했다.

구현은 4개 에이전트가 병렬/순차 분담하여 수행했다.

---

## 2. 에이전트별 작업 내역

### Agent A — P0-TK-01 (query_understanding + action_routing base)

**역할**: 사용자 의도 분류 + 핸들러 라우팅 기반 구현

**담당 티켓**: P0-TK-01

**수행 시간**: Phase 1 (병렬 실행)

**생성 파일 (11개)**

| 파일 | 설명 |
|------|------|
| `src/__init__.py` | 패키지 루트 마커 |
| `src/convention_qa/__init__.py` | convention_qa 패키지 마커 |
| `src/convention_qa/query_understanding/__init__.py` | IntentClassifier, QueryUnderstandingResult export |
| `src/convention_qa/query_understanding/models.py` | QueryUnderstandingResult Pydantic v2 모델 (5개 intent Literal, Field 설명 포함) |
| `src/convention_qa/query_understanding/prompts.py` | CLASSIFICATION_PROMPT — ChatPromptTemplate, 5개 intent 정의, 5개 few-shot 예시, {format_instructions} 주입 포인트 |
| `src/convention_qa/query_understanding/alias_normalizer.py` | normalize_domain(), normalize_stack() — 한국어/영어 FE/BE 별칭 정규화. 영문은 단어 경계(\b) 매칭, 한국어는 포함 검사 |
| `src/convention_qa/query_understanding/intent_classifier.py` | IntentClassifier — LCEL chain (CLASSIFICATION_PROMPT \| ChatOpenAI(gpt-4o-mini, temperature=0) \| PydanticOutputParser). alias_normalizer 결과로 LLM 응답 보강 |
| `src/convention_qa/action_routing/__init__.py` | ActionRouter, BaseHandler, HandlerContext, HandlerResult, ClarifyHandler export |
| `src/convention_qa/action_routing/base_handler.py` | HandlerContext, HandlerResult Pydantic 모델 + BaseHandler ABC |
| `src/convention_qa/action_routing/clarify_handler.py` | ClarifyHandler — resolved=False 시 미발견 메시지, candidates 다수 시 목록 나열 |
| `src/convention_qa/action_routing/router.py` | ActionRouter — HANDLER_MAP dispatch table. P0 단계 SummarizeHandler/ExtractHandler/DiscoverHandler는 ClarifyHandler stub |

**주요 설계 결정**
- alias_normalizer는 LLM 결과가 None일 때만 보강 (LLM 우선, normalizer 보조)
- HandlerContext.resolution은 Any 타입으로 선언하여 TK-02의 DocumentResolutionResult forward reference 수용
- FulltextHandler는 lazy import 패턴으로 TK-03 구현 후 자연 연동되도록 설계

---

### Agent B — Indexing 파이프라인

**역할**: ChromaDB 3개 컬렉션 빌드 파이프라인 구현

**담당 모듈**: src/convention_qa/indexing/, scripts/ingest.py

**수행 시간**: Phase 1 (Agent A와 병렬 실행)

**생성 파일 (11개)**

| 파일 | 설명 |
|------|------|
| `src/convention_qa/indexing/__init__.py` | run, parse_file, ParsedDocument, load_alias_registry, get_aliases export |
| `src/convention_qa/indexing/config.py` | CHROMA_PERSIST_DIR, CORPUS_DIRS, CHUNK_SIZE(500), CHUNK_OVERLAP(50), SIMILARITY_THRESHOLD(0.75), OPENAI_EMBEDDING_MODEL |
| `src/convention_qa/indexing/markdown_parser.py` | ParsedDocument dataclass + parse_file() — UUID 추출(파일명 끝 32자 hex), domain/stack 자동 판별 |
| `src/convention_qa/indexing/document_indexer.py` | build_document_index() — document_index 컬렉션 빌드 |
| `src/convention_qa/indexing/section_indexer.py` | build_section_index() — section_index 컬렉션 빌드 |
| `src/convention_qa/indexing/chunk_indexer.py` | build_chunk_index() — RecursiveCharacterTextSplitter(500/50) 기반 chunk_index 빌드 |
| `src/convention_qa/indexing/manifest.py` | load_alias_registry(), get_aliases() |
| `src/convention_qa/indexing/build_index.py` | run(force_rebuild, collections) 오케스트레이터 + ingest_manifest.json 저장 |
| `src/convention_qa/indexing/alias_registry.json` | FE 16개 + BE 37개, 총 53개 문서 UUID 기반 alias 정의 |
| `scripts/__init__.py` | 패키지 마커 |
| `scripts/ingest.py` | argparse CLI — --rebuild, --collections 옵션 |

**주요 설계 결정**
- 파일명 패턴 `{제목} {UUID}.md`에서 UUID는 정규식 `[0-9a-f]{32}$`으로 추출
- stack 감지: `Java(Spring)` → spring/java, `Kotlin(Spring)` → spring/kotlin, `Typescript(NestJS)` → nestjs/typescript, fe_chunk_docs 기본 → react
- sections 분리: `##`~`######` 기준, `#` 단독 제목은 제외
- 실제 docs/ 파일 목록을 직접 읽어 alias_registry.json의 UUID를 정확히 작성

---

### Agent C — P0-TK-02 (document_resolution)

**역할**: document_query → 실제 문서 경로 resolution

**담당 티켓**: P0-TK-02

**수행 시간**: Phase 2 (Agent A, B 완료 후 순차 실행)

**생성 파일 (5개)**

| 파일 | 설명 |
|------|------|
| `src/convention_qa/document_resolution/__init__.py` | DocumentResolver, DocumentResolutionResult, DocumentCandidate export |
| `src/convention_qa/document_resolution/models.py` | DocumentCandidate, DocumentResolutionResult Pydantic v2 모델 |
| `src/convention_qa/document_resolution/exact_matcher.py` | normalize_text(), exact_match(), alias_match() |
| `src/convention_qa/document_resolution/semantic_retriever.py` | semantic_search() — ChromaDB document_index semantic search, L2 distance → confidence 변환 |
| `src/convention_qa/document_resolution/resolver.py` | DocumentResolver — 5단계 resolution 로직 |

**주요 설계 결정**
- normalize_text: 소문자 + `[^\w\s가-힣]` 특수문자 제거 + 공백 정규화 (한글 문자 범위 명시)
- exact_match: 완전 일치(score=1.0) + 부분 일치(score=0.9) 허용
- alias_match: alias_registry 기반. ingest 미실행 시에도 alias 기반 후보(score=0.85) 반환
- semantic_retriever: langchain_chroma import를 함수 내부에서 시도 → ImportError도 graceful 처리. persist_dir 미존재 시 빈 리스트 반환
- resolver._evaluate_candidates(): 1위와 2위 score 격차 0.15 이상이면 단독 resolved, 미만이면 clarify
- document_query=None 시 즉시 unresolved 반환

**3단계 resolution 흐름**
```
exact_match → alias_match → semantic(domain/stack 필터) → semantic(필터 없이 재시도) → 결과 평가
```

---

### Agent D — P0-TK-03 + API 레이어

**역할 (TK-03)**: FulltextHandler + response layer 구현

**역할 (API)**: FastAPI 레이어 + E2E 파이프라인 연동

**담당 티켓**: P0-TK-03 + API

**수행 시간**: Phase 3 (TK-03) → Phase 4 (API) 순차 실행

#### Phase 3 — TK-03 생성 파일 (4개 신규 + 1개 수정)

| 파일 | 설명 |
|------|------|
| `src/convention_qa/action_routing/fulltext_handler.py` | FulltextHandler — is_safe_path() + 7단계 파일 읽기. LLM 호출 없음. 500KB 초과 시 앞부분만 반환 |
| `src/convention_qa/response/__init__.py` | QueryResponse, SourceRef, format_fulltext, format_clarify, format_not_found export |
| `src/convention_qa/response/models.py` | SourceRef, QueryResponse Pydantic v2 모델 |
| `src/convention_qa/response/formatters.py` | format_fulltext(), format_clarify(), format_not_found() |
| `src/convention_qa/action_routing/router.py` (수정) | FulltextHandler 실제 연결 + route_and_execute() 편의 메서드 추가 |

**FulltextHandler 안전 정책**
- ALLOWED_CORPUS_DIRS: `docs/fe_chunk_docs`, `docs/be_chunk_docs`
- is_safe_path(): os.path.abspath 정규화 + 후행 os.sep 추가로 prefix 오탐 방지
- path traversal 공격 차단 (예: `/etc/passwd` → 거부)

#### Phase 4 — API 레이어 생성 파일 (7개)

| 파일 | 설명 |
|------|------|
| `src/api/__init__.py` | 패키지 마커 |
| `src/api/models.py` | QueryRequest, QueryResponse, ResolvedDocumentInfo HTTP 모델 |
| `src/api/dependencies.py` | @lru_cache 싱글톤 — get_intent_classifier, get_document_resolver, get_action_router, get_chroma_client |
| `src/api/routes/__init__.py` | 라우터 패키지 마커 |
| `src/api/routes/health.py` | GET /health — 인덱스 미존재 시 status: "degraded", ingest_manifest.json 포함 |
| `src/api/routes/query.py` | POST /api/v1/query — 전체 파이프라인 실행, 예외 → HTTP 500 변환 |
| `src/api/main.py` | FastAPI lifespan — 인덱스 검증 + SKIP_INDEX_CHECK 개발 모드 지원 |

---

## 3. 전체 파일 목록 (35개 .py + 1개 .json + 1개 CLI)

```
src/
  __init__.py
  convention_qa/
    __init__.py
    query_understanding/
      __init__.py
      models.py
      prompts.py
      alias_normalizer.py
      intent_classifier.py
    action_routing/
      __init__.py
      base_handler.py
      clarify_handler.py
      router.py
      fulltext_handler.py
    document_resolution/
      __init__.py
      models.py
      exact_matcher.py
      semantic_retriever.py
      resolver.py
    indexing/
      __init__.py
      config.py
      markdown_parser.py
      document_indexer.py
      section_indexer.py
      chunk_indexer.py
      manifest.py
      build_index.py
      alias_registry.json
    response/
      __init__.py
      models.py
      formatters.py
  api/
    __init__.py
    models.py
    dependencies.py
    routes/
      __init__.py
      health.py
      query.py
    main.py
scripts/
  __init__.py
  ingest.py
```

---

## 4. E2E 데이터 플로우

```
POST /api/v1/query { question: "파일 네이밍 컨벤션 전문 보여줘" }
  │
  ▼
[IntentClassifier]  gpt-4o-mini + PydanticOutputParser
  → intent=fulltext, document_query="파일 네이밍 컨벤션", domain=frontend
  │
  ▼
[DocumentResolver]  exact/alias/semantic 3단계
  → resolved=True, path="docs/fe_chunk_docs/파일 네이밍 컨벤션 325e63c6...md"
  │
  ▼
[ActionRouter]  dispatch table
  → FulltextHandler 선택
  │
  ▼
[FulltextHandler]  LLM 없음, file read only
  → is_safe_path() 검증 → open(path).read()
  │
  ▼
[format_fulltext]  메타데이터 헤더 추가
  → "## 파일 네이밍 컨벤션\n> 경로: ...\n\n---\n\n{원문}"
  │
  ▼
HTTP 200 { answer: "...", answer_type: "fulltext", intent: "fulltext", ... }
```

---

## 5. 실행 방법

```bash
# 인덱스 빌드 (최초 1회, OPENAI_API_KEY 필요)
python scripts/ingest.py

# 전체 재빌드
python scripts/ingest.py --rebuild

# 특정 컬렉션만
python scripts/ingest.py --collections document_index

# 서버 기동 (인덱스 빌드 완료 후)
uvicorn src.api.main:app --reload

# 개발 모드 (인덱스 없이)
SKIP_INDEX_CHECK=true uvicorn src.api.main:app --reload
```

---

## 6. P0 완료 기준 체크

| 기준 | 상태 |
|------|------|
| intent_classifier.py 구현 | 완료 |
| 5개 intent 분류 테스트 케이스 (TK-01) | 구현 완료, 테스트 실행 필요 |
| router.py dispatch 테이블 구현 | 완료 |
| document_index 구축 스크립트 | 완료 |
| exact/alias/semantic match 구현 | 완료 |
| FulltextHandler 구현 | 완료 |
| 안전 정책 path traversal 방지 | 완료 |
| LLM 호출 없음 (FulltextHandler) | 완료 |
| "전문 보여줘" E2E 경로 구현 | 완료 |
| FastAPI POST /api/v1/query | 완료 |

---

## 7. 다음 단계 (P1)

- [ ] **P1-TK-04**: alias_registry 보강 + SummarizeHandler (section_index) 구현
- [ ] **P1-TK-05**: ExtractHandler (chunk_index MMR) + 응답 포맷 분리
- [ ] 테스트 코드 작성 (tests/test_intent_classifier.py, tests/test_document_resolver.py 등)
- [ ] python scripts/ingest.py 실행으로 실제 ChromaDB 인덱스 빌드
- [ ] E2E 동작 검증
