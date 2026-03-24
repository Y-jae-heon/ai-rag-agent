# Code Review Report

**Date**: 2026-03-24
**Reviewed Files**:
- `tests/convention_qa/__init__.py` (신규)
- `tests/convention_qa/query_understanding/__init__.py` (신규)
- `tests/convention_qa/query_understanding/test_alias_normalizer.py` (신규)
**Reviewer**: AI Code Reviewer
**Severity Legend**: Critical | Major | Minor | Suggestion

---

## Executive Summary

P2-BUG-05 티켓이 요구한 10개 테스트 케이스를 정확히 구현하였으며, 클래스 분리와 docstring 작성 등 테스트 구조도 양호하다. 다만 핵심 회귀 방지 대상인 `re.ASCII` 플래그 자체를 직접 검증하는 케이스가 없고, `_matches_alias` 테스트에 누락된 경계 케이스가 몇 가지 존재하여 회귀 안전망으로서의 완결성이 부분적으로 미흡하다. 프라이빗 함수(`_matches_alias`)를 직접 임포트하는 패턴은 인터페이스 변경에 취약하다는 점도 추후 고려가 필요하다.

**Overall Score**: 7/10

---

## Findings

### Code Quality & Readability

#### 내부 구현 함수(_matches_alias)를 직접 임포트 `Minor`
**File**: `tests/convention_qa/query_understanding/test_alias_normalizer.py` | **Line(s)**: 10-14

**Problem**:
`_matches_alias`는 언더스코어 접두사가 붙은 내부 구현 함수다. 퍼블릭 API(`normalize_stack`, `normalize_domain`)를 통해 간접적으로 검증하는 것이 원칙이다. 내부 함수를 직접 임포트하면 나중에 함수명이나 시그니처가 변경될 때 테스트가 불필요하게 깨지고, "구현 세부 사항을 테스트한다"는 안티패턴이 된다.

**Current Code**:
```python
from src.convention_qa.query_understanding.alias_normalizer import (
    _matches_alias,
    normalize_domain,
    normalize_stack,
)
```

**Recommended Fix**:
P1-BUG-02 회귀라는 특수 맥락을 고려하면, 내부 함수를 직접 테스트하는 현재 방식에는 정당한 이유가 있다. 다만 이를 명시적으로 주석으로 남겨두면 향후 리뷰어 혼선을 방지할 수 있다.

```python
# _matches_alias는 re.ASCII 플래그 관련 P1-BUG-02 회귀를 직접 검증하기 위해
# 내부 함수임에도 임포트한다. 리팩터링 시 퍼블릭화 또는 별도 모듈 분리 고려.
from src.convention_qa.query_understanding.alias_normalizer import (
    _matches_alias,
    normalize_domain,
    normalize_stack,
)
```

**Rationale**: 의도가 명시되면 이후 유지보수자가 해당 패턴을 실수로 제거하거나 반대로 무비판적으로 확산시키는 것을 막을 수 있다.

---

### Correctness & Logic

#### re.ASCII 플래그 제거 시나리오를 직접 검증하지 않음 `Major`
**File**: `tests/convention_qa/query_understanding/test_alias_normalizer.py` | **Line(s)**: 20-22

**Problem**:
P2-BUG-05 티켓의 핵심 목적은 "향후 `re.ASCII` 플래그가 제거되어도 CI에서 감지한다"이다. 현재 구현된 `test_ascii_alias_followed_by_korean_matches`는 버그가 없는 경우(`True`)만 검증하므로, `re.ASCII` 플래그가 제거되어도 이 케이스는 여전히 통과할 수 있다. 플래그가 없으면 `"Java에서"` 입력에서 `\b`가 성립하지 않아 `False`를 반환하므로, 반대 방향 검증이 진짜 회귀 방지다.

실제 시나리오: 누군가 `re.ASCII`를 제거하면
- `_matches_alias("Java에서 트랜잭션", "Java")` → `False` (회귀 발생)
- 현재 테스트가 `assert ... is True`이므로 실패하여 감지됨 --- **이것은 맞다**

재확인하면, 현재 구현도 `re.ASCII` 제거 시 회귀를 감지할 수 있다. 이 항목은 이슈 없음으로 정정.

단, 다음 시나리오는 여전히 커버되지 않는다: `re.IGNORECASE` 등 다른 플래그가 추가되어 `"javascript"` (소문자) 입력에서 `"JavaScript"` alias가 의도치 않게 매칭되는 회귀는 현재 테스트로 감지 불가.

**Recommended Fix**:
대소문자 구분 유지 검증 케이스 추가.

```python
def test_ascii_alias_case_sensitive(self):
    """ASCII alias 매칭은 대소문자를 구분해야 한다 (IGNORECASE 플래그 회귀 방지)."""
    assert _matches_alias("javascript 프레임워크", "JavaScript") is False
```

**Rationale**: alias 목록에는 `"JavaScript"`, `"Java"`, `"React"` 등 대소문자가 명시적으로 구분된 항목들이 있다. 대소문자 구분이 깨지는 회귀도 주요 위험 중 하나다.

---

#### normalize_domain / normalize_stack에서 None 반환 케이스 미완 `Minor`
**File**: `tests/convention_qa/query_understanding/test_alias_normalizer.py` | **Line(s)**: 53-61

**Problem**:
`normalize_domain`에는 알 수 없는 도메인 입력에 대한 `None` 반환 테스트가 없다. `normalize_stack`은 `test_unknown_stack_returns_none`이 있어 대칭이 맞지 않는다. 특히 `normalize_domain`의 `None` 경로는 퍼블릭 API 계약의 일부이므로 누락된 커버리지다.

**Current Code**:
```python
class TestNormalizeDomain:
    def test_fe_alias_maps_to_frontend(self):
        assert normalize_domain("FE에서 처리") == "frontend"

    def test_be_alias_maps_to_backend(self):
        assert normalize_domain("BE에서 API") == "backend"
    # None 반환 케이스 없음
```

**Recommended Fix**:
```python
def test_unknown_domain_returns_none(self):
    assert normalize_domain("스프링으로 API 개발") is None
```

**Rationale**: API 계약(`Returns: "frontend", "backend", 또는 None`)의 세 가지 반환값 중 하나가 검증되지 않았다.

---

#### 괄호로 끝나는 alias 커버리지 없음 `Minor`
**File**: `tests/convention_qa/query_understanding/test_alias_normalizer.py`

**Problem**:
에이전트 메모리에 기록된 알려진 구조적 결함(`Java(Spring)`, `Kotlin(Spring)`, `Typescript(NestJS)` 등 `)` 로 끝나는 alias는 `\b` 매칭이 실패함)에 대한 테스트가 전혀 없다. 이 버그는 문서화되어 있지만 자동화 테스트로 고정(pin)되어 있지 않아, 향후 이 결함이 수정되었을 때 의도적인 수정인지 회귀인지 판별하기 어렵다.

**Recommended Fix**:
현재 동작을 명시적으로 고정하는 케이스를 추가하거나, 스킵 마커로 알려진 결함임을 표시한다.

```python
@pytest.mark.xfail(reason="P3-BUG-06: 괄호로 끝나는 alias는 \\b 매칭 실패 (알려진 결함)")
def test_paren_alias_java_spring_matches(self):
    """'Java(Spring)' alias는 현재 \\b 매칭 실패로 동작하지 않는다."""
    assert _matches_alias("Java(Spring) 설정", "Java(Spring)") is True
```

**Rationale**: `xfail` 마커는 알려진 결함이 수정되었을 때 `XPASS`로 자동 감지되어, 의도치 않은 수정도 보고된다. 결함 문서화와 테스트를 연결짓는 표준적인 방법이다.

---

### Testing

#### 테스트 실행 결과
사용자 보고 기준: pytest 10/10 전원 통과.

로컬 환경에서 pytest 실행을 시도하였으나 bash 실행 권한 제한으로 직접 검증하지 못했다. 사용자 제공 결과를 신뢰하여 통과 상태로 기록한다.

티켓 요건(10개 케이스)과 구현된 테스트 메서드의 1:1 대응을 정적 분석으로 검증:

| 티켓 케이스 | 구현된 테스트 메서드 | 통과 |
|---|---|---|
| `_matches_alias("Java에서 트랜잭션", "Java")` → True | `test_ascii_alias_followed_by_korean_matches` | v |
| `_matches_alias("JavaScript", "Java")` → False | `test_ascii_alias_partial_match_prevented_ascii_suffix` | v |
| `_matches_alias("JavaEE에서 트랜잭션", "Java")` → False | `test_ascii_alias_partial_match_prevented_mixed_suffix` | v |
| `_matches_alias("스프링으로 개발", "스프링")` → True | `test_non_ascii_alias_korean_matches` | v |
| `normalize_stack("Java에서 트랜잭션 관리하는 법")` → "spring" | `test_java_maps_to_spring` | v |
| `normalize_stack("Kotlin으로 테스트 작성")` → "kotlin" | `test_kotlin_maps_to_kotlin` | v |
| `normalize_stack("React 컴포넌트 구조")` → "react" | `test_react_maps_to_react` | v |
| `normalize_stack("파이썬으로 API 만들기")` → None | `test_unknown_stack_returns_none` | v |
| `normalize_domain("FE에서 처리")` → "frontend" | `test_fe_alias_maps_to_frontend` | v |
| `normalize_domain("BE에서 API")` → "backend" | `test_be_alias_maps_to_backend` | v |

티켓 요건 10개 전원 커버됨.

---

## Positive Highlights

- 티켓 요건 10개 케이스를 정확히 1:1로 구현했으며 누락이 없다.
- `TestMatchesAlias`, `TestNormalizeStack`, `TestNormalizeDomain` 세 클래스로 책임별 분리가 명확하다.
- 각 테스트 메서드에 한국어 docstring을 작성하여 테스트 의도가 명확하다. 특히 `test_ascii_alias_followed_by_korean_matches`의 "핵심 버그 회귀"라는 표현은 이 테스트의 존재 이유를 정확히 전달한다.
- `__init__.py` 파일들도 함께 생성하여 패키지 구조를 올바르게 설정했다.
- `from __future__ import annotations` 사용으로 타입 힌트 호환성을 유지한다.

---

## Action Items Summary

| Priority | Issue | File | Line |
|----------|-------|------|------|
| Major | 대소문자 구분 유지 검증 케이스 미존재 (IGNORECASE 회귀 무방비) | `test_alias_normalizer.py` | 17-35 |
| Minor | `normalize_domain`의 None 반환 케이스 미검증 | `test_alias_normalizer.py` | 53-61 |
| Minor | 괄호 alias 알려진 결함이 테스트로 고정되지 않음 | `test_alias_normalizer.py` | 신규 추가 필요 |
| Minor | `_matches_alias` 직접 임포트 의도 미문서화 | `test_alias_normalizer.py` | 10-14 |

---

## Recommendations for Future Work

- **nestjs 스택 테스트 추가**: `_STACK_ALIASES`에 정의된 스택 중 `nestjs`는 테스트에서 전혀 등장하지 않는다. 향후 테스트 커버리지를 높일 때 추가를 권장한다.
- **대소문자 변형 alias 테스트**: `_FRONTEND_ALIASES`에는 `"FE"`와 `"fe"`가 별도 항목으로 존재한다. 현재 `"FE에서 처리"`만 테스트하므로 `"fe"`, `"프론트"`, `"front-end"` 등 다양한 alias 변형에 대한 케이스도 추가하면 alias 목록 확장 시 회귀를 더 빨리 감지할 수 있다.
- **파라미터화된 테스트 고려**: `normalize_stack` 테스트 케이스가 늘어날 경우 `@pytest.mark.parametrize`를 사용하면 반복 코드를 줄이고 케이스 추가가 용이해진다.
- **conftest.py 도입 여부 검토**: 테스트 파일이 늘어나면 공통 fixture나 pytest 설정을 `tests/conftest.py`에 집중시키는 것을 고려한다.
