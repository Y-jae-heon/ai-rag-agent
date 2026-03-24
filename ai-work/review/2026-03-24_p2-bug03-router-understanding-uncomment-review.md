# Code Review Report

**Date**: 2026-03-24
**Reviewed Files**:
- `src/convention_qa/action_routing/router.py` (L112–138)
- `src/convention_qa/action_routing/base_handler.py` (L16–35)
- `src/convention_qa/action_routing/compare_handler.py` (L28–43)
- `src/convention_qa/action_routing/discover_handler.py` (참고)
- `src/convention_qa/action_routing/extract_handler.py` (참고)
- `src/convention_qa/action_routing/summarize_handler.py` (참고)

**Reviewer**: AI Code Reviewer
**Severity Legend**: 🔴 Critical | 🟠 Major | 🟡 Minor | 🟢 Suggestion

---

## Executive Summary

`router.py`에서 주석 처리되어 있던 `understanding=understanding` 필드를 주석 해제한 단순하고 국소적인 수정이다. 수정 자체의 정확성은 문제가 없으며, `HandlerContext.understanding`이 `Optional(default=None)`으로 정의되어 있으므로 기존 핸들러(discover/extract/summarize)에 대한 호환성도 유지된다. 다만 몇 가지 코드 품질상의 개선 지점(디버그 `print` 문, 느슨한 `Any` 타입, 중복 로직)이 남아 있으며 이들은 이번 수정이 도입한 것은 아니나 동일 파일에 존재한다.

**Overall Score**: 9/10

---

## Findings

### Correctness & Logic

#### understanding 필드 주석 해제 — 수정 정확성 확인 `🟢 Suggestion`
**File**: `src/convention_qa/action_routing/router.py` | **Line(s)**: 132–137

**Problem**:
`HandlerContext` 생성 시 `understanding=understanding`이 주석 처리되어 있었기 때문에 `CompareHandler`가 `context.understanding`을 항상 `None`으로 받았고, `document_queries` 분기가 `not_found` fallback으로 강제 진입했다.

**현재 수정 코드** (정상):
```python
context = HandlerContext(
    question=question,
    intent=understanding.intent,
    resolution=resolution,
    understanding=understanding,
)
```

**Rationale**: 주석 해제만으로 증상이 완전히 해소된다. `CompareHandler.handle()`의 방어 코드(`if understanding else None`)도 그대로 유지되므로 향후 `understanding=None`이 전달되는 예외적 경로에서도 안전하다.

---

#### CompareHandler — understanding이 None인 경로의 방어 코드 검토 `🟢 Suggestion`
**File**: `src/convention_qa/action_routing/compare_handler.py` | **Line(s)**: 31–32

**Problem**:
`route_and_execute`가 항상 `understanding`을 전달하기 때문에 현실적으로 `None`이 들어오는 경우는 없다. 그러나 `HandlerContext.understanding`이 `Optional` 타입으로 선언되어 있어 이론적으로는 가능하다. 현재 방어 코드는 적절하다.

```python
understanding = context.understanding
document_queries = getattr(understanding, "document_queries", None) if understanding else None
```

**Rationale**: 방어 코드가 존재하는 것 자체는 긍정적이다. 다만 `HandlerContext.understanding`을 `Optional`이 아닌 `QueryUnderstandingResult` 타입으로 구체화하면 타입 안전성이 높아지고 불필요한 방어 코드도 제거할 수 있다(아래 Major 항목 참조).

---

### Code Quality & Readability

#### HandlerContext.understanding 타입이 Any로 정의됨 `🟠 Major`
**File**: `src/convention_qa/action_routing/base_handler.py` | **Line(s)**: 30–33

**Problem**:
`understanding` 필드가 `Any` 타입으로 선언되어 있어 IDE 자동완성이 동작하지 않고, `document_queries`, `domain`, `stack` 등의 속성 접근이 타입 체커에 의해 검증되지 않는다.

```python
understanding: Any = Field(
    default=None,
    description="QueryUnderstandingResult 인스턴스. compare handler에서 document_queries 접근에 사용.",
)
```

**Recommended Fix**:
```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.convention_qa.query_understanding.models import QueryUnderstandingResult

understanding: "QueryUnderstandingResult | None" = Field(
    default=None,
    description="QueryUnderstandingResult 인스턴스. compare handler에서 document_queries 접근에 사용.",
)
```

**Rationale**: `TYPE_CHECKING` 블록을 사용하면 순환 임포트를 피하면서도 정적 분석이 가능해진다. `arbitrary_types_allowed = True`가 이미 설정되어 있으므로 Pydantic 런타임 제약도 없다.

---

#### CompareHandler — 디버그 print 문이 프로덕션 코드에 잔존 `🟠 Major`
**File**: `src/convention_qa/action_routing/compare_handler.py` | **Line(s)**: 43–44, 112, 124

**Problem**:
`print()` 호출이 3곳에 존재한다. 이는 이번 수정이 도입한 것은 아니지만, 리뷰 범위 파일이므로 함께 지적한다.

```python
print(f"resolution_a = {resolution_a}")
print(f"resolution_b = {resolution_b}")
# ...
print(f"[ChromaDB] vectorstore.get() 호출 — ...")
print(f"[ChromaDB] vectorstore.get() 완료 — 섹션 수={len(sections)}")
```

**Recommended Fix**:
```python
logger.debug("resolution_a = %s", resolution_a)
logger.debug("resolution_b = %s", resolution_b)
# ...
logger.debug("[ChromaDB] vectorstore.get() 호출 — collection=section_index, canonical_doc_id=%s", canonical_doc_id)
logger.debug("[ChromaDB] vectorstore.get() 완료 — 섹션 수=%d", len(sections))
```

**Rationale**: `logger.debug`는 로그 레벨 설정으로 제어 가능하고, 운영 환경에서 `stdout`에 직접 출력하지 않는다. 동일 패턴이 `DiscoverHandler`, `SummarizeHandler`, `ExtractHandler`에도 존재하므로 일괄 정리를 권장한다.

---

### Maintainability & Architecture

#### _get_sections 로직이 CompareHandler와 SummarizeHandler에 중복 `🟡 Minor`
**File**: `src/convention_qa/action_routing/compare_handler.py` (L92–135), `src/convention_qa/action_routing/summarize_handler.py` (L68–111)

**Problem**:
`_get_sections`의 구현이 두 핸들러에서 거의 동일하다. Chroma 벡터스토어를 초기화하고, `get(where={"canonical_doc_id": ...})`를 호출하고, `documents`와 `metadatas`를 파싱하는 로직이 복사된 상태이다.

**Recommended Fix**:
공통 유틸리티 함수(`src/convention_qa/action_routing/section_utils.py` 또는 `BaseHandler`의 protected 메서드)로 추출하여 단일 구현을 공유한다.

**Rationale**: 현재는 ChromaDB 컬렉션명이나 파싱 로직을 변경할 때 두 곳을 모두 수정해야 한다. DRY 원칙 위반이며 유지보수 부담이 증가한다.

---

### Security

이번 변경에서 보안 관련 신규 위험은 없다. `understanding` 객체는 이미 intent classifier를 통과한 내부 도메인 모델이며 외부 입력이 직접 노출되지 않는다.

---

## Testing

테스트 실행 결과 (`tests/test_compare_handler.py`):

```
============================= test session starts ==============================
platform darwin -- Python 3.12.2, pytest-7.4.4
collected 16 items

TestHandleNotFound::test_handle_no_document_queries_returns_not_found    PASSED
TestHandleNotFound::test_handle_single_document_query_returns_not_found  PASSED
TestHandleNotFound::test_handle_empty_document_queries_returns_not_found PASSED
TestHandleNormalCase::test_handle_two_documents_returns_compare_type     PASSED
TestHandleNormalCase::test_handle_sources_contain_both_documents         PASSED
TestHandleNormalCase::test_handle_compare_called_with_correct_args       PASSED
TestHandleNormalCase::test_handle_answer_contains_titles                 PASSED
TestHandleResolutionFailure::test_handle_second_resolution_none_still_returns_compare   PASSED
TestHandleResolutionFailure::test_handle_second_resolution_none_uses_query_as_title     PASSED
TestHandleResolutionFailure::test_handle_second_resolution_none_get_sections_called_with_empty_string PASSED
TestHandleResolutionFailure::test_handle_compare_called_with_empty_sections_when_resolution_fails     PASSED
TestFormatSections::test_format_sections_empty_returns_placeholder       PASSED
TestFormatSections::test_format_sections_with_heading_and_content        PASSED
TestFormatSections::test_format_sections_multiple_sections_joined_by_double_newline    PASSED
TestFormatSections::test_format_sections_empty_content_only_heading      PASSED
TestFormatSections::test_get_sections_empty_canonical_doc_id_returns_empty_list        PASSED

============================== 16 passed in 0.03s ==============================
```

16개 전체 통과. 회귀 없음.

---

## Positive Highlights

- **방어 코드 설계 양호**: `CompareHandler.handle()`에서 `context.understanding`이 `None`인 경우를 `if understanding else None` 패턴으로 처리한다. 이로 인해 `HandlerContext`를 `understanding=None`으로 생성하는 다른 경로가 있더라도 핸들러가 안전하게 `not_found`를 반환한다.
- **타입 호환성 유지**: `HandlerContext.understanding`이 `default=None`으로 선언되어 있으므로 `understanding` 필드를 사용하지 않는 `DiscoverHandler`, `ExtractHandler`, `SummarizeHandler`는 이번 수정의 영향을 전혀 받지 않는다.
- **테스트 커버리지 적절**: `TestHandleNotFound`, `TestHandleNormalCase`, `TestHandleResolutionFailure`, `TestFormatSections`로 분류된 16개 테스트가 주요 경로를 모두 커버한다.
- **수정 범위 최소화**: 단 한 줄(주석 해제)로 버그를 수정하고 사이드 이펙트가 없다. 분리된 레이어 설계 덕분에 가능한 결과이다.

---

## Action Items Summary

| Priority | Issue | File | Line |
|----------|-------|------|------|
| 🟠 Major | HandlerContext.understanding 타입을 Any 대신 구체 타입으로 선언 | `base_handler.py` | 30–33 |
| 🟠 Major | 디버그 print 문을 logger.debug로 교체 | `compare_handler.py` | 43–44, 112, 124 |
| 🟡 Minor | _get_sections 중복 구현 공통 유틸리티로 추출 | `compare_handler.py`, `summarize_handler.py` | — |

---

## Recommendations for Future Work

- `HandlerContext.resolution` 필드도 현재 `Any` 타입이다. `DocumentResolutionResult` 타입으로 구체화하면 핸들러 전체의 타입 안전성이 크게 향상된다.
- `DiscoverHandler`, `SummarizeHandler`, `ExtractHandler`의 `print()` 문도 동일한 패턴으로 `logger.debug`로 일괄 교체하는 별도 정리 작업을 권장한다.
- `_get_sections` 중복 제거 시 `_resolve` 메서드도 공통화 대상이 될 수 있다 (`CompareHandler._resolve`는 `CompareHandler`에만 존재하지만, 향후 다른 핸들러가 동일 패턴을 사용한다면 `BaseHandler`로 올리는 것이 적합하다).
