# Code Review Report

**Date**: 2026-03-24
**Reviewed Files**:
- `src/convention_qa/query_understanding/alias_normalizer.py`
- `tests/convention_qa/query_understanding/test_alias_normalizer.py`
**Ticket**: P3-BUG-06 — alias_normalizer 도달 불가 alias 및 Kotlin(Spring) 의미 오류
**Reviewer**: AI Code Reviewer
**Severity Legend**: Critical | Major | Minor | Suggestion

---

## Executive Summary

P3-BUG-06 티켓의 두 가지 문제(현상 A: Kotlin(Spring) 의미 오류, 현상 B: 도달 불가 alias 6개)를 올바르게 해결했다. dict 순서 변경(kotlin -> spring)으로 현상 A를 수정하고, 괄호 종료 alias 6개 제거로 현상 B를 해결했다. 신규 테스트 2개도 티켓 요건과 정확히 대응된다. 다만 현상 A 수정(dict 순서)과 현상 B 수정(alias 제거)이 서로 독립적인 수정임에도 코드나 주석에서 이 구분이 명시되지 않아 유지보수 시 의도 파악이 어려울 수 있다. 또한 dict 순서 의존성이라는 암묵적인 결합이 새로 생성되었는데, 이에 대한 경고 주석이 없다.

**Overall Score**: 8/10

---

## Findings

### Correctness & Logic

#### "Kotlin(Spring)으로 개발" 의도 해석에 대한 스펙 불명확 `Minor`
**File**: `tests/convention_qa/query_understanding/test_alias_normalizer.py` | **Line(s)**: 52-58

**Problem**:
티켓 스펙 테이블은 `normalize_stack("Kotlin(Spring)으로 개발")` → `"kotlin"` 을 명시하고, `normalize_stack("Java(Spring) 프로젝트")` → `"spring"` 도 명시한다. 현재 구현은 두 케이스 모두 티켓 스펙대로 동작하지만, 이 결과가 "dict 순서에 의존하여 우연히 올바른 값이 반환되는 것"임이 테스트 docstring에서 드러나지 않는다.

구체적으로:
- `"Kotlin(Spring)으로 개발"` → `"kotlin"` 키가 먼저 순회되어 `"Kotlin"` alias가 `(Spring)` 앞부분에 매칭됨.
- `"Java(Spring) 프로젝트"` → `"kotlin"` 순회 시 매칭 없음, `"spring"` 키 순회 시 `"Java"` alias가 매칭되어 `"spring"` 반환.

즉 두 테스트 모두 "괄호 내용을 무시하고 괄호 앞 기술명으로 분류한다"는 암묵적 정책에 의존하고 있다. 이 정책이 명시되지 않으면, 향후 `_STACK_ALIASES`에 `"java"` 관련 alias가 `"kotlin"` 앞에 추가되거나 dict 순서가 재조정될 경우 `test_kotlin_spring_maps_to_kotlin`이 조용히 실패한다.

**Current Code**:
```python
def test_kotlin_spring_maps_to_kotlin(self):
    """P3-BUG-06 회귀: Kotlin(Spring) 조합은 kotlin을 반환해야 한다."""
    assert normalize_stack("Kotlin(Spring)으로 개발") == "kotlin"

def test_java_spring_maps_to_spring(self):
    """P3-BUG-06 회귀: Java(Spring) 조합은 spring을 반환해야 한다."""
    assert normalize_stack("Java(Spring) 프로젝트") == "spring"
```

**Recommended Fix**:
docstring에 "kotlin이 spring보다 먼저 순회되어 매칭됨"을 명시한다.

```python
def test_kotlin_spring_maps_to_kotlin(self):
    """P3-BUG-06 회귀: Kotlin(Spring) 조합은 kotlin을 반환해야 한다.

    _STACK_ALIASES에서 "kotlin" 키가 "spring" 키보다 앞에 위치하므로
    입력 내 "Kotlin"이 먼저 매칭된다. dict 순서 변경 시 이 케이스를 확인할 것.
    """
    assert normalize_stack("Kotlin(Spring)으로 개발") == "kotlin"
```

**Rationale**: 순서 의존 동작을 명시하면, 향후 `_STACK_ALIASES` 재정렬 시 이 테스트가 경고 역할을 한다는 것을 유지보수자가 인지할 수 있다.

---

### Maintainability & Architecture

#### dict 순서 의존성이 암묵적으로 도입됨 `Major`
**File**: `src/convention_qa/query_understanding/alias_normalizer.py` | **Line(s)**: 39-67

**Problem**:
`normalize_stack()`은 `_STACK_ALIASES.items()`를 순서대로 순회한다. 현상 A 수정(Kotlin(Spring) -> kotlin 반환)은 `"kotlin"` 키가 `"spring"` 키보다 앞에 위치함으로써 올바르게 동작한다. 그러나 이 순서 의존성은 코드 어디에도 명시되어 있지 않다.

현재 dict 순서:
```
kotlin -> spring -> nestjs -> react
```

이 순서가 유지되어야 `"Kotlin(Spring)으로 개발"` 입력에서 `"kotlin"`이 반환된다. 그러나:
1. 향후 새 스택이 `"kotlin"` 앞에 삽입되면 영향이 없지만, `"kotlin"`과 `"spring"` 사이에 `"java"` 같은 신규 키가 추가된다면 동작이 달라진다.
2. 더 위험한 시나리오: `"kotlin"` alias 목록에 `"spring"` alias 목록과 겹치는 단어가 없음을 가정하고 있지만, 향후 alias 추가 시 이 가정이 깨질 수 있다.

**Current Code**:
```python
_STACK_ALIASES: dict[str, list[str]] = {
    "kotlin": [
        "코틀린",
        "Kotlin",
        "kotlin",
    ],
    "spring": [
        "스프링",
        "Spring",
        "spring",
        "자바",
        "Java",
        "java",
    ],
    ...
}
```

**Recommended Fix**:
dict 상단에 순서 의존성을 명시하는 주석을 추가한다.

```python
# 순서 중요: 상위 키가 하위 키보다 먼저 매칭된다.
# "kotlin"은 "spring"보다 앞에 위치해야 한다.
# 이유: "Kotlin(Spring)" 입력 시 "Spring" alias가 spring 키에 매칭되기 전에
#       "Kotlin" alias가 kotlin 키에 먼저 매칭되어야 올바른 정규화가 가능하다.
# (P3-BUG-06 참조)
_STACK_ALIASES: dict[str, list[str]] = {
    "kotlin": [...],
    "spring": [...],
    ...
}
```

**Rationale**: 순서 의존적인 자료구조는 명시적인 주석 없이는 "안전하게 재정렬 가능한 설정값"으로 오해받기 쉽다. 이는 향후 신규 스택 추가나 알파벳 순 정렬 리팩터링 시 무음 회귀(silent regression)를 유발한다.

---

#### 현상 A(순서 변경)와 현상 B(alias 제거)가 단일 변경으로 묶임 `Minor`
**File**: `src/convention_qa/query_understanding/alias_normalizer.py` | **Line(s)**: 39-67

**Problem**:
P3-BUG-06 티켓은 두 가지 독립적인 문제를 다룬다:
- 현상 A: dict 순서 변경으로 해결 (kotlin이 spring보다 앞)
- 현상 B: 도달 불가 alias 6개 제거로 해결

두 수정이 단일 커밋/변경으로 합쳐졌는데, 변경 주석이나 docstring에 이 구분이 없다. 코드만 보면 "왜 kotlin이 spring보다 앞인가?" 와 "왜 Kotlin(Spring) alias가 없는가?"를 이해하려면 git log나 티켓을 직접 참조해야 한다.

**Recommended Fix**:
인라인 주석으로 각 수정의 의도를 표시한다.

```python
"kotlin": [
    "코틀린",
    "Kotlin",
    "kotlin",
    # "Kotlin(Spring)", "kotlin(spring)" 제거 — P3-BUG-06:
    # re.ASCII 모드에서 ")" 다음 \b가 성립하지 않아 영구 미매칭.
    # "Kotlin" alias가 이를 대체하여 커버한다.
],
"spring": [  # kotlin 다음에 위치해야 함 — P3-BUG-06 현상 A 참조
    "스프링",
    "Spring",
    "spring",
    "자바",
    "Java",
    "java",
    # "Java(Spring)", "java(spring)" 제거 — P3-BUG-06: 동일한 \b 이슈.
],
```

**Rationale**: 인라인 주석은 git blame 없이도 수정 이유를 파악하게 해주며, "왜 더 구체적인 alias를 넣지 않았는가?"라는 의문에 대한 답을 제공한다.

---

### Testing

#### 테스트 실행 결과
bash 실행 권한이 제한되어 pytest를 직접 실행하지 못했다. 정적 분석으로 대체하여 검증한다.

**신규 테스트 정적 검증:**

`test_kotlin_spring_maps_to_kotlin`:
- 입력: `"Kotlin(Spring)으로 개발"`
- `_STACK_ALIASES`를 순서대로 순회: `"kotlin"` 키의 alias 목록 `["코틀린", "Kotlin", "kotlin"]` 중 `"Kotlin"`이 `_matches_alias("Kotlin(Spring)으로 개발", "Kotlin")`에서 평가됨.
- `"Kotlin".isascii()` → `True`, 패턴 `r"\bKotlin\b"`, `re.search(r"\bKotlin\b", "Kotlin(Spring)으로 개발", re.ASCII)` → `"Kotlin"` 뒤가 `(` (`\W`)이므로 `\b` 성립 → 매칭 성공 → `"kotlin"` 반환.
- 기대값: `"kotlin"`. **통과 예상.**

`test_java_spring_maps_to_spring`:
- 입력: `"Java(Spring) 프로젝트"`
- `"kotlin"` 키 순회: `["코틀린", "Kotlin", "kotlin"]` 전부 미매칭.
- `"spring"` 키 순회: `"스프링"` (비ASCII) → `"스프링" in "Java(Spring) 프로젝트"` → `False`. `"Spring"` → `r"\bSpring\b"`, `re.search(r"\bSpring\b", "Java(Spring) 프로젝트", re.ASCII)` → `"Spring"` 앞이 `(` (`\W`), 뒤가 `)` (`\W`) → `\b` 양쪽 모두 `\W`-`\W` 경계 → **\b 미성립.**
- `"spring"` alias → `r"\bspring\b"` → 미매칭. `"자바"` → 미매칭. `"Java"` → `r"\bJava\b"`, `"Java"` 뒤가 `(` (`\W`) → `\b` 성립 → 매칭 성공 → `"spring"` 반환.
- 기대값: `"spring"`. **통과 예상.**

| 신규 테스트 | 정적 분석 결과 |
|---|---|
| `test_kotlin_spring_maps_to_kotlin` | 통과 예상 |
| `test_java_spring_maps_to_spring` | 통과 예상 |

**기존 테스트 회귀 검증:**

| 기존 테스트 | 영향받는 변경 | 회귀 위험 |
|---|---|---|
| `test_java_maps_to_spring` | `"Java"` alias 유지, dict 순서 무관 | 없음 |
| `test_kotlin_maps_to_kotlin` | `"Kotlin"` alias 유지, dict 순서 유지 | 없음 |
| `test_react_maps_to_react` | dict 순서 변경 무관 (최후 키) | 없음 |
| `test_unknown_stack_returns_none` | 제거된 alias는 어차피 미매칭 | 없음 |
| `test_ascii_alias_followed_by_korean_matches` | `_matches_alias` 로직 변경 없음 | 없음 |
| `test_ascii_alias_partial_match_prevented_*` | 동일 | 없음 |

기존 10개 테스트 전원 회귀 없음. 신규 2개 추가로 총 12개.

---

#### test_java_spring_maps_to_spring이 "Spring" alias 매칭에 의존하지 않음 `Suggestion`
**File**: `tests/convention_qa/query_understanding/test_alias_normalizer.py` | **Line(s)**: 56-58

**Problem**:
위 정적 분석에서 확인했듯이, `"Java(Spring) 프로젝트"` 입력에서 `"Spring"` alias는 `re.ASCII` 모드의 `\b` 이슈로 실제로 매칭되지 않는다. `"spring"` 반환은 `"Java"` alias 매칭을 통해 이루어진다. 이는 기술적으로 올바른 결과를 만들지만, 테스트 이름(`test_java_spring_maps_to_spring`)과 docstring("Java(Spring) 조합은 spring을 반환")이 "Java(Spring)이라는 조합을 인식해서 spring을 반환한다"는 인상을 주어 실제 동작 원리와 차이가 있다.

**Recommended Fix**:
docstring을 실제 매칭 경로를 반영하도록 수정한다.

```python
def test_java_spring_maps_to_spring(self):
    """P3-BUG-06 회귀: Java(Spring) 입력은 spring을 반환해야 한다.

    "Java" alias가 괄호 앞부분에 매칭되어 "spring"을 반환한다.
    ("Spring" alias 자체는 괄호 내에서 \\b 미성립으로 매칭되지 않음.)
    """
    assert normalize_stack("Java(Spring) 프로젝트") == "spring"
```

**Rationale**: 정확한 동작 설명은 향후 `_matches_alias` 로직 변경 시 이 테스트의 의미를 올바르게 재해석할 수 있게 한다.

---

## Positive Highlights

- 티켓 스펙에서 제시한 옵션 A(권장)를 채택하여 도달 불가 alias 6개를 깔끔하게 제거했다. 옵션 B(후행 `\b` 조건부 생략)보다 훨씬 단순하고 안전한 선택이다.
- `"kotlin"` → `"spring"` 순서 변경이라는 최소 침습적인 방법으로 현상 A를 해결했다. alias 목록 자체를 수정하거나 `normalize_stack` 로직을 복잡하게 만들지 않았다.
- 신규 테스트 2개가 티켓의 완료 기준 케이스와 1:1로 대응된다.
- `Typescript(NestJS)`, `typescript(nestjs)` alias도 함께 제거하여 동일한 패턴의 결함을 일괄 처리했다.
- P2-BUG-05에서 지적된 이전 리뷰의 Minor 항목("괄호 alias 알려진 결함이 테스트로 고정되지 않음")이 이번 수정을 통해 자연스럽게 해소되었다. 도달 불가 alias 자체를 제거함으로써 xfail 마커로 고정할 필요가 없어졌다.

---

## Action Items Summary

| Priority | Issue | File | Line |
|----------|-------|------|------|
| Major | dict 순서 의존성에 대한 경고 주석 없음 | `alias_normalizer.py` | 39-67 |
| Minor | 현상 A/B 수정 의도를 설명하는 인라인 주석 부재 | `alias_normalizer.py` | 40-51 |
| Minor | `test_kotlin_spring_maps_to_kotlin` docstring에 순서 의존성 미명시 | `test_alias_normalizer.py` | 52-54 |
| Suggestion | `test_java_spring_maps_to_spring` docstring이 실제 매칭 경로와 다름 | `test_alias_normalizer.py` | 56-58 |

---

## Recommendations for Future Work

- **순서 독립적 설계 고려**: 현재 dict 순서 의존성은 `normalize_stack()`이 "first match wins" 방식으로 동작하기 때문에 발생한다. alias 집합 간 겹치는 단어가 늘어날수록 이 취약성이 커진다. 장기적으로는 각 스택의 alias가 서로 배타적으로 유지되도록 alias 정의 시 중복 검사를 추가하거나, 충돌 시 명시적 우선순위 테이블을 도입하는 것을 검토할 수 있다.
- **`"TypeScript"` alias 추가 검토**: `"nestjs"` 키에서 `"Typescript(NestJS)"` alias를 제거했는데, `"TypeScript"` 단독 alias는 `_STACK_ALIASES`에 없다. `"TypeScript"` 입력 시 현재는 `None`이 반환된다. 이것이 의도된 동작인지 확인이 필요하다.
- **alias 제거 후 커버리지 갭 확인**: `"nestjs"` 키에서 `"Typescript(NestJS)"`, `"typescript(nestjs)"` alias를 제거했으나, 이 alias들이 도달 불가 상태였으므로 실제 커버리지 변화는 없다. 다만 이 alias 제거로 인해 사용자가 `"TypeScript(NestJS)"` 입력 시 `"nestjs"`를 기대했을 경우 다른 방법(예: `"NestJS"` alias 매칭)이 여전히 작동함을 확인하는 테스트를 추가하면 좋다.
