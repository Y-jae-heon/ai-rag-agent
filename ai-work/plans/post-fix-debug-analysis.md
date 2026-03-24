# RAG 검색 개선 후속 디버깅 분석

> 작업일: 2026-03-24
> 대상 커밋: `ff73d8f` (ff73d8f ai: P2까지 완료)
> 검증 대상: `ai-work/reports/2026-03-24-rag-search-improvement.md`에 기재된 Fix 1/2/3 적용 결과

---

## 개요

이전 작업 보고서에서 "해결됨"으로 표기된 두 시나리오가 실제 테스트에서 모두 실패하며, 추가로 500 Internal Server Error가 발생하였다. 본 문서는 각 실패의 원인을 코드 레벨에서 추적하고 실제 테스트 결과를 첨부한다.

---

## 실제 테스트 결과

### 서버 기동 명령

```bash
uvicorn src.api.main:app --port 8765
```

---

### Scenario A — "Java에서 트랜잭션 관리하는 법 알려줘"

**요청**:
```bash
curl -X POST http://localhost:8765/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Java에서 트랜잭션 관리하는 법 알려줘"}'
```

**실제 응답 (HTTP 200, 그러나 오답)**:
```json
{
  "answer": "요청하신 문서를 찾을 수 없습니다. 문서명을 다시 확인하거나 더 구체적인 키워드로 질문해 주세요.",
  "answer_type": "clarify",
  "intent": "extract",
  "resolved_document": null,
  "sources": []
}
```

**기대 결과**: `resolution_strategy != "unresolved"`, `answer_type = "extract"`

**서버 로그 (핵심 발췌)**:
```
understanding = intent='extract' document_query=None stack='Java' topic='트랜잭션 관리' ...
[semantic_search] query='트랜잭션 관리' | 필터=(domain=backend, stack=Java) | 결과 0건
[semantic_search] query='트랜잭션 관리' | 필터=(domain=None, stack=None) | 결과 5건
  [1] title='Git PR 템플릿'         score=0.3431  domain=frontend  stack=react
  [2] title='Git 협업 컨벤션 개요'   score=0.3409  domain=frontend  stack=react
  [3] title='FSD 레이어드 아키텍처 README 템플릿'  score=0.3406
  [4] title='Typescript(NestJS) 레이어드 아키텍처'  score=0.3398
  [5] title='폴더 네이밍 컨벤션'     score=0.3395
resolution = resolved=False, resolution_strategy='semantic'
handler_result = answer_type='not_found'
```

---

### Scenario B — "FSD 구조 규칙 알려줘"

**요청**:
```bash
curl -X POST http://localhost:8765/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "FSD 구조 규칙 알려줘"}'
```

**실제 응답 (HTTP 500)**:
```json
{
  "detail": "질의 처리 중 오류가 발생했습니다: 1 validation error for DocumentResolutionResult\nresolution_strategy\n  Input should be 'exact', 'alias', 'semantic' or 'unresolved' [type=literal_error, input_value='keyword_tiebreak', input_type=str]"
}
```

**서버 로그 (핵심 발췌)**:
```
understanding = intent='extract' document_query='FSD 구조 규칙' ...
[semantic_search] query='FSD 구조 규칙' | 필터=(domain=None, stack=None) | 결과 5건
  [1] title='Git PR 템플릿'             score=0.3465
  [2] title='FSD 레이어드 아키텍처 개요' score=0.3413
  [3] title='Kotlin(Spring) 테스트 코드 컨벤션'  score=0.3411
  [4] title='Typescript(NestJS) 레이어드 아키텍처 - 서비스 코드 패턴'  score=0.3395
  [5] title='Typescript(NestJS) 레이어드 아키텍처 디렉토리 구조'  score=0.3391
→ score_gap=0.0052 < 0.15 → keyword_tiebreak 시도
→ specific_tokens=["FSD"] → 'FSD 레이어드 아키텍처 개요' 1건 매칭 → tiebreak 성공
→ DocumentResolutionResult(resolution_strategy='keyword_tiebreak') → Pydantic ValidationError → 500
```

---

## 버그 분석

### Bug 1: Fix 3 실질적 미작동 — `alias_normalizer` 한국어 접사 단어 경계 문제

**관련 파일**: `src/convention_qa/query_understanding/alias_normalizer.py:133-136`

**현상**: `normalize_stack("Java에서 트랜잭션 관리하는 법 알려줘")` → `None`

**기대값**: `"spring"` (`"Java"` alias → `"spring"` 정규화)

**원인**:

`_matches_alias()` 함수에서 ASCII alias에 대해 Python `re` 모듈의 `\b` 단어 경계를 사용한다:

```python
# alias_normalizer.py:133-136
if alias.isascii():
    pattern = r"\b" + re.escape(alias) + r"\b"
    return bool(re.search(pattern, text))
```

Python `re`의 `\b`는 `\w`(단어 문자)와 `\W`(비단어 문자) 사이의 경계를 의미한다. 기본적으로 `\w`는 유니코드 문자를 포함하므로, 한국어 글자도 `\w`로 분류된다.

따라서 `"Java에서"` 에서:
- `a` → `\w` (ASCII 알파벳)
- `에` → `\w` (유니코드 한글)
- `a` ↔ `에` 사이에 단어 경계(`\b`) 없음

결과: `\bJava\b`가 `"Java에서"` 에 매칭되지 않음 → `normalize_stack` → `None`

**연쇄 실패**:

```
normalize_stack(question) = None (pre_stack = None)
  → Fix 3 조건: if pre_stack is not None → 실행 안됨
  → LLM이 반환한 stack='Java' 그대로 유지
  → semantic_search(filter={'stack': {'$eq': 'Java'}}) → 0건 (ChromaDB에는 'spring' 저장)
  → fallback 필터 없이 재검색 → 5건 반환, 모두 topic과 무관한 문서
  → score_gap = 0.0022 < 0.15, keyword_tiebreak("트랜잭션 관리")
    → specific_tokens = ["트랜잭션"] (len=4 ≥ 3)
    → "트랜잭션" 포함 title: 0건 → tiebreak 실패
  → resolved=False, resolution_strategy='semantic'
  → ExtractHandler(canonical_doc_id="") → chunks=[] → not_found
```

---

### Bug 2: Fix 2(keyword_tiebreak) 500 Error — `DocumentResolutionResult.resolution_strategy` Literal 미등록

**관련 파일**:
- `src/convention_qa/document_resolution/resolver.py:217-225` (값 생성)
- `src/convention_qa/document_resolution/models.py:23` (타입 정의)

**현상**: `_keyword_tiebreak()` 성공 후 `DocumentResolutionResult` 생성 시 Pydantic 검증 오류로 500

**원인**:

`resolver.py`에서 tiebreak 성공 시:
```python
# resolver.py:217-225
return DocumentResolutionResult(
    resolved=True,
    ...
    resolution_strategy="keyword_tiebreak",  # ← 신규 값
    ...
)
```

그러나 `models.py`의 `DocumentResolutionResult` 모델에 `"keyword_tiebreak"`가 등록되어 있지 않다:
```python
# models.py:23
resolution_strategy: Literal["exact", "alias", "semantic", "unresolved"]
#                                          ← "keyword_tiebreak" 미포함!
```

Fix 2 구현 시 `resolver.py`에만 새 값을 추가하고, `models.py`의 Literal 타입 정의를 갱신하지 않아 불일치 발생.

**연쇄 실패**:

```
keyword_tiebreak 성공 → DocumentResolutionResult(resolution_strategy='keyword_tiebreak')
  → Pydantic ValidationError: Input should be 'exact', 'alias', 'semantic' or 'unresolved'
  → query.py의 except 블록 → HTTPException(500) 반환
```

---

### Bug 3 (부수 결함): `answer_type="not_found"` Literal 불일치

**관련 파일**:
- `src/api/routes/query.py:48-49` (valid_answer_types 집합)
- `src/convention_qa/action_routing/extract_handler.py:43` (not_found 반환)

**현상**: ExtractHandler, CompareHandler 등이 `answer_type="not_found"`를 반환하지만, API 레이어에서 `"clarify"`로 silently 변환된다.

**원인**:

```python
# query.py:48-49
valid_answer_types = {"fulltext", "summary", "extract", "discover", "clarify"}
answer_type = handler_result.answer_type if handler_result.answer_type in valid_answer_types else "clarify"
# "not_found" ∉ valid_answer_types → "clarify"로 치환
```

```python
# extract_handler.py:43
return HandlerResult(answer=answer, answer_type="not_found", sources=[])
```

클라이언트 입장에서 `not_found`와 `clarify`는 다른 의미지만 동일하게 전달된다. Scenario A의 응답이 `answer_type="clarify"`로 나오는 이유다.

---

### Bug 4 (기존 결함 유지): `HandlerContext.understanding` 주석 처리

**관련 파일**: `src/convention_qa/action_routing/router.py:136`

**현상**: CompareHandler가 `context.understanding`에서 `document_queries`를 읽으나 항상 `None`

**원인**:

```python
# router.py:132-137
context = HandlerContext(
    question=question,
    intent=understanding.intent,
    resolution=resolution,
    # understanding=understanding,  ← 주석 처리됨
)
```

CompareHandler.handle()에서:
```python
understanding = context.understanding  # None
document_queries = getattr(understanding, "document_queries", None) if understanding else None  # None
if not document_queries or len(document_queries) < 2:
    answer = format_not_found(None)  # 항상 not_found로 fallback
```

compare intent 요청 시 항상 `not_found` 반환. 이번 두 시나리오와는 무관하나 같은 커밋에서 발생한 추가 결함.

---

## 수정 필요 사항 요약

| # | 파일 | 수정 내용 | 영향 시나리오 |
|---|------|-----------|--------------|
| 1 | `alias_normalizer.py` | `_matches_alias()`: ASCII alias 매칭 시 `\b` 대신 뒤따르는 문자가 `\w`인 경우도 경계로 인식하도록 보완 (예: `re.ASCII` 플래그 사용 또는 lookahead `(?=[^\w]|$)` 추가) | Scenario A |
| 2 | `models.py` | `DocumentResolutionResult.resolution_strategy` Literal에 `"keyword_tiebreak"` 추가 | Scenario B (500 Error) |
| 3 | `query.py` | `valid_answer_types`에 `"not_found"` 추가 또는 `answer_type` 변환 로직 제거 | 전반적 answer_type 오분류 |
| 4 | `router.py` | `HandlerContext` 생성 시 `understanding=understanding` 주석 해제 | compare 기능 전체 |

---

## 원인별 우선순위

| 우선순위 | 버그 | 심각도 | 이유 |
|---------|------|--------|------|
| P0 | Bug 2 (Literal 미등록) | 치명적 (500) | 정상 로직이 성공해도 무조건 500 반환 |
| P1 | Bug 1 (alias 단어경계) | 높음 | Fix 3의 전제 조건을 파괴함. `stack` 필터가 항상 오작동 |
| P2 | Bug 4 (understanding 주석) | 높음 | compare 기능 전체 불능 |
| P3 | Bug 3 (not_found Literal) | 낮음 | 기능은 동작하나 응답 타입 오분류 |

---

## 재현 방법

```bash
# 서버 기동
uvicorn src.api.main:app --reload

# Scenario A: 기대값 → extract, 실제값 → clarify(not_found)
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Java에서 트랜잭션 관리하는 법 알려줘"}'

# Scenario B: 기대값 → keyword_tiebreak resolved, 실제값 → 500
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "FSD 구조 규칙 알려줘"}'

# alias_normalizer 단독 검증 (Bug 1)
python3 -c "
from src.convention_qa.query_understanding.alias_normalizer import normalize_stack
print(repr(normalize_stack('Java에서 트랜잭션 관리하는 법 알려줘')))  # None (버그)
print(repr(normalize_stack('Java Spring 트랜잭션')))  # 'spring' (정상)
"
```

---

## alias_normalizer Bug 1 — 상세 재현

```python
import re

alias = "Java"
text = "Java에서 트랜잭션 관리하는 법 알려줘"

# 현재 코드
pattern_current = r"\b" + re.escape(alias) + r"\b"
print(bool(re.search(pattern_current, text)))  # False (버그)

# 원인: Python re의 \b는 유니코드 \w 사용, '에'도 \w로 분류됨
# 'a'(w)와 '에'(w) 사이에 경계 없음 → \bJava\b 미매칭

# re.ASCII 플래그 사용 시
pattern_ascii = r"\b" + re.escape(alias) + r"\b"
print(bool(re.search(pattern_ascii, text, re.ASCII)))  # True (수정 방향)
# re.ASCII 사용 시 \w = [a-zA-Z0-9_] 만 해당 → '에'는 \W → Java 뒤에 경계 발생
```
