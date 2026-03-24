# Code Review Report

**Date**: 2026-03-24
**Reviewed Files**: `src/convention_qa/query_understanding/alias_normalizer.py`
**Reviewer**: AI Code Reviewer
**Severity Legend**: Critical | Major | Minor | Suggestion

---

## Executive Summary

P1-BUG-02 수정(`re.ASCII` 플래그 추가)은 원래 보고된 버그("Java에서" 매칭 실패)를 정확히 해결한다. 수정 자체는 올바르며 ASCII-only 입력에 대한 회귀도 없다. 그러나 분석 과정에서 `re.ASCII` 적용 이전부터 잠재해 있던 별도의 구조적 문제가 두 가지 발견되었다. `Java(Spring)` 등 `)`로 끝나는 alias는 `\b` 기반 매칭이 전혀 작동하지 않으며, 이는 이번 수정과 무관하게 해당 alias들이 ASCII 분기에서 항상 매칭 실패 상태임을 의미한다. 추가로 alias 리스트의 정의 순서에 따른 불필요한 중복 항목도 존재한다.

**Overall Score**: 7/10

---

## Findings

### Correctness

#### 핵심 버그 수정 — 올바름 확인

**File**: `src/convention_qa/query_understanding/alias_normalizer.py` | **Line(s)**: 136

**검증 결과**:

Python `re` 모듈은 기본적으로 유니코드 모드로 동작하므로 한국어 글자(예: `에`, `으`, `로`)도 `\w`로 분류된다. 이로 인해 `"Java에서"` 문자열에서 `a`(`\w`)와 `에`(`\w`) 사이에 단어 경계(`\b`)가 생기지 않아 매칭이 실패했다. `re.ASCII` 플래그를 적용하면 `\w`가 `[a-zA-Z0-9_]`로 제한되어 `에`가 `\W`로 분류되고, `a`와 `에` 사이에 `\b`가 성립한다.

실증 테스트 결과:

| 입력 | 수정 전 | 수정 후 | 기대값 |
|------|---------|---------|--------|
| `"Java에서 트랜잭션"` | False | True | True |
| `"Java Spring 트랜잭션"` | True | True | True |
| `"JavaScript 써도 돼?"` | False | False | False |
| `"Kotlin으로 테스트"` | False | True | True |
| `"BE에서 처리"` | False | True | True |
| `"front-end에서 사용"` | False | True | True |

수정은 정확하며 ASCII-only 케이스에 대한 회귀 없음이 확인된다.

---

#### `)`로 끝나는 alias의 `\b` 매칭 영구 실패 `Major`

**File**: `src/convention_qa/query_understanding/alias_normalizer.py` | **Line(s)**: 39-73

**Problem**:

`_STACK_ALIASES`에는 `Java(Spring)`, `java(spring)`, `Kotlin(Spring)`, `kotlin(spring)`, `Typescript(NestJS)`, `typescript(nestjs)` 총 6개의 alias가 `)` 문자로 끝난다. `\b` 단어 경계는 `\w`와 `\W` 사이의 전환 지점에 성립하는데, `)` 는 항상 `\W`이다. 따라서 `\bJava\(Spring\)\b`에서 마지막 `\b`는 `)` 이후 위치를 검사하는데, 다음에 오는 문자가 공백이든 한국어 조사든 모두 `\W`이므로 `\b`가 성립하지 않는다.

이 문제는 `re.ASCII` 적용 이전에도 동일하게 존재했다. 단, 수정 전에는 `"Java(Spring)으로"` 같이 한국어 조사가 뒤따르는 경우 `으`가 `\w`(유니코드)로 분류되어 우연히 매칭이 되는 경우가 있었다. `re.ASCII` 적용 후에는 이 우연한 매칭마저 사라져 해당 alias 6개는 어떤 입력에서도 매칭되지 않는 상태가 되었다.

실증 결과:

```
'Java(Spring)'          수정 전: False  수정 후: False
'Java(Spring) 사용'      수정 전: False  수정 후: False
'Java(Spring)을'        수정 전: True   수정 후: False   ← 수정으로 동작 역전
'Java(Spring)으로'       수정 전: True   수정 후: False   ← 수정으로 동작 역전
```

수정 후 `"Java(Spring)으로 개발"` 같은 입력은 매칭되지 않는다. 그러나 실용적 영향은 제한적인데, `"Java"` alias가 `_STACK_ALIASES["spring"]` 리스트에서 `"Java(Spring)"` 보다 먼저 정의되어 있어 실제 탐색 시 `"Java"` alias가 먼저 매칭된다. 따라서 `"Java(Spring)으로 개발"` 입력은 `"Java"` alias로 여전히 `"spring"`을 반환한다.

그럼에도 이 alias들은 정의된 의도대로 동작하지 않으므로 설계 결함이다.

**Recommended Fix**:

옵션 A (권장): `)` 로 끝나는 alias를 리스트에서 제거한다. `"Java"`, `"Spring"` 등 단독 alias들이 이미 모든 케이스를 커버하고 있다.

```python
_STACK_ALIASES: dict[str, list[str]] = {
    "spring": [
        "스프링",
        "Spring",
        "spring",
        "자바",
        "Java",
        "java",
        # "Java(Spring)", "java(spring)" 제거 — "Java", "Spring" alias로 커버됨
    ],
    "kotlin": [
        "코틀린",
        "Kotlin",
        "kotlin",
        # "Kotlin(Spring)", "kotlin(spring)" 제거
    ],
    "nestjs": [
        "NestJS",
        "nestjs",
        "Nest",
        "nest",
        "네스트",
        "네스트JS",
        "네스트js",
        "Typescript",
        "typescript",
        # "Typescript(NestJS)", "typescript(nestjs)" 제거 — Typescript 단독으로 대체
    ],
    ...
}
```

옵션 B: `_matches_alias` 내부에서 alias가 `\W`로 끝나는 경우 마지막 `\b`를 생략한다.

```python
def _matches_alias(text: str, alias: str) -> bool:
    if alias.isascii():
        escaped = re.escape(alias)
        last_char = alias[-1]
        suffix = r"\b" if re.match(r"\w", last_char) else ""
        pattern = r"\b" + escaped + suffix
        return bool(re.search(pattern, text, re.ASCII))
    else:
        return alias in text
```

**Rationale**: 작동하지 않는 alias를 제거하면 리스트가 간결해지고 의도와 동작이 일치하게 된다.

---

#### `JavaEE에서` 입력 시 `Java` 미매칭 동작 확인 `Minor`

**File**: `src/convention_qa/query_understanding/alias_normalizer.py` | **Line(s)**: 133-136

**Problem**:

`"JavaEE에서"` 텍스트에서 `Java` alias는 수정 후 `False`를 반환한다. `JavaEE`는 `Java`의 부분 문자열이지만, `\b` 단어 경계 매칭 덕분에 `Java` 단독 alias로는 매칭되지 않는다. 이는 의도된 올바른 동작이다.

그러나 `"Java와 JavaEE를 비교"` 와 같이 `Java` 단독이 함께 있는 경우에는 `True`를 반환한다. 이 역시 올바르다.

**Rationale**: 별도 수정 불필요. 단어 경계 로직이 의도대로 작동함을 확인하는 차원에서 기록한다.

---

### Code Quality

#### alias 리스트 내 중복 및 우선순위 의존 `Minor`

**File**: `src/convention_qa/query_understanding/alias_normalizer.py` | **Line(s)**: 39-73

**Problem**:

`normalize_stack`은 `_STACK_ALIASES`를 순회하며 첫 번째로 매칭되는 alias를 반환한다. `"spring"` 키의 alias 리스트에 `"Java"`, `"java"`, `"Java(Spring)"`, `"java(spring)"` 이 모두 포함되어 있는데, `"Java(Spring)"` 은 앞서 `"Java"` 가 먼저 매칭되므로 사실상 도달 불가한 코드에 해당한다.

동일하게 `"kotlin"` 의 `"Kotlin(Spring)"`, `"nestjs"` 의 `"Typescript(NestJS)"` 도 각각 `"Kotlin"`, `"NestJS"` 에 의해 먼저 매칭된다. 이 중복 항목들이 유지될 경우, 향후 리스트 순서가 변경될 때 예상치 못한 동작 변화가 발생할 수 있다.

**Current Code**:

```python
"spring": [
    "스프링",
    "Spring",
    "spring",
    "자바",
    "Java",      # 여기서 매칭되면
    "java",
    "Java(Spring)",  # 이 줄은 실질적으로 도달하지 않음
    "java(spring)",  # 이 줄도 동일
],
```

**Recommended Fix**:

도달 불가한 alias들을 제거하거나, 주석으로 의도를 명시한다. 만약 `"Java(Spring)"` 만 쓰는 사용자를 별도로 처리해야 한다면, 해당 alias를 리스트 앞으로 이동시키고 의도를 주석으로 문서화한다.

**Rationale**: 리스트의 정확성과 의도가 일치해야 향후 유지보수 시 혼란을 막을 수 있다.

---

#### `_matches_alias` 함수 docstring과 실제 동작 간 불일치 `Minor`

**File**: `src/convention_qa/query_understanding/alias_normalizer.py` | **Line(s)**: 121-124

**Problem**:

수정 후 docstring은 여전히 `re.ASCII` 플래그에 대한 언급 없이 "영문/숫자 alias는 단어 경계 매칭"이라고만 설명한다. 구체적으로 왜 `re.ASCII`가 필요한지(한국어 조사 문제)를 명시하지 않으면 향후 유지보수자가 플래그를 제거할 가능성이 있다.

**Current Code**:

```python
def _matches_alias(text: str, alias: str) -> bool:
    """텍스트 내에서 alias가 단어 단위로 존재하는지 확인한다.

    ASCII alias는 단어 경계(\b) 매칭을, 한국어/비ASCII alias는
    단순 포함(in) 검사를 사용한다.
    ...
    """
```

**Recommended Fix**:

```python
def _matches_alias(text: str, alias: str) -> bool:
    """텍스트 내에서 alias가 단어 단위로 존재하는지 확인한다.

    ASCII alias는 단어 경계(\\b) 매칭을, 한국어/비ASCII alias는
    단순 포함(in) 검사를 사용한다.

    Note:
        ASCII 매칭에 re.ASCII 플래그를 사용한다. 기본 유니코드 모드에서는
        한국어 글자도 \\w로 분류되어 "Java에서" 같은 입력에서 \\b가
        성립하지 않는 문제가 있다. re.ASCII 적용으로 \\w = [a-zA-Z0-9_]로
        제한되어 한국어 조사 앞에서도 정확한 단어 경계 탐지가 가능하다.
    ...
    """
```

**Rationale**: 플래그 추가 배경이 문서화되어야 미래의 리뷰어나 유지보수자가 "왜 re.ASCII가 있는가"를 이해하고 실수로 제거하는 일을 방지할 수 있다.

---

### Testing

#### 수정된 동작에 대한 단위 테스트 부재 `Major`

**File**: `src/convention_qa/query_understanding/alias_normalizer.py`

**Problem**:

티켓에 테스트 케이스 표가 명시되어 있으나, 코드베이스 내에 `alias_normalizer.py`에 대한 자동화 단위 테스트 파일이 확인되지 않는다. 특히 이번처럼 정규 표현식 플래그 변경이 한국어 입력과의 상호작용에 의존하는 경우, 단위 테스트 없이는 향후 동일 버그가 재발하더라도 감지되지 않는다.

이번 수정으로 기존에 우연히 작동하던 `"Java(Spring)으로"` 케이스가 `False`로 역전되었는데, 이러한 변화를 잡아낼 회귀 테스트가 없다.

**Recommended Fix**:

```python
# tests/convention_qa/query_understanding/test_alias_normalizer.py

import pytest
from src.convention_qa.query_understanding.alias_normalizer import (
    normalize_stack,
    normalize_domain,
    _matches_alias,
)

class TestMatchesAlias:
    # 핵심 버그 케이스 (P1-BUG-02)
    def test_ascii_alias_with_korean_postposition(self):
        assert _matches_alias("Java에서 트랜잭션", "Java") is True

    def test_ascii_alias_with_ascii_context(self):
        assert _matches_alias("Java Spring", "Java") is True

    def test_ascii_alias_no_partial_match(self):
        assert _matches_alias("JavaScript", "Java") is False

    def test_ascii_alias_end_of_string(self):
        assert _matches_alias("배워야 할 Java", "Java") is True

    def test_korean_alias_substring_match(self):
        assert _matches_alias("스프링 부트 사용법", "스프링") is True


class TestNormalizeStack:
    def test_java_with_korean_postposition(self):
        assert normalize_stack("Java에서 트랜잭션 관리하는 법") == "spring"

    def test_kotlin_with_korean_postposition(self):
        assert normalize_stack("Kotlin으로 테스트 작성") == "kotlin"

    def test_react_with_korean_context(self):
        assert normalize_stack("React 컴포넌트 구조") == "react"

    def test_no_match(self):
        assert normalize_stack("파이썬으로 API 만들기") is None
```

**Rationale**: 티켓에 정의된 완료 기준에도 "테스트 케이스 전원 통과"가 포함되어 있으므로, 자동화 테스트로 이를 지속적으로 검증해야 한다.

---

## Positive Highlights

- `re.ASCII` 플래그 선택이 기술적으로 정확하다. `re.UNICODE`가 기본값이고 한국어가 `\w`로 분류된다는 원인 분석이 올바르며, 최소한의 변경(단일 플래그 추가)으로 문제를 해결했다.
- `isascii()` 를 이용한 ASCII/비ASCII 분기 처리는 간결하고 의도가 명확하다.
- 한국어 alias에 단순 `in` 검사를 사용하는 설계는 한국어의 어절 경계 문제를 실용적으로 회피한다.
- `normalize_domain`, `normalize_stack`의 공개 API가 단순하고 호출부(`intent_classifier.py`)와의 연계가 명확하다.
- `re.escape(alias)`를 사용하여 alias 내 특수문자(`(`, `)`, `-` 등)를 자동으로 이스케이프하는 처리는 올바르다.

---

## Action Items Summary

| Priority | Issue | File | Line |
|----------|-------|------|------|
| Major | `)`로 끝나는 6개 alias의 `\b` 매칭 영구 실패 (수정과 무관한 기존 결함) | `alias_normalizer.py` | 39-73 |
| Major | `_matches_alias`에 대한 단위 테스트 없음 | 신규 파일 필요 | - |
| Minor | 도달 불가한 alias 항목 (`Java(Spring)` 등) 존재 | `alias_normalizer.py` | 47-48, 54-55, 65-66 |
| Minor | `_matches_alias` docstring에 `re.ASCII` 사용 이유 미문서화 | `alias_normalizer.py` | 121-124 |

---

## Recommendations for Future Work

- **`)`로 끝나는 alias 처리 전략 결정**: 옵션 A(제거)가 권장이나, 만약 `"Java(Spring)"` 이라는 표현을 입력하는 사용자를 실제로 대응해야 한다면 `_matches_alias`에서 alias 마지막 문자가 `\W`인 경우 후행 `\b`를 생략하는 옵션 B를 채택한다.
- **`alias_normalizer.py` 단위 테스트 작성**: P1-BUG-02 티켓의 완료 기준에 테스트 통과가 명시되어 있다. `pytest` 기반 테스트 파일을 `tests/convention_qa/query_understanding/` 경로에 추가한다.
- **대소문자 처리 전략 문서화**: 현재 `"Spring"`과 `"spring"`을 별도 alias로 관리한다. 향후 alias 추가 시 일관성을 위해 대소문자 정책을 주석 또는 PLAN.md에 명시한다.
- **`"back"` alias와 `"backend"` 부분 매칭 가능성**: `_BACKEND_ALIASES`에 `"back"`이 있는데, `"back-end"`, `"back end"` 같은 입력에서 `"back"` 단독이 먼저 매칭된다. 이는 의도된 동작일 수 있으나, alias 리스트에서 더 구체적인 항목을 앞에 배치하는 규칙을 문서화하면 유지보수 시 혼란을 줄일 수 있다.
