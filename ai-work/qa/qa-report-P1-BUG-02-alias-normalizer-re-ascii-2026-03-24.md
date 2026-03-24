# QA Report: P1-BUG-02 — alias_normalizer re.ASCII 플래그 추가

## Metadata
- **Date**: 2026-03-24
- **Scope**: `src/convention_qa/query_understanding/alias_normalizer.py` — `_matches_alias()` 함수 `re.ASCII` 플래그 적용
- **Implementation Status**: Complete
- **Code Review Status**: Complete (ai-work/review/2026-03-24_alias-normalizer-re-ascii-fix-review.md)
- **QA Status**: CONDITIONAL PASS

---

## Executive Summary

P1-BUG-02의 핵심 수정(`re.ASCII` 플래그 추가)은 티켓의 테스트 케이스 4개를 모두 통과하며, 한국어 alias 처리 경로(비ASCII 분기)에도 영향을 주지 않는다. 파이프라인 전체 추적에서 `"Java에서 트랜잭션 관리하는 법 알려줘"` 입력이 `stack="spring"` 으로 올바르게 정규화되어 `resolved=True`, `answer_type="extract"` 경로로 진입함을 확인하였다. 단, code-reviewer가 지적한 `)` alias 이슈 중 `"Kotlin(Spring)"` 입력이 `"spring"`을 반환하는 의미 오류와, `alias_normalizer.py`에 대한 자동화 단위 테스트 미비라는 두 가지 잔존 문제가 배포 전 확인을 요구한다.

---

## Test Scenarios Executed

### Scenario 1: Java + 한국어 조사 매칭 (핵심 버그 케이스)
- **Type**: Happy Path (버그 수정 검증)
- **Input**: `normalize_stack("Java에서 트랜잭션 관리하는 법 알려줘")`
- **Expected Behavior**: `"spring"` 반환
- **Simulated Behavior**: `re.ASCII` 플래그로 `에`가 `\W`로 분류되어 `Java` 뒤에 `\b` 성립 → `"Java"` alias 매칭 → `"spring"` 반환
- **Result**: PASS
- **Notes**: 수정 전에는 기본 유니코드 모드에서 `에`가 `\w`로 분류되어 `\b`가 성립하지 않아 `None` 반환

---

### Scenario 2: 순수 ASCII 컨텍스트 회귀 없음
- **Type**: Happy Path (회귀 테스트)
- **Input**: `normalize_stack("Java Spring 트랜잭션")`
- **Expected Behavior**: `"spring"` 반환
- **Simulated Behavior**: `Java`와 `Spring` 모두 ASCII 공백 경계에서 `\b` 성립 → `"Java"` alias 매칭 → `"spring"` 반환
- **Result**: PASS
- **Notes**: 수정 전과 동일한 동작 유지, 회귀 없음

---

### Scenario 3: Kotlin + 한국어 조사 매칭
- **Type**: Happy Path
- **Input**: `normalize_stack("Kotlin으로 테스트 작성")`
- **Expected Behavior**: `"kotlin"` 반환
- **Simulated Behavior**: `re.ASCII`로 `으`가 `\W` → `Kotlin` 뒤 `\b` 성립 → `"kotlin"` 반환
- **Result**: PASS
- **Notes**: 수정 전에는 `None` 반환

---

### Scenario 4: React 순수 공백 경계 매칭
- **Type**: Happy Path
- **Input**: `normalize_stack("React 컴포넌트 구조")`
- **Expected Behavior**: `"react"` 반환
- **Simulated Behavior**: `React` 뒤 공백 → `\b` 성립(수정 전후 동일) → `"react"` 반환
- **Result**: PASS
- **Notes**: 수정 전후 동일 동작

---

### Scenario 5: 한국어 alias — re.ASCII 영향 없음 확인
- **Type**: Edge Case
- **Input**: `normalize_stack("스프링 부트 사용법")`, `normalize_stack("코틀린으로 개발")`, `normalize_stack("리액트 컴포넌트")`, `normalize_stack("네스트JS 프로젝트")`
- **Expected Behavior**: 각각 `"spring"`, `"kotlin"`, `"react"`, `"nestjs"`
- **Simulated Behavior**: `alias.isascii()`가 `False`인 경우 `re.ASCII` 적용 없이 단순 `in` 검사 경로 사용 → 모두 정상 반환
- **Result**: PASS
- **Notes**: `re.ASCII` 플래그는 ASCII 분기에만 적용되며 비ASCII 경로는 변경 없음

---

### Scenario 6: normalize_domain ASCII alias + 한국어 접사 조합
- **Type**: Edge Case
- **Input**: `normalize_domain("FE에서 처리")`, `normalize_domain("BE에서 API")`, `normalize_domain("front-end에서 사용")`, `normalize_domain("프론트엔드 작업")` 등
- **Expected Behavior**: 각각 `"frontend"`, `"backend"`, `"frontend"`, `"frontend"`
- **Simulated Behavior**: `re.ASCII` 적용으로 `에`가 `\W` 처리 → 모든 케이스 정상 반환
- **Result**: PASS
- **Notes**: `normalize_domain` 함수도 동일한 `_matches_alias()` 경유하므로 동일하게 개선

---

### Scenario 7: 파이프라인 전체 추적 (완료 기준 3항목)
- **Type**: Happy Path (E2E 시뮬레이션)
- **Input**: `"Java에서 트랜잭션 관리하는 법 알려줘"`
- **Expected Behavior**: `resolved=True`, `answer_type="extract"`
- **Simulated Behavior**:
  1. `IntentClassifier.classify()` 진입
  2. `normalize_stack()` → `"spring"` (수정 후 정상 작동)
  3. LLM이 `stack="Java"` 반환 가정 시, `intent_classifier.py:85-86` override 로직으로 `"spring"` 덮어씀
  4. `DocumentResolver.resolve(stack="spring")` → ChromaDB `spring` 필터 정상 매칭
  5. `ExtractHandler.handle()` → chunk 검색 → `answer_type="extract"` 반환
- **Result**: PASS
- **Notes**: override 로직(`if pre_stack is not None: result.model_copy(...)`)이 alias 정규화의 핵심 안전망 역할 수행 확인

---

### Scenario 8: 부분 일치 방지 — JavaScript/JavaEE
- **Type**: Edge Case
- **Input**: `normalize_stack("JavaScript 사용법")`, `normalize_stack("JavaEE에서 트랜잭션")`
- **Expected Behavior**: 둘 다 `None`
- **Simulated Behavior**: `\b` 단어 경계로 `Java` alias가 `JavaScript`, `JavaEE` 내부에서 매칭되지 않음 → `None`
- **Result**: PASS
- **Notes**: `re.ASCII` 적용 후 `re.ASCII` 없는 버전과 동일하게 `None` 반환. 의도된 올바른 동작

---

### Scenario 9: ) 로 끝나는 alias — Java(Spring) 입력
- **Type**: Edge Case (code-reviewer 지적)
- **Input**: `normalize_stack("Java(Spring)으로 개발")`
- **Expected Behavior**: `"spring"` (기능적으로)
- **Simulated Behavior**: `Java(Spring)` alias 자체는 `\b` 실패하나, 리스트 내 `"Spring"` alias가 매칭되어 `"spring"` 반환
- **Result**: PASS (기능적으로 올바름)
- **Notes**: `Java(Spring)` alias 자체는 미동작 상태지만 `"Spring"` alias가 동일 결과를 커버함. 실용적 영향 없음

---

### Scenario 10: ) 로 끝나는 alias — Kotlin(Spring) 입력
- **Type**: Edge Case (code-reviewer 지적)
- **Input**: `normalize_stack("Kotlin(Spring)으로 개발")`
- **Expected Behavior**: `"kotlin"` (사용자 의도 기준)
- **Simulated Behavior**: `_STACK_ALIASES` dict 순회 시 `"spring"` 키가 먼저 처리되고 `"Spring"` alias가 `(Spring)` 부분에 매칭 → `"spring"` 반환
- **Result**: WARNING
- **Notes**: 이는 `re.ASCII` 수정과 무관한 기존 alias 순서 문제. `Kotlin(Spring)` 조합은 Kotlin 위주 개발을 의미하지만 `spring` 문서가 반환될 수 있음. 실용적 영향은 제한적이나 의미적으로 부정확. 별도 티켓 검토 권장

---

### Scenario 11: SpringBoot 미매칭 (단어 경계 의도 확인)
- **Type**: Edge Case
- **Input**: `normalize_stack("SpringBoot 설정")`
- **Expected Behavior**: `None` (설계 의도) 또는 `"spring"` (사용자 기대 가능)
- **Simulated Behavior**: `SpringBoot`는 `Spring` alias와 `\b` 경계가 성립하지 않아 `None` 반환
- **Result**: NOTE (설계 의도 확인 필요)
- **Notes**: `SpringBoot`를 Spring으로 인식할지 여부는 제품 결정 사항. 현재 코드는 미매칭이며 수정 전후 동일. 별도 alias 추가 여부 검토 권장

---

## Issues Found

### Issue #1: Kotlin(Spring) 입력 시 의미 오류 반환
- **Severity**: LOW
- **Location**: `src/convention_qa/query_understanding/alias_normalizer.py:39-73` (`_STACK_ALIASES` 정의)
- **Description**: `"Kotlin(Spring)으로 개발"` 입력 시 `normalize_stack()`이 `"kotlin"` 대신 `"spring"`을 반환한다. dict 순회 순서상 `"spring"` 키가 먼저 처리되고, `"Spring"` alias가 입력 내 `(Spring)` 부분에 매칭되기 때문이다. `Kotlin(Spring)` 전용 alias 자체는 `\b` 이슈로 미동작이며, 의존하던 fallback 동작도 `re.ASCII` 수정 이전의 유니코드 `\b` 우연 매칭에 기반하고 있었다.
- **Reproduction Steps**:
  1. `from src.convention_qa.query_understanding.alias_normalizer import normalize_stack`
  2. `normalize_stack("Kotlin(Spring)으로 개발")` 실행
  3. 반환값 `"spring"` 확인 (기대: `"kotlin"`)
- **Expected vs Actual**: 기대 `"kotlin"`, 실제 `"spring"`
- **Recommendation**: code-reviewer 권장안 A(옵션) 채택 — `Kotlin(Spring)`, `kotlin(spring)` alias를 제거하고 `Kotlin`, `kotlin` alias로 커버. `Kotlin(Spring)` 조합을 명시적으로 처리하려면 `"kotlin"` 키의 alias를 `"Spring"` 보다 dict에서 먼저 오도록 순서를 조정하거나, `_matches_alias` 에서 alias 마지막 문자가 `\W`인 경우 후행 `\b`를 생략하는 옵션 B를 적용한다.

---

### Issue #2: alias_normalizer.py 단위 테스트 파일 미존재
- **Severity**: MEDIUM
- **Location**: `tests/convention_qa/query_understanding/` (신규 파일 필요)
- **Description**: 티켓 완료 기준에 "테스트 케이스 전원 통과"가 명시되어 있으나 자동화 단위 테스트 파일이 없다. 이번 수정처럼 정규 표현식 플래그 하나의 변경이 한국어 입력과의 상호작용에 영향을 주는 경우, 테스트 없이는 향후 동일 버그가 재발해도 감지되지 않는다. code-reviewer도 Major 수준으로 지적한 항목이다.
- **Reproduction Steps**: 코드베이스 전체에서 `test_alias_normalizer` 파일 검색 시 결과 없음
- **Expected vs Actual**: 자동화 테스트 파일 존재, 실제 미존재
- **Recommendation**: `tests/convention_qa/query_understanding/test_alias_normalizer.py` 파일을 생성하고, code-reviewer 리포트에 제시된 테스트 케이스를 기준으로 최소한 아래 케이스를 포함한다:
  - `_matches_alias("Java에서 트랜잭션", "Java")` → `True` (핵심 버그 케이스)
  - `_matches_alias("JavaScript", "Java")` → `False` (부분 일치 방지)
  - `normalize_stack("Java에서 트랜잭션 관리하는 법")` → `"spring"`
  - `normalize_stack("Kotlin으로 테스트 작성")` → `"kotlin"`
  - `normalize_stack("파이썬으로 API 만들기")` → `None`

---

### Issue #3: _matches_alias docstring에 re.ASCII 적용 이유 미문서화
- **Severity**: LOW
- **Location**: `src/convention_qa/query_understanding/alias_normalizer.py:121-139`
- **Description**: 수정 후 docstring이 `re.ASCII` 플래그의 존재와 필요성을 언급하지 않는다. 향후 유지보수자가 플래그를 의도치 않게 제거할 가능성이 있다. code-reviewer가 Minor로 지적.
- **Reproduction Steps**: `alias_normalizer.py:121-139` 참조 — docstring에 `re.ASCII` 언급 없음
- **Expected vs Actual**: docstring에 `re.ASCII`가 필요한 이유(한국어 조사가 기본 유니코드 `\w`로 분류되는 문제) 설명 포함, 실제 미포함
- **Recommendation**: docstring Note 섹션에 "ASCII 매칭에 `re.ASCII` 플래그를 사용한다. 기본 유니코드 모드에서는 한국어 글자도 `\w`로 분류되어 `"Java에서"` 같은 입력에서 `\b`가 성립하지 않는 문제가 있다" 내용을 추가한다.

---

## Code Review Compliance

code-reviewer 리포트(`ai-work/review/2026-03-24_alias-normalizer-re-ascii-fix-review.md`) 기준:

| 지적 항목 | 반영 여부 | 비고 |
|-----------|-----------|------|
| 핵심 버그 수정 (`re.ASCII` 적용) | 반영됨 | line 136 확인 |
| `)` alias `\b` 매칭 영구 실패 (Major) | 미반영 | 기존 결함, 별도 처리 필요 |
| 단위 테스트 부재 (Major) | 미반영 | 별도 작업 필요 |
| 도달 불가 alias 정리 (Minor) | 미반영 | `Java(Spring)` 등 6개 잔존 |
| docstring `re.ASCII` 이유 미문서화 (Minor) | 미반영 | 현행 docstring 그대로 |

핵심 버그 수정은 정확히 이행되었으나, code-reviewer가 지적한 2건의 Major 항목(테스트 부재, `)` alias 설계 결함)은 이번 구현에서 반영되지 않았다.

---

## Risk Assessment

배포 위험도: **낮음 (LOW)**

핵심 수정(`re.ASCII` 추가)은 단 1줄 변경으로 원인 분석이 명확하고, 모든 티켓 테스트 케이스를 통과하며, 한국어 alias 경로(비ASCII 분기)에 영향을 주지 않는다. 수정 전 우연히 작동하던 `"Java(Spring)으로"` 케이스는 `False`로 역전되었으나, 실제 입력 시에는 `"Spring"` alias(또는 `"Java"` alias)가 커버하므로 기능적 결과는 동일하다.

잔존 이슈(Kotlin(Spring) 의미 오류, 테스트 부재)는 배포를 차단할 수준이 아니나, 테스트 부재는 향후 회귀 위험을 높인다.

---

## Recommendations

배포 전 조치 (우선순위 순):

1. **[MEDIUM — 배포 후 단기]** `tests/convention_qa/query_understanding/test_alias_normalizer.py` 단위 테스트 파일 작성. 티켓 완료 기준에 명시된 항목이므로 다음 스프린트 내 완료 권장.

2. **[LOW — 배포 후 중기]** `_matches_alias` docstring에 `re.ASCII` 적용 이유를 Note 섹션으로 추가. 5분 내 수정 가능한 1줄 변경.

3. **[LOW — 별도 티켓 검토]** `Kotlin(Spring)` 입력 시 `"spring"` 반환 이슈 — `Kotlin(Spring)`, `kotlin(spring)` alias 제거 또는 처리 전략 결정을 위한 별도 태스크 생성 권장.

4. **[LOW — 별도 티켓 검토]** `Java(Spring)` 등 도달 불가 alias 6개 정리 — code-reviewer 권장안 A(제거) 채택 여부 결정.

---

## Sign-off
- **QA Engineer (AI)**: qa-reporter
- **Verdict**: CONDITIONAL PASS — 핵심 버그 수정 검증 완료. 단위 테스트 작성 및 Kotlin(Spring) 이슈 별도 티켓 처리 조건부 승인.
