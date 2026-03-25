# Code Review Report

**Date**: 2026-03-24
**Reviewed Files**:
- `src/convention_qa/action_routing/summarize_handler.py`
- `tests/test_summarize_handler.py`
**Reviewer**: AI Code Reviewer
**Severity Legend**: 🔴 Critical | 🟠 Major | 🟡 Minor | 🟢 Suggestion

---

## Executive Summary

P3-BUG-08의 핵심 수정(Option A: `"summarize"` → `"summary"`)은 올바르게 적용되었으며, `valid_answer_types`, `models.py` Literal, 핸들러 반환값이 모두 `"summary"`로 일치한다. 테스트 6건 모두 통과하고 기댓값 수정도 누락 없이 완료되었다. 다만 수정 범위 밖의 기존 코드에서 디버그 `print` 구문 2건이 잔존하고 있어 별도 정리가 필요하다. 수정 자체의 정확성은 높으나, 타입 안전성 측면에서 `HandlerResult.answer_type` 필드가 `str`로 선언되어 컴파일 타임 검증이 불가능한 구조적 한계가 남아 있다.

**Overall Score**: 8/10

---

## Findings

### 정확성 & 일관성

#### answer_type 삼중 일치 확인 완료 `🟢`

**File**: `src/api/routes/query.py` | **Line(s)**: 48
**File**: `src/api/models.py` | **Line(s)**: 50
**File**: `src/convention_qa/action_routing/summarize_handler.py` | **Line(s)**: 59

**Problem**: 없음. 세 곳의 허용 값이 모두 `"summary"`로 일치하여 BUG-08이 의도한 수정이 완전히 반영되어 있다.

- `valid_answer_types` (query.py:48): `{"fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"}`
- `QueryResponse.answer_type` Literal (models.py:50): `"summary"` 포함
- `SummarizeHandler.handle()` 반환 (summarize_handler.py:59): `answer_type="summary"`

**Rationale**: 이 세 곳의 값이 일치해야만 요약 응답이 `"clarify"`로 silent 변환되지 않는다. 수정이 정확하다.

---

### 코드 품질

#### 디버그 print 구문 잔존 `🟠`
**File**: `src/convention_qa/action_routing/summarize_handler.py` | **Line(s)**: 88, 100

**Problem**:
`_get_sections()` 내부에 `print()` 구문이 2건 남아 있다. 이는 이번 수정 대상은 아니지만, BUG-04(query.py의 print) 및 action_routing 레이어 전반의 디버그 print 잔존 패턴과 동일한 문제다. 프로덕션 로그 오염과 stdout 혼입이 발생한다.

**Current Code**:
```python
# summarize_handler.py:88
print(f"[ChromaDB] vectorstore.get() 호출 — collection=section_index, canonical_doc_id={canonical_doc_id}")

# summarize_handler.py:100
print(f"[ChromaDB] vectorstore.get() 완료 — 섹션 수={len(sections)}")
```

**Recommended Fix**:
```python
# 두 print 구문을 logger.debug()로 교체
logger.debug(
    "[SummarizeHandler._get_sections] vectorstore.get() 호출 — collection=section_index, canonical_doc_id=%s",
    canonical_doc_id,
)
# ...
logger.debug(
    "[SummarizeHandler._get_sections] vectorstore.get() 완료 — 섹션 수=%d",
    len(sections),
)
```

**Rationale**: 해당 정보는 이미 하단의 `logger.info()`로 섹션 수가 기록되므로 print 구문은 중복이자 잡음이다. `logger.debug()`로 교체하면 로그 레벨 제어가 가능해진다. 이 패턴은 프로젝트 전반의 기존 이슈이므로 별도 티켓으로 일괄 정리를 권고한다.

---

### 타입 안전성

#### HandlerResult.answer_type이 str로 선언되어 컴파일 타임 검증 불가 `🟡`
**File**: `src/convention_qa/action_routing/base_handler.py` | **Line(s)**: 49

**Problem**:
`HandlerResult.answer_type`이 `str`로 선언되어 있어, 핸들러가 허용되지 않은 값을 반환해도 타입 체커나 Pydantic이 이를 잡지 못한다. BUG-04와 BUG-08 모두 이 구조적 약점에서 비롯된 패턴이다. 런타임에서만 `valid_answer_types` 집합 비교를 통해 방어한다.

**Current Code**:
```python
# base_handler.py:49
answer_type: str = Field(description="응답 유형 식별자.")
```

**Recommended Fix**:
```python
from typing import Literal

AnswerType = Literal["fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"]

answer_type: AnswerType = Field(description="응답 유형 식별자.")
```

**Rationale**: `AnswerType` Literal을 `base_handler.py`에 한 곳에서 정의하고 `models.py`의 `QueryResponse`와 `query.py`의 `valid_answer_types`가 이를 참조하도록 만들면 단일 진실 공급원(SSOT)이 확보된다. 앞으로 새로운 `answer_type`이 추가될 때 세 파일을 동시에 수정해야 하는 현재 구조의 위험을 제거할 수 있다. 이 개선은 P3-BUG-10(answer_type 이중 진실 공급원) 티켓과 직접 연관된다.

---

### 테스트

#### 테스트 6/6 통과 확인

```
tests/test_summarize_handler.py::TestHandleWithSections::test_handle_with_sections PASSED
tests/test_summarize_handler.py::TestHandleWithSections::test_handle_sections_text_includes_heading_and_content PASSED
tests/test_summarize_handler.py::TestHandleEmptySections::test_handle_empty_sections PASSED
tests/test_summarize_handler.py::TestHandleEmptySections::test_handle_empty_sections_still_returns_summarize_type PASSED
tests/test_summarize_handler.py::TestHandleNoCanonicalDocId::test_handle_no_canonical_doc_id PASSED
tests/test_summarize_handler.py::TestHandleNoCanonicalDocId::test_handle_empty_canonical_doc_id_string PASSED

6 passed in 0.01s
```

기댓값 수정(4곳 → `"summary"`)이 누락 없이 완료되었고, 빈 섹션/canonical_doc_id None/빈 문자열 등 edge case도 모두 커버되어 있다.

#### _build_response() 통합 테스트 부재 `🟢`
**File**: `src/api/routes/query.py` | **Line(s)**: 25-57

**Problem**: 이번 수정의 실질적 위험 지점인 `_build_response()`의 fallback 로직(`valid_answer_types` 집합 비교)에 대한 단위 테스트가 존재하지 않는다. 핸들러 단위 테스트는 완비되어 있으나, `_build_response`가 `"summary"`를 올바르게 통과시키고 알 수 없는 값을 `"clarify"`로 fallback하는지 검증하는 테스트가 없다. 이는 P3-BUG-09 티켓과 직접 연관된다.

**Rationale**: 이번 수정 범위를 넘어서므로 별도 티켓(`P3-BUG-09`)에서 처리하는 것이 적절하다. 다만 리뷰 시점에서 인지하고 있어야 한다.

---

## Positive Highlights

- BUG-08의 핵심 수정(handler 반환값 `"summary"` 통일)이 정확하고 누락 없이 적용되었다.
- 테스트 기댓값 수정 4곳이 모두 올바르게 변경되었으며 테스트 6건 전부 통과한다.
- 다른 핸들러(`fulltext`, `extract`, `clarify`, `discover`, `compare`)의 `answer_type` 반환값은 모두 `valid_answer_types`에 포함된 값을 반환하고 있어 동일 패턴의 잔존 버그가 없음을 확인했다.
- BUG-08 자체의 수정 범위(Option A 선택 후 두 파일만 수정)가 명확하게 유지되어 무관한 변경이 혼입되지 않았다.

---

## Action Items Summary

| Priority | Issue | File | Line |
|----------|-------|------|------|
| 🟠 Major | 디버그 print 구문 2건 잔존 | `summarize_handler.py` | 88, 100 |
| 🟡 Minor | HandlerResult.answer_type str 선언 — Literal로 교체 필요 | `base_handler.py` | 49 |
| 🟢 Suggestion | _build_response() 단위 테스트 부재 (P3-BUG-09 연계) | `query.py` | 25-57 |

---

## Recommendations for Future Work

- **P3-BUG-09 우선 처리**: `_build_response()`에 대한 단위 테스트를 추가하여 `valid_answer_types` fallback 로직을 회귀 테스트로 보호해야 한다.
- **P3-BUG-10 처리**: `AnswerType` Literal을 `base_handler.py`에 단일 정의하고 `models.py`와 `query.py`가 이를 참조하도록 리팩토링하면 BUG-04/08과 같은 패턴의 버그가 구조적으로 불가능해진다.
- **디버그 print 일괄 정리**: `action_routing` 레이어 및 `query.py`에 잔존하는 모든 `print()` 구문을 `logger.debug()`로 일괄 교체하는 별도 정리 작업을 권고한다.
