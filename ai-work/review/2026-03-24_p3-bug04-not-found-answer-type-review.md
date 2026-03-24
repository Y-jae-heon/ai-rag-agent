# Code Review Report

**Date**: 2026-03-24
**Reviewed Files**:
- `src/api/routes/query.py` (line 48)
- `src/api/models.py` (line 50)
**Reviewer**: AI Code Reviewer
**Severity Legend**: 🔴 Critical | 🟠 Major | 🟡 Minor | 🟢 Suggestion

---

## Executive Summary

P3-BUG-04의 수정은 올바르다. `valid_answer_types` 집합과 `QueryResponse.answer_type` Literal에 `"not_found"`를 동시에 추가하여 두 선언이 일치하며, 기존에 `ExtractHandler`·`CompareHandler`가 반환하던 `"not_found"`가 `"clarify"`로 silently 변환되던 버그를 정확히 차단한다. 회귀 테스트 56개 전원 통과. 다만 아래 두 가지 잠재적 위험 지점이 남아 있다.

**Overall Score**: 7/10

---

## Findings

### Correctness & Logic

#### `"compare"` answer_type이 valid_answer_types에 누락 🟠
**File**: `src/api/routes/query.py` | **Line(s)**: 48–49

**Problem**:
`CompareHandler.handle()`은 정상 경로에서 `answer_type="compare"`를 반환하지만 (`compare_handler.py:72`), `valid_answer_types` 집합에 `"compare"`가 없다. 이 버그는 이번 PR 이전부터 존재하므로 이번 수정의 결과물은 아니지만, 이번 수정에서 집합을 직접 편집하면서 발견하고 함께 해결해야 할 지점이다. 현재 `CompareHandler`의 정상 응답도 `"clarify"`로 silently 변환된다.

**Current Code**:
```python
# src/api/routes/query.py:48
valid_answer_types = {"fulltext", "summary", "extract", "discover", "clarify", "not_found"}
```

**Recommended Fix**:
```python
valid_answer_types = {"fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"}
```

그리고 `src/api/models.py:50`의 Literal도 동기화:
```python
answer_type: Literal["fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"]
```

**Rationale**: handler가 실제로 반환하는 모든 `answer_type` 값이 허용 목록에 있어야 silent 변환이 발생하지 않는다. `"not_found"` 추가와 동일한 논리가 `"compare"`에도 그대로 적용된다.

---

### Maintainability & Architecture

#### `valid_answer_types`와 `QueryResponse.answer_type` Literal의 이중 관리 구조 🟡
**File**: `src/api/routes/query.py` | **Line(s)**: 48 / `src/api/models.py` | **Line(s)**: 50

**Problem**:
허용 answer_type 목록이 `query.py`의 `set`과 `models.py`의 `Literal` 두 곳에 중복 정의되어 있다. 이번 PR처럼 새 값을 추가할 때 한쪽만 수정하면 런타임 오류 또는 타입 검증 불일치가 발생한다. 실제로 이번 수정은 두 파일을 모두 올바르게 수정했으나, 다음 수정에서 다시 발생할 수 있는 구조적 취약점이다.

**Recommended Fix**:
`Literal` 자체에서 허용 집합을 파생시켜 단일 진실 공급원(single source of truth)을 만든다:

```python
# src/api/models.py
from typing import Literal, get_args

ANSWER_TYPE_LITERAL = Literal["fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"]

class QueryResponse(BaseModel):
    answer_type: ANSWER_TYPE_LITERAL
    ...
```

```python
# src/api/routes/query.py
from src.api.models import ANSWER_TYPE_LITERAL
from typing import get_args

valid_answer_types = set(get_args(ANSWER_TYPE_LITERAL))
answer_type = handler_result.answer_type if handler_result.answer_type in valid_answer_types else "clarify"
```

**Rationale**: 두 선언을 동기화하는 책임이 사람에게 있는 구조를 없애고, `models.py`의 Literal만 수정하면 `query.py`의 검증 집합이 자동으로 반영된다.

---

#### `HandlerResult.answer_type` 필드가 `str`로 선언되어 타입 안전망 없음 🟢
**File**: `src/convention_qa/action_routing/base_handler.py` | **Line(s)**: 49

**Problem**:
`HandlerResult.answer_type`은 `str`로 선언되어 있어, handler가 임의의 문자열을 반환해도 Pydantic이 잡아주지 않는다. 허용 목록 검증이 전적으로 `query.py`의 런타임 집합 비교에만 의존한다.

**Current Code**:
```python
answer_type: str = Field(description="응답 유형 식별자.")
```

**Recommended Fix**:
```python
from typing import Literal
AnswerType = Literal["fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"]

answer_type: AnswerType = Field(description="응답 유형 식별자.")
```

`ANSWER_TYPE_LITERAL`을 공유 상수로 뽑으면 `models.py`, `base_handler.py`, `query.py` 세 곳이 모두 단일 선언을 참조할 수 있다.

**Rationale**: handler 레이어에서 잘못된 값이 생성되면 Pydantic 모델 생성 시점에 즉시 `ValidationError`로 잡아, `query.py`까지 전파되기 전에 차단할 수 있다.

---

### Code Quality

#### `_build_response()`의 `# type: ignore[arg-type]` 주석 🟢
**File**: `src/api/routes/query.py` | **Line(s)**: 53

**Problem**:
`answer_type` 인자에 `# type: ignore[arg-type]`가 붙어 있다. 이는 `HandlerResult.answer_type`이 `str`인 반면 `QueryResponse.answer_type`이 `Literal`이어서 발생하는 타입 불일치를 억제하는 임시 처치다. 위의 `HandlerResult.answer_type` 타입 구체화 제안을 적용하면 이 주석도 제거할 수 있다.

**Rationale**: `type: ignore` 억제 주석은 타입 불일치를 숨겨 잠재적 오류를 정적 분석에서 놓치게 만든다. 근본 타입을 맞추는 것이 올바른 해결책이다.

---

### Testing

#### 테스트 실행 결과

```
pytest tests/ -v --tb=short
56 passed in 0.40s
```

56개 전원 통과. 회귀 없음.

#### `_build_response()` 직접 단위 테스트 부재 🟡
**File**: `src/api/routes/query.py` | **Line(s)**: 25–57

**Problem**:
이번 버그(`"not_found"` → `"clarify"` silently 변환)의 발생 지점은 `_build_response()` 함수였으나, 이 함수에 대한 직접 단위 테스트가 없다. handler 계층의 테스트는 충분하지만, `valid_answer_types`를 통과한 값이 `QueryResponse`로 올바르게 매핑되는지를 검증하는 테스트가 없어 동일 유형의 회귀가 무음으로 재발할 수 있다.

**Recommended Fix**:
```python
# tests/test_query_route.py (신규)
from src.api.routes.query import _build_response
from src.convention_qa.action_routing.base_handler import HandlerResult

def test_build_response_not_found_is_not_coerced_to_clarify():
    result = HandlerResult(answer="없음", answer_type="not_found", sources=[])
    response = _build_response(result, intent="extract")
    assert response.answer_type == "not_found"

def test_build_response_unknown_type_falls_back_to_clarify():
    result = HandlerResult(answer="?", answer_type="unknown_type", sources=[])
    response = _build_response(result, intent="extract")
    assert response.answer_type == "clarify"
```

**Rationale**: 이번 버그의 발생 위치를 직접 커버하는 테스트가 있었다면 수정 전에 실패로 드러났을 것이다.

---

## Positive Highlights

- `valid_answer_types` (set)과 `QueryResponse.answer_type` (Literal) 두 선언을 모두 빠짐없이 업데이트한 점. 한쪽만 수정했을 때 발생하는 반쪽 수정 오류를 피했다.
- P3 우선순위 티켓임에도 `"not_found"`와 `"clarify"`의 의미 차이를 정확히 구분하여 클라이언트 오해 가능성을 명시한 티켓 문서 품질이 높다.
- 기존 56개 테스트가 모두 통과하여 이번 수정이 어떠한 회귀도 유발하지 않음이 확인되었다.

---

## Action Items Summary

| Priority | Issue | File | Line |
|----------|-------|------|------|
| 🟠 Major | `"compare"` answer_type이 valid_answer_types 및 Literal에 누락 | `query.py`, `models.py` | 48, 50 |
| 🟡 Minor | valid_answer_types와 Literal 이중 관리 구조 — 동기화 누락 위험 | `query.py`, `models.py` | 48, 50 |
| 🟡 Minor | `_build_response()` 직접 단위 테스트 부재 | `tests/test_query_route.py` | (신규) |
| 🟢 Suggestion | `HandlerResult.answer_type`을 `str` → `Literal`로 구체화 | `base_handler.py` | 49 |
| 🟢 Suggestion | `# type: ignore[arg-type]` 주석 제거 (타입 구체화 후) | `query.py` | 53 |

---

## Recommendations for Future Work

- `ANSWER_TYPE_LITERAL`을 공유 상수(`src/api/models.py` 또는 별도 `src/convention_qa/types.py`)로 추출하여, `models.py` · `base_handler.py` · `query.py` 세 곳이 단일 선언을 참조하도록 리팩토링한다. 이렇게 하면 새 handler가 신규 answer_type을 추가할 때 한 곳만 수정하면 된다.
- `_build_response()` 함수 수준의 단위 테스트 파일(`tests/test_query_route.py`)을 추가하여, 라우터 레이어의 answer_type 변환 로직을 독립적으로 검증하는 테스트 커버리지를 확보한다.
