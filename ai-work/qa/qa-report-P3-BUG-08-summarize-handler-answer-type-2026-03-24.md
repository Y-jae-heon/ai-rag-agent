# QA Report: P3-BUG-08 SummarizeHandler answer_type "summarize" vs "summary" 불일치 수정

## Metadata
- **Date**: 2026-03-24
- **Scope**: SummarizeHandler.handle() answer_type 반환값 수정 (Option A 적용)
- **Implementation Status**: Complete
- **Code Review Status**: Complete
- **QA Status**: PASS

## Executive Summary

`SummarizeHandler.handle()`이 `answer_type="summarize"`를 반환하던 버그가 `"summary"`로 수정되었으며, `query.py`의 `valid_answer_types` 및 `models.py`의 Literal 정의와 완전히 일치함을 확인했다. 테스트 파일 내 기댓값 4곳도 `"summary"`로 올바르게 수정되었고, 전체 테스트 56개 모두 통과한다. 다른 핸들러에 동일한 패턴의 answer_type 불일치는 존재하지 않는다.

## Test Scenarios Executed

### Scenario 1: SummarizeHandler.handle() 반환 answer_type 값 직접 확인
- **Type**: Static Code Inspection
- **Input**: `summarize_handler.py` 59번 라인
- **Expected Behavior**: `answer_type="summary"` 반환
- **Simulated Behavior**: `return HandlerResult(answer=answer, answer_type="summary", ...)` — 수정 완료 확인
- **Result**: PASS
- **Notes**: Option A 기준으로 핸들러 반환값이 `"summary"`로 통일됨

### Scenario 2: valid_answer_types 집합에 "summary" 포함 여부 확인
- **Type**: Static Code Inspection
- **Input**: `query.py` 48번 라인 `valid_answer_types` 집합
- **Expected Behavior**: `"summary"` 포함, `"summarize"` 미포함
- **Simulated Behavior**: `valid_answer_types = {"fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"}` — `"summary"` 포함 확인
- **Result**: PASS
- **Notes**: `"summarize"` 는 해당 집합에 없으며, 수정 전 버그 재현 경로 차단 완료

### Scenario 3: models.py QueryResponse.answer_type Literal에 "summary" 포함 여부 확인
- **Type**: Static Code Inspection
- **Input**: `models.py` 50번 라인 `answer_type` Literal 정의
- **Expected Behavior**: `Literal[..., "summary", ...]` 포함
- **Simulated Behavior**: `answer_type: Literal["fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"]` — 포함 확인
- **Result**: PASS
- **Notes**: `valid_answer_types` 집합과 Literal 정의의 원소가 완전히 일치함 (7개 동일)

### Scenario 4: valid_answer_types vs models.py Literal 교차 검증
- **Type**: Static Code Inspection (Cross-check)
- **Input**: `query.py:48` 집합 vs `models.py:50` Literal
- **Expected Behavior**: 두 정의가 동일한 원소 집합을 가져야 함
- **Simulated Behavior**: 양쪽 모두 `{"fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"}` 7개로 완전 일치
- **Result**: PASS
- **Notes**: 이중 source-of-truth 구조는 여전히 잔존하나 (P3-BUG-10 참조), 현재 값은 일치하여 기능 오류 없음

### Scenario 5: 테스트 파일 기댓값 수정 확인 (4곳)
- **Type**: Static Code Inspection
- **Input**: `tests/test_summarize_handler.py` 전체
- **Expected Behavior**: `result.answer_type == "summary"` 기댓값이 4개 테스트에 존재
- **Simulated Behavior**: 51번, 108번, 122번, 154번 라인 — 모두 `assert result.answer_type == "summary"` 확인
- **Result**: PASS
- **Notes**: `"summarize"` 기댓값 잔존 없음

### Scenario 6: test_summarize_handler.py 단위 테스트 6개 실행
- **Type**: Automated Test Execution
- **Input**: `pytest tests/test_summarize_handler.py -v`
- **Expected Behavior**: 6/6 passed
- **Simulated Behavior**:
  - TestHandleWithSections::test_handle_with_sections PASSED
  - TestHandleWithSections::test_handle_sections_text_includes_heading_and_content PASSED
  - TestHandleEmptySections::test_handle_empty_sections PASSED
  - TestHandleEmptySections::test_handle_empty_sections_still_returns_summarize_type PASSED
  - TestHandleNoCanonicalDocId::test_handle_no_canonical_doc_id PASSED
  - TestHandleNoCanonicalDocId::test_handle_empty_canonical_doc_id_string PASSED
- **Result**: PASS
- **Notes**: 0.01s 완료

### Scenario 7: 전체 테스트 스위트 실행 (회귀 확인)
- **Type**: Automated Test Execution (Regression)
- **Input**: `pytest tests/ -v`
- **Expected Behavior**: 기존 테스트 전부 통과
- **Simulated Behavior**: 56 passed in 0.46s — alias_normalizer(12), compare_handler(16), discover_handler(13), extract_handler(9), summarize_handler(6) 전부 통과
- **Result**: PASS
- **Notes**: P3-BUG-08 수정이 다른 테스트에 회귀를 일으키지 않음

### Scenario 8: 다른 핸들러의 answer_type 불일치 잔존 여부 확인
- **Type**: Static Code Inspection (Pattern Scan)
- **Input**: `src/convention_qa/action_routing/` 하위 전체 핸들러 파일
- **Expected Behavior**: 모든 핸들러가 `valid_answer_types` 집합 내 값만 반환
- **Simulated Behavior**:
  - `extract_handler.py`: `"not_found"`, `"extract"` — 모두 집합 내 포함
  - `clarify_handler.py`: `"clarify"` — 포함
  - `discover_handler.py`: `"discover"`, `"clarify"` — 포함
  - `compare_handler.py`: `"not_found"`, `"compare"` — 포함
  - `fulltext_handler.py`: `"fulltext"` (4곳) — 포함
  - `summarize_handler.py`: `"summary"` — 포함 (수정 완료)
- **Result**: PASS
- **Notes**: 동일 패턴의 불일치가 다른 핸들러에 잔존하지 않음을 확인

## Issues Found

이슈 없음. 수정 사항이 요구사항에 맞게 적용되었으며 전체 테스트가 통과한다.

## Code Review Compliance

Option A 기준 수정 완료 기준 전항 충족:
- [x] `SummarizeHandler` 반환 `answer_type`이 `"summary"`로 수정됨 (`summarize_handler.py:59`)
- [x] `valid_answer_types` 집합과 일치하여 `"clarify"` fallback 발생 불가
- [x] `models.py` Literal과도 일치
- [x] 테스트 기댓값 4곳 모두 `"summary"`로 수정됨
- [x] 테스트 6/6 통과

## Risk Assessment

배포 리스크: **낮음**

- 수정 범위가 단일 파일 단일 라인 (`answer_type="summary"`)으로 국소적
- 테스트 수정은 코드 수정과 완전히 정합
- 회귀 없음 (전체 56개 테스트 통과)
- 다른 핸들러에 동일 패턴 잔존 없어 부분 수정 위험 없음

잔존 구조적 설계 이슈 (별도 티켓 P3-BUG-10):
- `valid_answer_types` 집합(query.py)과 `answer_type` Literal(models.py)이 이중 source-of-truth로 관리되고 있어 향후 타입 추가 시 한 쪽 누락 위험이 있음. 현재는 값이 일치하므로 기능 오류 없음.

## Recommendations

1. (배포 전 불필요) 현재 상태로 배포 가능
2. (중장기) P3-BUG-10에 따라 `valid_answer_types` 집합을 `models.py` Literal에서 자동 파생하도록 단일화하면 동일 패턴의 재발 구조적으로 차단 가능

## Sign-off
- **QA Engineer (AI)**: qa-reporter
- **Verdict**: APPROVED FOR DEPLOYMENT
