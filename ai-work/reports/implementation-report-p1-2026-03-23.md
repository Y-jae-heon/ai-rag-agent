# 구현 보고서 — P1 티켓 전체 구현 완료

작성일: 2026-03-23
기반 보고서: ai-work/reports/implementation-report-2026-03-23.md (P0 완료)

---

## 1. 개요

P0에서 구축한 fulltext E2E 파이프라인 위에 P1 티켓 2개(TK-04, TK-05)를 구현 완료했다.
총 3개 핸들러 신규 구현, 3개 포맷터 추가, alias_registry 포맷 업그레이드, 관련 코드 호환 수정을 수행했다.

---

## 2. 티켓별 작업 내역

### P1-TK-04: alias_registry 보강 + SummarizeHandler

#### alias_registry.json 포맷 업그레이드

**변경 전**
```json
{
  "325e63c6fa9780149d90e16c61f7f0e2": ["file naming", "파일명 규칙", ...]
}
```

**변경 후**
```json
{
  "325e63c6fa9780149d90e16c61f7f0e2": {
    "title": "파일 네이밍 컨벤션",
    "aliases": ["file naming", "파일명 규칙", ...],
    "domain": "frontend",
    "stack": "react",
    "topic": "naming"
  }
}
```

- 54개 문서 전체 커버 (FE 16개 + Java 17개 + Kotlin 10개 + NestJS 11개)
- topic 분류: naming / architecture / pattern / git / fsd / database / logging / security / testing / dependency / transaction / exception / datetime / api / workflow / overview / utility

#### 코드 호환 수정

| 파일 | 변경 내용 |
|------|-----------|
| `src/convention_qa/indexing/manifest.py` | `load_alias_registry` 반환 타입 `dict[str, dict]`로 변경. `get_aliases`는 구형/신형 포맷 모두 처리 |
| `src/convention_qa/document_resolution/exact_matcher.py` | `alias_match` — `entry`가 list이면 그대로, dict이면 `.get("aliases", [])` 추출 |

#### SummarizeHandler 구현

**파일**: `src/convention_qa/action_routing/summarize_handler.py`

```
section_index (canonical_doc_id filter)
  → 전체 섹션 수집 (heading + content)
  → ChatPromptTemplate | ChatOpenAI(gpt-4o-mini, temperature=0)
  → format_summarize() 포맷팅
```

- section_index `vectorstore.get(where={"canonical_doc_id": ...})` 방식 — similarity search 아님
- LLM 프롬프트: 3~6개 항목 번호 목록 + 굵은 글씨 제목 형식 요구
- section_index 미존재 시 graceful 처리 → "(섹션 데이터 없음)" 텍스트로 LLM 호출

---

### P1-TK-05: ExtractHandler + DiscoverHandler + 응답 포맷 분리

#### ExtractHandler 구현

**파일**: `src/convention_qa/action_routing/extract_handler.py`

```
chunk_index MMR (canonical_doc_id filter, k=4, fetch_k=20)
  → 관련 청크 수집
  → ChatPromptTemplate | ChatOpenAI(gpt-4o-mini, temperature=0)
  → format_extract() 포맷팅 (§섹션 출처 포함)
```

- resolved=False여도 canonical_doc_id 없이는 graceful → `format_not_found` 반환
- MMR 검색 실패 시 빈 리스트 반환 → `format_not_found`

#### DiscoverHandler 구현

**파일**: `src/convention_qa/action_routing/discover_handler.py`

```
resolved=True:
  section_index에서 섹션 헤딩 목록 수집 (LLM 없음)
  → format_discover() — 제목/경로/도메인/스택/주요섹션 구조화

resolved=False:
  resolution.candidates → format_clarify() 다중 후보 안내
```

#### 포맷터 추가

**파일**: `src/convention_qa/response/formatters.py`

| 함수 | 출력 형식 |
|------|-----------|
| `format_summarize(title, summary, path)` | `## {title} 요약\n\n{summary}\n\n> 출처: ...` |
| `format_discover(title, path, domain, stack, section_headings)` | `## 문서 발견 결과\n\n**제목**: ...\n**경로**: ...\n**도메인**: ...\n**주요 섹션**: ...` |
| `format_extract(title, answer_text, source_sections, path)` | `{answer_text}\n\n> 근거: {title} §섹션1, §섹션2` |

#### router.py stub 제거

P0 단계에서 ClarifyHandler로 fallback하던 stub을 실제 핸들러로 교체:

```python
# P1 완료 — 전체 라우팅 활성화
("fulltext", True)  → FulltextHandler
("summarize", True) → SummarizeHandler
("extract", True)   → ExtractHandler
("extract", False)  → ExtractHandler
("discover", True)  → DiscoverHandler
("discover", False) → DiscoverHandler
```

---

## 3. 전체 변경 파일 목록

### 신규 파일 (3개)

```
src/convention_qa/action_routing/
  summarize_handler.py
  extract_handler.py
  discover_handler.py
```

### 수정 파일 (6개)

```
src/convention_qa/indexing/alias_registry.json   — 포맷 업그레이드 (54개 문서)
src/convention_qa/indexing/manifest.py           — 신형 포맷 지원
src/convention_qa/document_resolution/exact_matcher.py — 포맷 호환
src/convention_qa/response/formatters.py         — format_summarize/discover/extract 추가
src/convention_qa/response/__init__.py           — 신규 포맷터 export
src/convention_qa/action_routing/__init__.py     — 신규 핸들러 export
src/convention_qa/action_routing/router.py       — stub 제거, 핸들러 실제 연결
```

---

## 4. E2E 데이터 플로우 (P1 추가 케이스)

### 케이스 A: "내용 알려줘" (summarize)

```
POST /api/v1/query { question: "파일 네이밍 컨벤션 내용 알려줘" }
  │
  ▼ [IntentClassifier] → intent=summarize, document_query="파일 네이밍 컨벤션"
  │
  ▼ [DocumentResolver] → resolved=True, canonical_doc_id="325e63c6..."
  │
  ▼ [ActionRouter] → SummarizeHandler
  │
  ▼ [SummarizeHandler]
      section_index.get(where={"canonical_doc_id": "325e63c6..."})
      → 섹션 목록 수집
      → gpt-4o-mini 요약
      → "## 파일 네이밍 컨벤션 요약\n\n1. **컴포넌트 파일**: PascalCase ..."
```

### 케이스 C: "규칙만 알려줘" (extract)

```
POST /api/v1/query { question: "테스트 파일 네이밍 규칙 알려줘" }
  │
  ▼ [IntentClassifier] → intent=extract, document_query="파일 네이밍 컨벤션"
  │
  ▼ [DocumentResolver] → resolved=True
  │
  ▼ [ActionRouter] → ExtractHandler
  │
  ▼ [ExtractHandler]
      chunk_index.mmr(question, filter={"canonical_doc_id": ...}, k=4)
      → gpt-4o-mini QA
      → "테스트 파일은 `{kebab-case}.spec.ts` 형식을 따릅니다.\n\n> 근거: 파일 네이밍 컨벤션 §테스트 파일"
```

### 케이스 D: "이런 문서 있어?" (discover)

```
POST /api/v1/query { question: "파일 네이밍 컨벤션 문서 있어?" }
  │
  ▼ [IntentClassifier] → intent=discover
  │
  ▼ [DocumentResolver] → resolved=True
  │
  ▼ [ActionRouter] → DiscoverHandler
  │
  ▼ [DiscoverHandler] (LLM 없음)
      section_index에서 섹션 헤딩 수집
      → "## 문서 발견 결과\n\n**제목**: 파일 네이밍 컨벤션\n**도메인**: Frontend / React ..."
```

---

## 5. P1 완료 기준 체크

| 기준 | 상태 |
|------|------|
| alias_registry.json 54개 문서 커버리지 | 완료 |
| title / domain / stack / topic 메타데이터 추가 | 완료 |
| manifest.py / exact_matcher.py 포맷 호환 | 완료 |
| SummarizeHandler section_index 조회 구현 | 완료 |
| SummarizeHandler LLMChain 3~6개 요약 | 완료 |
| ExtractHandler chunk_index MMR 검색 | 완료 |
| ExtractHandler LLMChain QA 답변 | 완료 |
| DiscoverHandler deterministic 포맷 | 완료 |
| 5개 intent 포맷터 구현 (fulltext/summarize/extract/discover/clarify) | 완료 |
| router.py stub 전체 제거 | 완료 |

---

## 6. 다음 단계 (P2 + 운영 준비)

- [ ] **ingest 실행**: `python scripts/ingest.py` — ChromaDB section_index / chunk_index 빌드 (OPENAI_API_KEY 필요)
- [ ] **E2E 검증**: 케이스 A(summarize), B(fulltext), C(extract), D(discover) 실제 API 호출 테스트
- [ ] **P2-TK-06**: compare intent 도입 (두 문서/스택 간 규칙 비교)
- [ ] **테스트 코드**: `tests/test_summarize_handler.py`, `tests/test_extract_handler.py` 등
