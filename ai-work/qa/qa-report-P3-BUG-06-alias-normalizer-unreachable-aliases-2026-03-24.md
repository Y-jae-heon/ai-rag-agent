# QA Report: P3-BUG-06 alias_normalizer 도달 불가 alias 및 Kotlin(Spring) 의미 오류

## Metadata
- **Date**: 2026-03-24
- **Scope**: `src/convention_qa/query_understanding/alias_normalizer.py`, `tests/convention_qa/query_understanding/test_alias_normalizer.py`
- **Ticket**: P3-BUG-06
- **Implementation Status**: Complete
- **Code Review Status**: Complete (Score 8/10)
- **QA Status**: CONDITIONAL PASS

## Executive Summary

P3-BUG-06의 두 현상(현상 A: Kotlin(Spring) 입력 시 spring 반환, 현상 B: `)` 종료 도달 불가 alias 6개 잔존)이 모두 올바르게 수정되었다. `_STACK_ALIASES` dict 순서 변경(kotlin -> spring)과 도달 불가 alias 6개 제거라는 최소 침습적 방법으로 티켓 완료 기준을 충족했으며, pytest 12/12 PASS가 확인되었다. 다만 code-reviewer가 지적한 dict 순서 의존성 경고 주석(Major) 및 docstring 보완(Minor) 2건이 코드에 아직 미반영 상태이다. 이 항목들은 런타임 동작에 영향을 주지 않으나, 향후 alias 추가 시 무음 회귀(silent regression) 위험을 높이는 유지보수 결함으로 판단한다.

---

## Test Scenarios Executed

### Scenario 1: Kotlin(Spring) 입력 시 kotlin 반환 (현상 A 핵심 케이스)
- **Type**: Happy Path / 버그 픽스 검증
- **Input**: `normalize_stack("Kotlin(Spring)으로 개발")`
- **Expected Behavior**: `"kotlin"` 반환
- **Simulated Behavior**: `_STACK_ALIASES` 순회 시 `"kotlin"` 키가 `"spring"` 키보다 먼저 처리된다. `"Kotlin"` alias에 대해 `_matches_alias`는 `re.search(r"\bKotlin\b", "Kotlin(Spring)으로 개발", re.ASCII)`를 수행한다. `"Kotlin"` 뒤 문자가 `(` (`\W`)이므로 `\b` 성립. 매칭 성공 → `"kotlin"` 반환.
- **Result**: PASS
- **Notes**: 수정 전에는 `"spring"` 키가 먼저 순회되어 `"Spring"` alias가 `(Spring)` 부분에 매칭되면서 `"spring"`을 반환했었다. dict 순서 변경으로 명확히 해소됨.

### Scenario 2: Java(Spring) 입력 시 spring 반환
- **Type**: Happy Path / 버그 픽스 검증
- **Input**: `normalize_stack("Java(Spring) 프로젝트")`
- **Expected Behavior**: `"spring"` 반환
- **Simulated Behavior**: `"kotlin"` 키 순회 시 `["코틀린", "Kotlin", "kotlin"]` 전부 미매칭. `"spring"` 키 순회 시 `"스프링"` (비ASCII, in 검사) → False. `"Spring"` → `re.search(r"\bSpring\b", "Java(Spring) 프로젝트", re.ASCII)` → `"Spring"` 앞이 `(`(`\W`), 뒤가 `)`(`\W`) → `\W`-`\W` 경계에서 `\b` 미성립 → 미매칭. `"spring"` → 미매칭. `"자바"` → 비ASCII, in 검사 → False. `"Java"` → `re.search(r"\bJava\b", "Java(Spring) 프로젝트", re.ASCII)` → `"Java"` 뒤가 `(`(`\W`) → `\b` 성립 → `"spring"` 반환.
- **Result**: PASS
- **Notes**: 티켓 스펙과 일치. 단, 반환의 실제 원인은 `"Java"` alias 매칭이며 `"Spring"` alias 매칭이 아님. code-reviewer가 docstring과 실제 동작 불일치를 Suggestion으로 지적했으나, 결과값은 정확하다.

### Scenario 3: Kotlin 단독 입력 회귀
- **Type**: 회귀 (Regression)
- **Input**: `normalize_stack("Kotlin으로 테스트 작성")`
- **Expected Behavior**: `"kotlin"` 반환
- **Simulated Behavior**: `"kotlin"` 키 순회, `"Kotlin"` alias → `re.search(r"\bKotlin\b", "Kotlin으로 테스트 작성", re.ASCII)` → `"Kotlin"` 뒤 `으` (비ASCII, `\W` 범위) → re.ASCII 플래그 하에서 `\b` 성립(ASCII 문자 후 비ASCII 문자) → 매칭 성공 → `"kotlin"` 반환.
- **Result**: PASS
- **Notes**: P1-BUG-02에서 수정된 re.ASCII 동작이 유지됨. 회귀 없음.

### Scenario 4: Java 단독 입력 회귀
- **Type**: 회귀 (Regression)
- **Input**: `normalize_stack("Java에서 트랜잭션 관리")`
- **Expected Behavior**: `"spring"` 반환
- **Simulated Behavior**: `"kotlin"` 키 순회 → 미매칭. `"spring"` 키 순회 → `"Java"` alias → `re.search(r"\bJava\b", "Java에서 트랜잭션 관리", re.ASCII)` → `"Java"` 뒤 `에` (비ASCII) → re.ASCII 하에서 `\b` 성립 → `"spring"` 반환.
- **Result**: PASS
- **Notes**: dict 순서 변경에 의한 영향 없음. 회귀 없음.

### Scenario 5: 도달 불가 alias 6개 제거 확인
- **Type**: 코드 정합성 검증
- **Input**: (코드 정적 분석)
- **Expected Behavior**: `_STACK_ALIASES` 내에 `"Java(Spring)"`, `"java(spring)"`, `"Kotlin(Spring)"`, `"kotlin(spring)"`, `"Typescript(NestJS)"`, `"typescript(nestjs)"` 미존재
- **Simulated Behavior**: `alias_normalizer.py` 소스 코드 확인 결과, 해당 6개 alias는 모두 제거되었으며 각 키(`kotlin`, `spring`, `nestjs`)의 주석에 제거 이유(`\b` 미성립)와 티켓 번호(P3-BUG-06)가 명시됨.
- **Result**: PASS
- **Notes**: Typescript(NestJS) alias도 동일한 `\b` 이슈를 가지고 있어 함께 제거됨. 일괄 처리로 동일 결함 패턴을 해소함.

### Scenario 6: TypeScript(NestJS) 입력 시 NestJS 매칭 확인
- **Type**: 엣지 케이스 (alias 제거 후 커버리지 확인)
- **Input**: `normalize_stack("TypeScript(NestJS)로 개발")`
- **Expected Behavior**: `"nestjs"` 반환 (NestJS alias가 별도 존재하므로)
- **Simulated Behavior**: `"kotlin"` 키 → 미매칭. `"spring"` 키 → 미매칭. `"nestjs"` 키 순회: `"NestJS"` alias → `re.search(r"\bNestJS\b", "TypeScript(NestJS)로 개발", re.ASCII)` → `"NestJS"` 앞이 `(`(`\W`) → `\b` 성립. 뒤가 `)`(`\W`) → `\b` 미성립. `\b`-word-`\W` 패턴 이므로 전방 `\b`만 평가 — 실제로는 `\bNestJS\b` 패턴에서 뒤의 `\b`도 필요하다. `"NestJS"` 마지막 문자 `S` (ASCII) 뒤가 `)` (`\W`) → `\b` 성립 → **매칭 성공** → `"nestjs"` 반환.
- **Result**: PASS
- **Notes**: `"TypeScript(NestJS)로 개발"` 입력에서 `"Typescript(NestJS)"` alias가 제거되었음에도, `"NestJS"` 단독 alias가 괄호 내부의 `NestJS`를 정상 매칭하여 커버리지 갭 없음. code-reviewer가 추가 테스트를 권장한 시나리오이며, 정적 시뮬레이션 결과 기능 정상.

### Scenario 7: 알 수 없는 스택 입력
- **Type**: Edge Case
- **Input**: `normalize_stack("파이썬으로 API 만들기")`
- **Expected Behavior**: `None` 반환
- **Simulated Behavior**: 모든 키 순회 후 매칭 없음. `None` 반환.
- **Result**: PASS
- **Notes**: 회귀 없음.

### Scenario 8: dict 순서 의존성 경계 시나리오 (가상 위험 시뮬레이션)
- **Type**: 위험 시뮬레이션 (코드에 적용하지 않음)
- **Input**: 만약 `"spring"` 키가 `"kotlin"` 키보다 앞에 위치하도록 순서가 변경될 경우
- **Expected Behavior**: `normalize_stack("Kotlin(Spring)으로 개발")` → `"kotlin"`
- **Simulated Behavior**: `"spring"` 키 먼저 순회 → `"Spring"` alias → `re.search(r"\bSpring\b", "Kotlin(Spring)으로 개발", re.ASCII)` → `"Spring"` 앞이 `(`(`\W`) → `\b` 성립. 뒤가 `)`(`\W`) → `\b` 미성립. → **미매칭**. 이후 `"java"` alias 등도 미매칭. `"kotlin"` 키 순회 → `"Kotlin"` 매칭 → `"kotlin"` 반환.
- **Result**: WARNING
- **Notes**: 이 시나리오에서는 우연히 결과가 맞다. 그러나 만약 `"spring"` 키에 `"Kotlin"` 또는 `"kotlin"`과 겹치는 alias가 추가된다면, 순서 변경 시 즉시 오동작이 발생한다. 순서 의존성 경고 주석이 없으면 향후 알파벳 순 정렬 리팩터링 시 무음 회귀 위험이 존재한다.

### Scenario 9: 소문자 normalize_domain 회귀 (FE/BE alias)
- **Type**: 회귀 (Regression)
- **Input**: `normalize_domain("FE에서 처리")`, `normalize_domain("BE에서 API")`
- **Expected Behavior**: `"frontend"`, `"backend"` 반환
- **Simulated Behavior**: `_FRONTEND_ALIASES`, `_BACKEND_ALIASES`는 이번 수정에서 변경되지 않음. `_matches_alias` 로직도 동일. 동작 변화 없음.
- **Result**: PASS
- **Notes**: normalize_domain은 이번 수정 범위 외. 영향 없음.

---

## Issues Found

### Issue #1: dict 순서 의존성에 대한 경고 주석 미반영
- **Severity**: 🟡 MEDIUM
- **Location**: `src/convention_qa/query_understanding/alias_normalizer.py:43-74` (`_STACK_ALIASES` 정의부)
- **Description**: code-reviewer가 Major로 지적한 항목이다. `normalize_stack()`은 `_STACK_ALIASES.items()` 를 순서대로 순회하는 first-match-wins 방식이며, `"kotlin"` 키가 `"spring"` 키보다 앞에 위치해야 `"Kotlin(Spring)으로 개발"` 입력에서 `"kotlin"`이 반환된다. 현재 코드에는 `"kotlin"이 "spring"보다 먼저 와야 한다`는 간략한 1줄 주석이 있으나, 이 경고가 왜 필요한지(dict 순서 재정렬 시 어떤 케이스가 깨지는지)에 대한 설명이 없다. code-reviewer의 권장 주석 형태(왜 이 순서여야 하는지, 변경 시 어떤 테스트가 깨지는지)는 미반영 상태다.
- **Reproduction Steps**:
  1. `_STACK_ALIASES`에서 `"spring"` 키를 `"kotlin"` 키 앞으로 이동
  2. `normalize_stack("Kotlin(Spring)으로 개발")` 실행
  3. `"spring"` 또는 `"kotlin"` 반환 여부 확인 (현재 구조에서는 우연히 `"kotlin"`이 반환되지만, alias 목록이 달라지면 달라짐)
- **Expected vs Actual**: 경고 주석이 충분히 명시적이어야 향후 리팩터링 시 "안전하게 재정렬 가능한 설정값"으로 오인하지 않는다. 현재 주석은 규칙은 있으나 이유와 위험이 충분히 설명되지 않는다.
- **Recommendation**: code-reviewer의 권장 형태로 dict 상단 주석을 보강한다. `"kotlin"은 "spring"보다 앞에 위치해야 하며, 이 순서 변경 시 test_kotlin_spring_maps_to_kotlin이 실패한다`는 내용을 명시한다.

### Issue #2: test_kotlin_spring_maps_to_kotlin docstring에 순서 의존성 미명시
- **Severity**: 🟢 LOW
- **Location**: `tests/convention_qa/query_understanding/test_alias_normalizer.py:52-59`
- **Description**: code-reviewer가 Minor로 지적한 항목이다. 현재 docstring은 `_STACK_ALIASES에서 "kotlin" 키가 "spring" 키보다 먼저 순회되므로 "Kotlin" alias가 먼저 매칭된다. dict 순서가 바뀌면 이 테스트가 깨진다.`라는 내용이 이미 반영되어 있다. code-reviewer의 권장 형태와 비교하면 차이가 미미하다.
- **Reproduction Steps**: 해당 없음 (이미 일부 반영됨)
- **Expected vs Actual**: 현재 docstring이 code-reviewer의 권장 형태와 거의 동일하게 이미 반영되어 있어, 이 항목은 경미한 차이만 존재한다. code-reviewer가 리뷰 시점에 아직 이 내용이 반영되지 않은 상태를 보았을 가능성이 있다.
- **Recommendation**: 현재 코드를 재확인한 결과 docstring에 `_STACK_ALIASES에서 "kotlin" 키가 "spring" 키보다 먼저 순회되므로 / "Kotlin" alias가 먼저 매칭된다. dict 순서가 바뀌면 이 테스트가 깨진다.`가 명시되어 있다. 이 항목은 이미 수용된 것으로 판단한다. 추가 조치 불필요.

### Issue #3: test_java_spring_maps_to_spring docstring이 실제 매칭 경로와 불일치
- **Severity**: 🟢 LOW
- **Location**: `tests/convention_qa/query_understanding/test_alias_normalizer.py:61-66`
- **Description**: code-reviewer가 Suggestion으로 지적한 항목이다. docstring에 `"kotlin" 키에 "Java" alias가 없으므로 "spring" 키의 "Java" alias가 매칭된다`라고 명시되어 있어, 실제 매칭 경로(Java alias → spring 반환)를 올바르게 설명하고 있다. 그러나 `("Spring" alias 자체는 괄호 내에서 \b 미성립으로 매칭되지 않음)` 이라는 보충 설명이 없어, `"Spring"` alias가 `(Spring)` 내에서 매칭된다고 오해할 여지가 남아 있다.
- **Reproduction Steps**:
  1. `normalize_stack("Java(Spring) 프로젝트")` 실행 중 `"spring"` 키 순회 시 어떤 alias가 실제로 매칭되는지 트레이스
  2. `"Spring"` alias는 `\b` 미성립으로 미매칭, `"Java"` alias가 매칭됨을 확인
- **Expected vs Actual**: docstring이 `"Java"` alias 매칭임을 명시하지만, `"Spring"` alias 미매칭 이유를 설명하지 않아 독자가 오해할 수 있다.
- **Recommendation**: docstring에 `("Spring" alias는 괄호 내에서 \b 미성립으로 매칭되지 않음)`을 추가한다. 기능 동작에는 영향 없음.

### Issue #4: TypeScript 단독 alias 미존재 (잠재적 커버리지 갭)
- **Severity**: 💡 SUGGESTION
- **Location**: `src/convention_qa/query_understanding/alias_normalizer.py:59-68` (`"nestjs"` alias 목록)
- **Description**: code-reviewer의 Future Work 권장 항목이다. `"Typescript(NestJS)"`, `"typescript(nestjs)"` alias가 도달 불가 상태였으므로 실제 커버리지에는 변화가 없다. 그러나 `_STACK_ALIASES`에 `"TypeScript"` 단독 alias가 없어, `normalize_stack("TypeScript로 개발")` 입력 시 `None`이 반환된다. 이것이 의도된 동작인지 확인이 필요하다.
- **Reproduction Steps**:
  1. `normalize_stack("TypeScript로 개발")` 실행
  2. 반환값 확인 → `None`
- **Expected vs Actual**: 사용자가 TypeScript를 NestJS 문서로 연결하길 원한다면, `"TypeScript"` alias를 `"nestjs"` 키에 추가해야 한다. 그렇지 않다면 현재 동작이 의도된 것.
- **Recommendation**: 의도된 동작인지 스펙을 명확히 정의한다. TypeScript를 nestjs로 연결할 경우 `"TypeScript"`, `"typescript"` alias 추가를 고려한다. 단, 이는 이번 P3-BUG-06 범위 밖이며 별도 티켓으로 처리를 권장한다.

---

## Code Review Compliance

code-reviewer가 제시한 Action Items 4개 중 처리 현황은 다음과 같다:

| Priority | Issue | 반영 여부 |
|----------|-------|-----------|
| Major | dict 순서 의존성 경고 주석 미반영 | 부분 반영 (간략 주석 존재, 보강 필요) |
| Minor | 현상 A/B 수정 의도 인라인 주석 부재 | 반영됨 (각 alias 목록에 `\b` 미성립 설명 주석 추가됨) |
| Minor | test_kotlin_spring_maps_to_kotlin docstring 순서 의존성 미명시 | 반영됨 (docstring에 순서 의존성 명시됨) |
| Suggestion | test_java_spring_maps_to_spring docstring과 실제 매칭 경로 불일치 | 미반영 (Java alias 언급 있으나 Spring alias 미매칭 이유 누락) |

Major 1건이 부분 반영 상태이며, Suggestion 1건이 미반영이다. 런타임 동작에는 영향 없으나 유지보수성 위험으로 잔존한다.

---

## Risk Assessment

**배포 위험 수준: 낮음**

핵심 버그 2건(현상 A: 의미 오류, 현상 B: 도달 불가 alias)이 모두 해소되었으며 pytest 12/12 PASS를 확인했다. 발견된 이슈는 모두 주석/docstring 수준의 유지보수성 문제이며, 현재 런타임 동작에 영향을 주지 않는다.

유일한 중기 위험은 `_STACK_ALIASES` dict 순서 의존성 경고 주석의 부재이다. 현재 팀이 alias 추가/정렬 리팩터링을 진행할 경우 `test_kotlin_spring_maps_to_kotlin`이 silent regression으로 실패할 수 있다. 이 위험은 `test_kotlin_spring_maps_to_kotlin` 테스트 자체가 이미 존재하여 어느 정도 방어되고 있으나, 경고 주석 보강으로 위험을 더 줄일 수 있다.

---

## Recommendations

1. **(배포 전 권장)** `_STACK_ALIASES` dict 상단에 순서 의존성 경고 주석을 보강한다. `"kotlin"은 "spring"보다 앞에 위치해야 하며, 이 순서 변경 시 test_kotlin_spring_maps_to_kotlin이 실패한다` 수준으로 명시한다. 런타임 영향 없음. 소요 시간 5분 이내.
2. **(배포 후 선택)** `test_java_spring_maps_to_spring` docstring에 `("Spring" alias 자체는 괄호 내에서 \b 미성립으로 매칭되지 않음)` 보충 설명을 추가한다.
3. **(별도 티켓 검토)** `TypeScript` 단독 alias 미존재 여부를 스펙으로 확정하고, 필요 시 `"nestjs"` 키에 `"TypeScript"`, `"typescript"` alias를 추가하는 별도 작업을 계획한다.

---

## Sign-off
- **QA Engineer (AI)**: qa-reporter
- **Verdict**: CONDITIONAL PASS — 배포 가능하나, dict 순서 의존성 경고 주석 보강(Issue #1) 후 최종 확정 권장
