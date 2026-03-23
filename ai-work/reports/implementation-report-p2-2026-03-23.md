# 구현 보고서 — P2 구현 완료

작성일: 2026-03-23
기반 보고서: ai-work/reports/implementation-report-p1-2026-03-23.md (P1 완료)

---

## 1. 개요

P1에서 구축한 5개 intent 파이프라인(fulltext/summarize/extract/discover/clarify) 위에
P2 티켓 TK-06(compare intent)을 구현하고, 전체 핸들러 단위 테스트를 작성했다.

---

## 2. P2-TK-06: CompareHandler 구현

### QueryUnderstandingResult 모델 확장

**파일**: `src/convention_qa/query_understanding/models.py`

`document_queries: list[str] | None` 필드 추가.
- compare intent에서 비교할 두 문서의 키워드 목록을 담는다.
- 기존 단일 문서 intent의 `document_query` 필드와 공존하며 하위 호환성을 유지한다.

### Intent 분류 프롬프트 업데이트

**파일**: `src/convention_qa/query_understanding/prompts.py`

- 메타데이터 추출 규칙에 `document_queries` 항목 추가
- 기존 비교 예시("FE vs BE 네이밍 차이점")를 "Java Spring vs Kotlin Spring" 구체적인 예시로 교체
- 비-compare 예시 4개에 `"document_queries": null` 필드 추가
- compare 예시 결과에 `document_queries` 배열 추가:
  ```json
  {
    "intent": "compare",
    "document_queries": ["Java Spring 네이밍 컨벤션", "Kotlin Spring 네이밍 컨벤션"],
    ...
  }
  ```

### HandlerContext 확장

**파일**: `src/convention_qa/action_routing/base_handler.py`

`HandlerContext`에 `understanding: Any = None` 필드 추가.
CompareHandler가 `document_queries`에 접근할 수 있도록 `QueryUnderstandingResult`를 전달한다.

### CompareHandler 구현

**파일**: `src/convention_qa/action_routing/compare_handler.py` (신규)

```
document_queries[0], document_queries[1]
  → DocumentResolver.resolve() × 2 (각 문서 개별 resolution)
  → section_index.get(where={"canonical_doc_id": ...}) × 2
  → ChatPromptTemplate | ChatOpenAI(gpt-4o-mini, temperature=0)
  → format_compare() 포맷팅
```

- `document_queries`가 없거나 1개 이하인 경우 → `format_not_found` graceful 반환
- 개별 문서 resolution 실패(None 반환) 시 빈 섹션으로 처리 (graceful)
- section_index 조회 실패 시 "(섹션 데이터 없음)" 텍스트로 LLM 호출

LLM 프롬프트:
- SYSTEM: 두 문서 공통점/차이점/충돌 지점 분석 요청
- HUMAN: 문서 A·B 섹션 텍스트 + 질문 → 표 또는 항목 목록 형식 응답 요청

### router.py 수정

**파일**: `src/convention_qa/action_routing/router.py`

| 변경 항목 | 내용 |
|-----------|------|
| `HANDLER_MAP` 추가 | `("compare", True)`, `("compare", False)` → `"CompareHandler"` |
| `_instantiate` 분기 추가 | `CompareHandler` lazy import |
| `route` 메서드 수정 | `resolved=False` 예외 목록에 `"compare"` 추가 |
| `route_and_execute` 수정 | `HandlerContext` 생성 시 `understanding=understanding` 전달 |

### 포맷터 추가

**파일**: `src/convention_qa/response/formatters.py`

| 함수 | 출력 형식 |
|------|-----------|
| `format_compare(title_a, title_b, comparison_text, path_a, path_b)` | `## {title_a} vs {title_b} 비교\n\n{comparison_text}\n\n> 출처: ...` |

---

## 3. 단위 테스트 작성

**신규 디렉터리**: `tests/`

모든 외부 의존(ChromaDB, OpenAI API)을 `unittest.mock.patch`로 대체하는 순수 단위 테스트.

### 테스트 파일 목록

| 파일 | 테스트 수 | 주요 검증 항목 |
|------|-----------|----------------|
| `tests/test_summarize_handler.py` | 6개 | 섹션 수집 → LLM 요약 → answer_type="summarize", 빈 섹션 graceful |
| `tests/test_extract_handler.py` | 8개 | MMR 청크 검색 → QA 답변 → answer_type="extract", 빈 청크 → not_found |
| `tests/test_discover_handler.py` | 11개 | resolved=True → 헤딩 목록 수집, resolved=False → clarify 후보 안내 |
| `tests/test_compare_handler.py` | 16개 | document_queries 없음/1개 → not_found, 두 문서 정상 비교, resolution 실패 graceful |

**총 41개 단위 테스트**

### test_compare_handler.py 테스트 구조

```
TestHandleNotFound (3개)
  - document_queries=None → not_found
  - document_queries=["문서A"] (1개) → not_found
  - document_queries=[] (빈 리스트) → not_found

TestHandleNormalCase (4개)
  - 두 문서 모두 resolve 성공 → answer_type="compare", sources 두 문서 포함
  - _resolve 2회, _get_sections 2회, _compare 1회 호출 검증
  - _compare 인자(title_a/title_b/sections_a/sections_b/question) 정확성 검증
  - 최종 answer에 두 제목 포함 검증

TestHandleResolutionFailure (4개)
  - 두 번째 _resolve → None 반환 → 여전히 answer_type="compare"
  - None 반환 시 query 문자열을 title_b로 fallback
  - None 반환 시 _get_sections에 빈 문자열 전달
  - _compare의 sections_b → "(섹션 데이터 없음)"

TestFormatSections (5개)
  - _format_sections([]) → "(섹션 데이터 없음)"
  - heading/content 포함, 섹션 간 \n\n 구분, 빈 content 처리
  - _get_sections("") → [] (경계 케이스)
```

---

## 4. 전체 변경 파일 목록

### 신규 파일 (6개)

```
src/convention_qa/action_routing/
  compare_handler.py

tests/
  __init__.py
  test_summarize_handler.py
  test_extract_handler.py
  test_discover_handler.py
  test_compare_handler.py
```

### 수정 파일 (7개)

```
src/convention_qa/query_understanding/models.py     — document_queries 필드 추가
src/convention_qa/query_understanding/prompts.py    — compare 예시 + document_queries 추출 추가
src/convention_qa/action_routing/base_handler.py    — HandlerContext.understanding 추가
src/convention_qa/action_routing/router.py          — compare 라우팅 + understanding 전달
src/convention_qa/response/formatters.py            — format_compare 추가
src/convention_qa/response/__init__.py              — format_compare export
src/convention_qa/action_routing/__init__.py        — CompareHandler export
requirements.txt                                    — pytest>=8.0.0, langchain-chroma>=0.1.0 추가
```

---

## 5. E2E 데이터 플로우 (P2 추가 케이스)

### 케이스 E: "두 문서 비교해줘" (compare)

```
POST /api/v1/query { question: "Java Spring과 Kotlin Spring 네이밍 컨벤션 차이점 알려줘" }
  │
  ▼ [IntentClassifier] → intent=compare, document_queries=["Java Spring 네이밍 컨벤션", "Kotlin Spring 네이밍 컨벤션"]
  │
  ▼ [ActionRouter] → CompareHandler (resolved 여부 무관)
  │
  ▼ [CompareHandler]
      DocumentResolver.resolve("Java Spring 네이밍 컨벤션") → canonical_doc_id_a
      DocumentResolver.resolve("Kotlin Spring 네이밍 컨벤션") → canonical_doc_id_b
      section_index.get(where={"canonical_doc_id": canonical_doc_id_a}) → sections_a
      section_index.get(where={"canonical_doc_id": canonical_doc_id_b}) → sections_b
      → gpt-4o-mini 비교 분석
      → "## Java Spring 네이밍 컨벤션 vs Kotlin Spring 네이밍 컨벤션 비교\n\n..."
```

---

## 6. P2 완료 기준 체크

| 기준 | 상태 |
|------|------|
| compare intent 분류 (document_queries 추출) | 완료 |
| 두 문서 동시 resolution 로직 구현 | 완료 |
| compare 응답 포맷 정의 및 구현 | 완료 |
| router.py compare 라우팅 연결 | 완료 |
| 단위 테스트 41개 작성 | 완료 |
| requirements.txt pytest/langchain-chroma 추가 | 완료 |

---

## 7. 다음 단계 (운영 준비)

- [ ] **ingest 실행**: `python scripts/ingest.py` — ChromaDB section_index / chunk_index 빌드 (OPENAI_API_KEY 필요)
- [ ] **단위 테스트 실행**: `python -m pytest tests/ -v`
- [ ] **E2E 검증**: 케이스 A(summarize), B(fulltext), C(extract), D(discover), E(compare) 실제 API 호출 테스트
- [ ] **intent_classifier compare 분류 통합 테스트**: 실제 LLM 호출로 document_queries 추출 정확도 검증
