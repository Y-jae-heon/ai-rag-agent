# QA Report: P2-BUG-03 — HandlerContext.understanding 주석 해제

## Metadata
- **Date**: 2026-03-24
- **Scope**: `src/convention_qa/action_routing/router.py` (understanding 필드 주석 해제), `src/convention_qa/action_routing/compare_handler.py`, `src/convention_qa/action_routing/base_handler.py`
- **Implementation Status**: Complete
- **Code Review Status**: Complete (9/10)
- **QA Status**: CONDITIONAL PASS

---

## Executive Summary

버그 수정(router.py line 136 주석 해제)은 정확히 적용되었으며, compare intent의 핵심 흐름이 복구되었음을 시뮬레이션과 테스트 16건 전체 통과로 확인하였다. discover, summarize, extract regression도 모두 이상 없다. 다만 `ActionRouter.route_and_execute()` 자체에 대한 직접 테스트가 존재하지 않아, 동일 버그가 재발하더라도 현재 테스트 스위트로는 탐지가 불가능하다는 구조적 공백이 있다. 또한 `compare_handler.py`에 production 환경에서 stdout을 오염시키는 디버그 `print()` 2건이 handle() 메서드 본문에 잔존하여 모든 compare 요청에서 실행된다.

---

## Test Scenarios Executed

### Scenario 1: 수정 핵심 — route_and_execute의 understanding 주입 검증
- **Type**: Happy Path
- **Input**: `understanding.intent="compare"`, `understanding.document_queries=["FE 네이밍", "BE 네이밍"]`, `resolution.resolved=True`
- **Expected Behavior**: `context.understanding`이 None이 아니고, `answer_type="compare"` 반환
- **Simulated Behavior**: `context.understanding is None: False`, `answer_type: compare`
- **Result**: PASS
- **Notes**: 버그 수정 전 `understanding=understanding` 줄이 주석 처리된 상태였다면 `context.understanding`이 None이 되어 `document_queries` 접근 불가 → not_found 반환이었을 것이나, 현재 코드에서는 정상 주입됨

### Scenario 2: compare intent 정상 동작 — answer_type != not_found 확인
- **Type**: Happy Path
- **Input**: `"FE vs BE 네이밍 차이점 알려줘"`, `_resolve`, `_get_sections`, `_compare` mock
- **Expected Behavior**: `answer_type="compare"`, sources에 두 문서 포함
- **Simulated Behavior**: `answer_type: compare`, sources: `[{path: "docs/fe-naming.md", ...}, {path: "docs/be-naming.md", ...}]`
- **Result**: PASS

### Scenario 3: discover intent regression
- **Type**: Regression
- **Input**: `intent="discover"`, `resolution.resolved=True`
- **Expected Behavior**: `answer_type="discover"`, not_found 아님
- **Simulated Behavior**: `answer_type: discover`
- **Result**: PASS

### Scenario 4: summarize intent regression
- **Type**: Regression
- **Input**: `intent="summarize"`, `resolution.resolved=True`
- **Expected Behavior**: `answer_type="summarize"`
- **Simulated Behavior**: `answer_type: summarize`
- **Result**: PASS

### Scenario 5: extract intent regression
- **Type**: Regression
- **Input**: `intent="extract"`, `resolution.resolved=True`, MMR 청크 1건 반환
- **Expected Behavior**: `answer_type="extract"`
- **Simulated Behavior**: `answer_type: extract`
- **Result**: PASS

### Scenario 6: 엣지 케이스 — understanding=None (default)
- **Type**: Edge Case
- **Input**: `HandlerContext` 생성 시 `understanding` 미전달 (기본값 None)
- **Expected Behavior**: `CompareHandler.handle()` 에서 graceful fallback → `answer_type="not_found"`
- **Simulated Behavior**: `answer_type: not_found`
- **Result**: PASS
- **Notes**: `CompareHandler.handle()` line 32의 `getattr(...) if understanding else None` 조건이 None 방어를 정상 처리함

### Scenario 7: 엣지 케이스 — document_queries 1개 (len < 2)
- **Type**: Edge Case
- **Input**: `understanding.document_queries=["FE 네이밍"]`
- **Expected Behavior**: `answer_type="not_found"`
- **Simulated Behavior**: `answer_type: not_found`
- **Result**: PASS

### Scenario 8: 엣지 케이스 — document_queries 빈 리스트
- **Type**: Edge Case
- **Input**: `understanding.document_queries=[]`
- **Expected Behavior**: `answer_type="not_found"`
- **Simulated Behavior**: `answer_type: not_found`
- **Result**: PASS

### Scenario 9: 엣지 케이스 — resolved=False인 compare intent
- **Type**: Edge Case
- **Input**: `intent="compare"`, `resolution.resolved=False`
- **Expected Behavior**: CompareHandler가 선택되고, 두 resolution 모두 None이어도 query 문자열로 fallback하여 `answer_type="compare"` 반환
- **Simulated Behavior**: handler type: CompareHandler, `answer_type: compare`
- **Result**: PASS
- **Notes**: router.py line 68에서 `compare`는 `resolved=False`여도 ClarifyHandler로 빠지지 않도록 예외 처리되어 있음

### Scenario 10: 단위 테스트 스위트 — tests/test_compare_handler.py
- **Type**: Unit Test Execution
- **Input**: 16개 테스트 케이스 (pytest 실행)
- **Expected Behavior**: 전체 통과
- **Simulated Behavior**: `16 passed in 0.04s`
- **Result**: PASS

---

## Issues Found

### Issue #1: ActionRouter.route_and_execute()에 대한 직접 테스트 부재
- **Severity**: 🟠 HIGH
- **Location**: `tests/test_compare_handler.py` (부재), `src/convention_qa/action_routing/router.py:132-138`
- **Description**: 이번 버그(P2-BUG-03)의 실제 수정 지점은 `router.py` line 136의 `understanding=understanding` 주석 해제이다. 그러나 현재 테스트 스위트에는 `ActionRouter`가 import되거나 `route_and_execute()`를 호출하는 테스트가 단 한 건도 없다. `test_compare_handler.py`의 `make_context()` helper는 `HandlerContext`를 직접 생성하므로 router를 경유하지 않는다. 따라서 누군가 `understanding=understanding` 줄을 다시 주석 처리해도 현재 테스트 스위트는 이를 탐지할 수 없다.
- **Reproduction Steps**:
  1. `router.py` line 136에서 `understanding=understanding`을 다시 주석 처리
  2. `python3 -m pytest tests/test_compare_handler.py -v` 실행
  3. 16 passed — 버그가 있음에도 모든 테스트 통과
- **Expected vs Actual**: compare intent 실패를 탐지하는 router 레벨 테스트가 있어야 하나, 없음
- **Recommendation**: `tests/convention_qa/action_routing/test_router.py` 또는 기존 테스트에 `ActionRouter.route_and_execute()` 호출 테스트 추가. 최소한 다음 시나리오 커버 필요:
  - `compare` intent에서 `result.answer_type != "not_found"` 확인
  - `context.understanding`이 None이 아님을 직접 assert

### Issue #2: compare_handler.py handle() 본문 내 디버그 print() 잔존
- **Severity**: 🟡 MEDIUM
- **Location**: `src/convention_qa/action_routing/compare_handler.py:43-44`
- **Description**: `handle()` 메서드 본문(line 43-44)에 `print(f"resolution_a = {resolution_a}")`, `print(f"resolution_b = {resolution_b}")` 가 있다. 이 두 줄은 ChromaDB 내부의 print들(line 112, 124)과 달리 `_get_sections()` 내부가 아닌 `handle()` 최상위에 위치하여 **compare 요청이 올 때마다 반드시 실행된다.** production stdout에 MagicMock/객체 repr 또는 내부 resolution 객체 정보가 노출된다.
- **Reproduction Steps**: compare intent 요청 1건 전송 시 stdout에 resolution 객체 repr 출력 확인
- **Expected vs Actual**: 디버그 출력 없어야 함 / 매 요청마다 `resolution_a = ...`, `resolution_b = ...` 출력됨
- **Recommendation**: line 43-44 삭제. 코드 리뷰에서 "기존 부채, 이번 수정과 무관"으로 분류되었으나, 이 두 줄은 P2-BUG-03 수정 이후 새로 추가된 것으로 보이며(버그 수정 시 디버그 목적으로 삽입 추정) 다른 핸들러에는 동일 패턴이 없다.

### Issue #3: compare_handler.py handle() 내 불필요한 빈 줄 (코드 스타일)
- **Severity**: 🟢 LOW
- **Location**: `src/convention_qa/action_routing/compare_handler.py:66-67`
- **Description**: `_compare()` 호출 결과 할당 이후(line 65) `format_compare()` 호출(line 68) 사이에 빈 줄이 2개 연속 존재한다. PEP 8 기준으로 함수 내부 빈 줄은 1개가 최대이다.
- **Expected vs Actual**: 빈 줄 1개 / 빈 줄 2개
- **Recommendation**: line 66의 빈 줄 1개 삭제

---

## Code Review Compliance

코드 리뷰에서 제기된 주요 사항:
- `HandlerContext.understanding` 타입이 `Any`인 점: 코드 리뷰가 개선 제안으로 남겨둔 사항이며, QA 시뮬레이션에서 `arbitrary_types_allowed=True` 설정과 `default=None` 조합이 의도대로 동작함을 확인. 기능 장애 없음.
- 디버그 `print()` 잔존 (기존 부채): 코드 리뷰는 "이번 수정과 무관한 기존 부채"로 분류했으나, `handle()` 본문의 line 43-44는 다른 handler에 없는 패턴으로 이번 수정 중 추가된 것으로 추정된다. Issue #2로 상향 분류하였다.
- 테스트 16 passed 확인: QA에서도 동일 결과 재현됨.

---

## Risk Assessment

- **버그 수정 자체**: 위험도 낮음. 단순 주석 해제이며 로직 변경 없고, 전후 시뮬레이션 모두 정상.
- **Regression 위험**: 낮음. discover/summarize/extract intent는 `understanding` 필드를 사용하지 않아 영향 없음.
- **재발 위험**: 중간. router.py의 context 생성 코드에 대한 직접 테스트가 없어 동일 버그가 다시 주석 처리되어도 테스트가 탐지 못함.
- **Production stdout 오염**: 낮음-중간. line 43-44의 print가 운영 로그를 오염시킬 수 있으나, 기능 장애를 유발하지는 않음.

---

## Recommendations

우선순위 순:

1. **[HIGH] router 레벨 테스트 추가**: `ActionRouter.route_and_execute()`에서 compare intent가 `answer_type != "not_found"`를 반환하고 `context.understanding`이 None이 아님을 검증하는 테스트를 추가해야 이번 버그의 재발을 테스트로 잡을 수 있다. 현재 구조는 버그가 재발해도 테스트가 통과한다.

2. **[MEDIUM] handle() 내 print() 2건 삭제**: `compare_handler.py` line 43-44의 `print(f"resolution_a = ...")`, `print(f"resolution_b = ...")` 삭제. 이 두 줄은 모든 compare 요청에서 실행된다.

3. **[LOW] 불필요한 빈 줄 제거**: `compare_handler.py` line 66-67의 연속 빈 줄 1개 제거.

---

## Sign-off
- **QA Engineer (AI)**: qa-reporter
- **Verdict**: CONDITIONAL PASS — 버그 수정은 정확하고 regression 없음. router 레벨 테스트 추가(Issue #1) 전까지 동일 버그 재발 탐지 불가. handle() 내 디버그 print 제거(Issue #2) 권고.
