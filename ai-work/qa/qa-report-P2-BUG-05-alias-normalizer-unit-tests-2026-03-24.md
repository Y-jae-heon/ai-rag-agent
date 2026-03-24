# QA Report: P2-BUG-05 — alias_normalizer 단위 테스트 파일 생성

## Metadata
- **Date**: 2026-03-24
- **Scope**: `tests/convention_qa/query_understanding/test_alias_normalizer.py` 신규 생성 및 테스트 케이스 10개 검증
- **Implementation Status**: Complete
- **Code Review Status**: 병렬 진행 중 (QA 선행)
- **QA Status**: PASS

---

## Executive Summary

P2-BUG-05 티켓의 완료 기준 3개 항목이 모두 충족되었다. 티켓에 명시된 10개 테스트 케이스가 구현 파일에 1:1 대응되며, 소스 코드 정적 추적을 통해 각 케이스의 통과 근거가 확인된다. 핵심 회귀 방지 효과 — `re.ASCII` 플래그 제거 시 `test_ascii_alias_followed_by_korean_matches`가 실패하는 메커니즘 — 도 논리적으로 검증되었다. 누락 테스트 케이스 3건이 식별되나, 티켓 완료 기준을 벗어나는 추가 커버리지 항목으로 현재 배포를 차단하지 않는다.

---

## Test Scenarios Executed

### Scenario 1: _matches_alias — ASCII alias + 한국어 조사 (핵심 버그 회귀 케이스)
- **Type**: Happy Path (버그 회귀 방지)
- **Input**: `_matches_alias("Java에서 트랜잭션", "Java")`
- **Expected Behavior**: `True`
- **Simulated Behavior**: `"Java".isascii()` → True → `pattern = r"\bJava\b"`, `re.ASCII` 플래그 적용 → `에`는 ASCII 모드에서 `\W`로 분류 → `Java` 뒤 `\b` 성립 → `True` 반환
- **Result**: PASS
- **Notes**: `re.ASCII` 없이 기본 유니코드 모드에서는 `에`가 `\w`로 분류되어 `\b` 불성립 → `False` 반환. 해당 테스트가 회귀 감지의 핵심 케이스임.

---

### Scenario 2: _matches_alias — 부분 일치 방지 (ASCII suffix)
- **Type**: Edge Case
- **Input**: `_matches_alias("JavaScript", "Java")`
- **Expected Behavior**: `False`
- **Simulated Behavior**: `pattern = r"\bJava\b"`, `re.ASCII` → `S`는 ASCII `\w` → `Java` 뒤 `\b` 불성립 → `False` 반환
- **Result**: PASS
- **Notes**: `re.ASCII` 존재 여부와 무관하게 `S`는 항상 ASCII `\w`. 이 케이스는 회귀 방지보다 정상 동작 보증에 해당.

---

### Scenario 3: _matches_alias — 부분 일치 방지 (mixed suffix: ASCII + 한국어)
- **Type**: Edge Case
- **Input**: `_matches_alias("JavaEE에서 트랜잭션", "Java")`
- **Expected Behavior**: `False`
- **Simulated Behavior**: `E`는 ASCII `\w` → `Java` 뒤(E 앞) `\b` 불성립 → `False` 반환
- **Result**: PASS
- **Notes**: `JavaEE에서` 패턴에서 `Java`와 `EE` 사이에 단어 경계 없음. ASCII 문자 경계이므로 `re.ASCII` 영향 없음.

---

### Scenario 4: _matches_alias — 비ASCII alias (한국어 포함 검사)
- **Type**: Happy Path
- **Input**: `_matches_alias("스프링으로 개발", "스프링")`
- **Expected Behavior**: `True`
- **Simulated Behavior**: `"스프링".isascii()` → False → `"스프링" in "스프링으로 개발"` → True → `True` 반환
- **Result**: PASS
- **Notes**: `isascii()` 분기로 한국어 alias는 단순 포함 검사 경로 진입. `re.ASCII` 적용 없음. 이 경로는 P1-BUG-02 수정 전후 동일하게 동작.

---

### Scenario 5: normalize_stack — Java 입력 → "spring" 반환
- **Type**: Happy Path
- **Input**: `normalize_stack("Java에서 트랜잭션 관리하는 법")`
- **Expected Behavior**: `"spring"`
- **Simulated Behavior**: `_STACK_ALIASES["spring"]` 순회 → `"Java"` alias에 대해 `_matches_alias("Java에서 트랜잭션 관리하는 법", "Java")` → Scenario 1 경로 → `True` → `"spring"` 반환
- **Result**: PASS
- **Notes**: `_STACK_ALIASES` dict에서 `"spring"`이 `"kotlin"`보다 먼저 순회되므로, `"spring"` 키 내 `"Java"` alias가 먼저 매칭됨.

---

### Scenario 6: normalize_stack — Kotlin 입력 → "kotlin" 반환
- **Type**: Happy Path
- **Input**: `normalize_stack("Kotlin으로 테스트 작성")`
- **Expected Behavior**: `"kotlin"`
- **Simulated Behavior**: `"spring"` 키 내 alias 순회 → `"스프링"`, `"Spring"`, `"spring"`, `"자바"`, `"Java"`, `"java"`, `"Java(Spring)"`, `"java(spring)"` 모두 불일치 → `"kotlin"` 키 순회 → `"Kotlin"` alias에 대해 `_matches_alias("Kotlin으로 테스트 작성", "Kotlin")` → `으`는 `re.ASCII` 모드에서 `\W` → `\b` 성립 → `True` → `"kotlin"` 반환
- **Result**: PASS
- **Notes**: `"spring"` 키 내 `"Spring"` alias와 `"Kotlin으로 테스트 작성"` 입력 간에 `Spring`이 포함되지 않으므로 오탐 없음.

---

### Scenario 7: normalize_stack — React 입력 → "react" 반환
- **Type**: Happy Path
- **Input**: `normalize_stack("React 컴포넌트 구조")`
- **Expected Behavior**: `"react"`
- **Simulated Behavior**: `"spring"`, `"kotlin"`, `"nestjs"` 키 순회 후 불일치 → `"react"` 키 → `"React"` alias → `_matches_alias("React 컴포넌트 구조", "React")` → `React` 뒤 공백 → `\b` 성립(`re.ASCII` 여부 무관) → `True` → `"react"` 반환
- **Result**: PASS
- **Notes**: 공백 경계는 ASCII/유니코드 무관하게 항상 `\b` 성립. 이 케이스는 회귀에 민감하지 않음.

---

### Scenario 8: normalize_stack — 알 수 없는 스택 → None 반환
- **Type**: Edge Case
- **Input**: `normalize_stack("파이썬으로 API 만들기")`
- **Expected Behavior**: `None`
- **Simulated Behavior**: 모든 스택 키(`spring`, `kotlin`, `nestjs`, `react`) 내 alias 전수 순회 → 입력에 `스프링`, `Spring`, `spring`, `자바`, `Java`, `java`, `코틀린`, `Kotlin`, `kotlin`, `NestJS`, `Nest`, `네스트`, `React`, `react`, `리액트` 중 어느 것도 포함되지 않음 → `None` 반환
- **Result**: PASS
- **Notes**: `"파이썬"`, `"API"` 는 어떤 alias와도 일치하지 않음.

---

### Scenario 9: normalize_domain — FE alias → "frontend" 반환
- **Type**: Happy Path
- **Input**: `normalize_domain("FE에서 처리")`
- **Expected Behavior**: `"frontend"`
- **Simulated Behavior**: `_FRONTEND_ALIASES` 순회 → `"FE"` alias → `_matches_alias("FE에서 처리", "FE")` → `"FE".isascii()` → True → `pattern = r"\bFE\b"`, `re.ASCII` → `에`는 `re.ASCII`에서 `\W` → `FE` 뒤 `\b` 성립 → `True` → `"frontend"` 반환
- **Result**: PASS
- **Notes**: 이 케이스도 `re.ASCII` 없이는 `에`가 `\w`로 분류되어 실패한다. Scenario 1과 동일한 회귀 방지 메커니즘이 적용됨.

---

### Scenario 10: normalize_domain — BE alias → "backend" 반환
- **Type**: Happy Path
- **Input**: `normalize_domain("BE에서 API")`
- **Expected Behavior**: `"backend"`
- **Simulated Behavior**: `_FRONTEND_ALIASES` 순회 → `"BE"`는 프론트엔드 alias에 없음 → 불일치 → `_BACKEND_ALIASES` 순회 → `"BE"` alias → `_matches_alias("BE에서 API", "BE")` → Scenario 9와 동일 메커니즘 → `True` → `"backend"` 반환
- **Result**: PASS
- **Notes**: `_FRONTEND_ALIASES`에 `"BE"` alias가 없어 오탐 없음.

---

## 회귀 방지 효과 검증 (re.ASCII 제거 시뮬레이션)

이 섹션은 테스트 파일이 실제로 회귀를 감지하는지 논리적으로 추적한다.

### 시뮬레이션 가정: `_matches_alias`에서 `re.ASCII` 플래그 제거

```python
# 회귀 코드 (re.ASCII 제거)
pattern = r"\b" + re.escape(alias) + r"\b"
return bool(re.search(pattern, text))  # re.ASCII 없음
```

유니코드 모드에서 `에`, `으로`, `에서` 등 한국어 글자는 `\w` 범주에 포함된다.

| 테스트 케이스 | re.ASCII 있음 | re.ASCII 없음 | 기대값 | 탐지 여부 |
|-------------|--------------|--------------|-------|---------|
| `_matches_alias("Java에서 트랜잭션", "Java")` | True | False (`에`가 `\w`, `\b` 불성립) | True | CAUGHT |
| `_matches_alias("JavaScript", "Java")` | False | False | False | N/A (회귀 무관) |
| `_matches_alias("JavaEE에서 트랜잭션", "Java")` | False | False (`E`는 항상 `\w`) | False | N/A (회귀 무관) |
| `_matches_alias("스프링으로 개발", "스프링")` | True | True (비ASCII 경로 불변) | True | N/A (회귀 무관) |
| `normalize_stack("Java에서 트랜잭션 관리하는 법")` | "spring" | None | "spring" | CAUGHT |
| `normalize_domain("FE에서 처리")` | "frontend" | None | "frontend" | CAUGHT |
| `normalize_domain("BE에서 API")` | "backend" | None | "backend" | CAUGHT |

`re.ASCII` 제거 시 `test_ascii_alias_followed_by_korean_matches`, `test_java_maps_to_spring`, `test_fe_alias_maps_to_frontend`, `test_be_alias_maps_to_backend` 4개 케이스가 실패한다. 회귀 방지 효과가 충분하다.

---

## 티켓 완료 기준 체크리스트

| 완료 기준 | 충족 여부 | 근거 |
|-----------|----------|------|
| `tests/convention_qa/query_understanding/test_alias_normalizer.py` 파일 생성 | 충족 | 파일 존재 확인 (61줄) |
| 티켓 명시 10개 테스트 케이스 전원 pytest 통과 | 충족 | 사용자 제공 pytest 결과: 10 passed in 0.53s |
| `__init__.py` 파일 필요 시 함께 생성 | 충족 | `tests/convention_qa/__init__.py`, `tests/convention_qa/query_understanding/__init__.py` 모두 생성 확인 |

---

## Issues Found

### Issue #1: normalize_domain FE/BE 테스트 케이스의 회귀 방지 커버리지 부분적 중복
- **Severity**: LOW
- **Location**: `tests/convention_qa/query_understanding/test_alias_normalizer.py:53-60`
- **Description**: `test_fe_alias_maps_to_frontend`와 `test_be_alias_maps_to_backend`는 `normalize_domain`의 정상 동작을 검증하나, `_matches_alias` 레벨에서 직접 `re.ASCII` 회귀를 감지하는 `test_ascii_alias_followed_by_korean_matches`와 의존하는 핵심 메커니즘이 동일하다. 중복은 아니나, 두 계층이 모두 실패하면 어느 레벨의 문제인지 진단이 약간 복잡해질 수 있다.
- **Recommendation**: 현재 구조 유지. 필요시 향후 도메인 테스트 클래스에 별도 회귀 케이스(`_matches_alias("FE에서", "FE")`) 추가를 고려할 수 있으나 필수 아님.

---

### Issue #2: normalize_stack 대소문자 혼용 alias 커버리지 미포함
- **Severity**: LOW
- **Location**: `tests/convention_qa/query_understanding/test_alias_normalizer.py:37-50`
- **Description**: `_STACK_ALIASES["spring"]`에는 `"spring"` (소문자), `"자바"` alias가 포함되어 있으나, 이에 대한 테스트 케이스가 없다. 예를 들어 `normalize_stack("spring 설정")`, `normalize_stack("자바로 개발")` 등의 케이스가 없다. 티켓 완료 기준에 명시된 범위를 벗어나므로 차단 이슈는 아니다.
- **Recommendation**: 추후 테스트 보강 시 소문자 alias와 한국어 alias에 대한 케이스 추가. 별도 티켓으로 관리 권장.

---

### Issue #3: normalize_domain "fe", "be" 소문자 alias 테스트 미포함
- **Severity**: LOW
- **Location**: `tests/convention_qa/query_understanding/test_alias_normalizer.py:53-60`
- **Description**: `_FRONTEND_ALIASES`에 `"fe"` (소문자)가 포함되어 있으나, `normalize_domain("fe에서 작업")`과 같은 소문자 입력 케이스가 없다. `"fe".isascii()` → True → `re.ASCII` 경로 진입으로 동일 회귀 위험에 노출되어 있으나 테스트되지 않았다.
- **Recommendation**: 추후 테스트 보강 시 소문자 alias 케이스 추가. 우선순위 낮음.

---

## Code Review Compliance

P1-BUG-02 QA 리포트(`ai-work/qa/qa-report-P1-BUG-02-alias-normalizer-re-ascii-2026-03-24.md`)에서 Issue #2로 지적된 "alias_normalizer.py 단위 테스트 파일 미존재 (MEDIUM)" 항목이 본 티켓(P2-BUG-05)으로 트래킹되어 구현 완료되었다.

P1-BUG-02 QA 리포트 당시 Code Review Compliance 표에서 "단위 테스트 부재 (Major) — 미반영" 항목이 이번 구현으로 해소되었다.

---

## Risk Assessment

배포 위험도: **없음 (NONE)**

테스트 파일 추가는 프로덕션 코드를 변경하지 않는다. `__init__.py` 파일도 기존 패키지 구조에 맞게 생성되어 import 충돌이나 사이드 이펙트가 없다. 10개 테스트가 0.53초에 통과하므로 CI 빌드 타임에 미치는 영향도 무시할 수준이다.

---

## Recommendations

1. **[LOW — 추후]** `normalize_stack` 및 `normalize_domain`의 소문자 alias, 한국어 alias 테스트 케이스 보강. 별도 테스트 보강 티켓 또는 기존 테스트 파일 확장으로 처리.

2. **[LOW — 추후]** P1-BUG-02 잔존 이슈(`Kotlin(Spring)` 의미 오류, 도달 불가 alias, docstring 미문서화)는 본 티켓 범위 외이며 해당 티켓에서 별도 관리.

---

## Sign-off
- **QA Engineer (AI)**: qa-reporter
- **Verdict**: APPROVED FOR DEPLOYMENT
