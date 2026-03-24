# QA Report: P3-BUG-04 — answer_type "not_found" silent 변환 → clarify 오분류

## Metadata
- **Date**: 2026-03-24
- **Scope**: `src/api/routes/query.py:48`, `src/api/models.py:50`, `_build_response()` 함수 전체 경로, handler 반환값 전수 조사
- **Implementation Status**: Complete
- **Code Review Status**: Complete (2026-03-24, ai-work/review/2026-03-24_p3-bug04-not-found-answer-type-review.md)
- **QA Status**: CONDITIONAL PASS

## Executive Summary

P3-BUG-04의 핵심 수정(valid_answer_types에 "not_found"와 "compare" 추가, models.py Literal 동기화)은 정확하게 구현되었고 `_build_response()` 시뮬레이션 6개 케이스 전원 통과했다. 그러나 QA 시뮬레이션 중 기존부터 존재하던 별도 버그를 발견했다: `SummarizeHandler`가 반환하는 `"summarize"` answer_type이 `valid_answer_types`에 없는 `"summary"`와 불일치하여 현재도 `"clarify"`로 silent 변환된다. 이 버그는 P3-BUG-04 수정 범위 외부이지만 동일한 silent 변환 패턴의 잔존 사례이다. 테스트 56개 전원 통과.

## Test Scenarios Executed

### Scenario 1: ExtractHandler — 청크 없음 → not_found (핵심 수정 검증)
- **Type**: Happy Path (버그 수정 직접 검증)
- **Input**: `HandlerResult(answer="찾을 수 없습니다.", answer_type="not_found", sources=[])`
- **Expected Behavior**: `_build_response()` 반환 `answer_type="not_found"`
- **Simulated Behavior**: `answer_type="not_found"` 반환 확인. 수정 전 코드(`valid_before` 집합)로 동일 입력 시 `"clarify"` 반환 확인.
- **Result**: PASS
- **Notes**: 버그 수정 전/후 동작을 나란히 시뮬레이션하여 회귀 없음 검증 완료.

### Scenario 2: CompareHandler — document_queries 부족 → not_found
- **Type**: Edge Case
- **Input**: `HandlerResult(answer="찾을 수 없습니다.", answer_type="not_found", sources=[])`, intent="compare"
- **Expected Behavior**: `answer_type="not_found"` 반환
- **Simulated Behavior**: `answer_type="not_found"` 반환 확인
- **Result**: PASS

### Scenario 3: CompareHandler — 정상 비교 → compare (코드 리뷰 지적 반영 검증)
- **Type**: Happy Path
- **Input**: `HandlerResult(answer="비교 결과", answer_type="compare", sources=[...])`
- **Expected Behavior**: `answer_type="compare"` 반환
- **Simulated Behavior**: `answer_type="compare"` 반환 확인. 수정 전 코드에서는 `"clarify"`로 변환됨을 시뮬레이션으로 재현.
- **Result**: PASS
- **Notes**: code reviewer가 지적한 "compare도 허용 목록에 없었음" 문제가 이번 수정에서 함께 해결되었음을 확인.

### Scenario 4: 알 수 없는 answer_type → clarify fallback
- **Type**: Error Case
- **Input**: `HandlerResult(answer="?", answer_type="invalid_type", sources=[])`
- **Expected Behavior**: `answer_type="clarify"` fallback 반환
- **Simulated Behavior**: `answer_type="clarify"` 반환 확인
- **Result**: PASS
- **Notes**: fallback 로직이 의도대로 작동함.

### Scenario 5: resolved_document 포함 경로 (추출 성공 케이스)
- **Type**: Happy Path
- **Input**: `HandlerResult(answer_type="extract", resolved_document={canonical_doc_id, title, path})`
- **Expected Behavior**: `ResolvedDocumentInfo` 인스턴스로 변환, `answer_type="extract"`
- **Simulated Behavior**: 정상 변환 확인, `resolved_document.canonical_doc_id == "test_id"`
- **Result**: PASS

### Scenario 6: resolved_document=None 경로
- **Type**: Edge Case
- **Input**: `HandlerResult(answer_type="not_found", resolved_document=None)`
- **Expected Behavior**: `resolved_document=None` 유지, `answer_type="not_found"`
- **Simulated Behavior**: 정상 확인
- **Result**: PASS

### Scenario 7: models.py Literal와 query.py set 동기화 검증
- **Type**: Integration
- **Input**: `get_args(Literal["fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"])` vs `valid_answer_types` set
- **Expected Behavior**: 두 집합이 완전히 일치
- **Simulated Behavior**: 두 집합 완전 일치 확인. 어느 한쪽에만 있는 값 없음.
- **Result**: PASS

### Scenario 8: 모든 handler answer_type 반환값 전수 조사
- **Type**: Integration / Environment Simulation
- **Input**: handler 소스 파일 전체 정적 분석
- **Expected Behavior**: 모든 handler의 실제 반환값이 valid_answer_types에 포함
- **Simulated Behavior**: `SummarizeHandler`가 `"summarize"` 반환하나 valid_answer_types에는 `"summary"`만 존재 → silent 변환 발생
- **Result**: WARNING
- **Notes**: 이 버그는 P3-BUG-04 수정 범위 밖의 기존 결함이나 동일 패턴이므로 별도 이슈로 문서화.

### Scenario 9: pytest 전체 테스트 스위트 실행
- **Type**: Regression
- **Input**: `pytest tests/ -v --tb=short`
- **Expected Behavior**: 56개 전원 통과, 회귀 없음
- **Simulated Behavior**: 56 passed in 0.40s. 회귀 없음.
- **Result**: PASS

## Issues Found

### Issue #1: SummarizeHandler의 answer_type "summarize" — valid_answer_types 불일치 (기존 결함)
- **Severity**: 🟠 HIGH
- **Location**: `src/convention_qa/action_routing/summarize_handler.py:59`
- **Description**: `SummarizeHandler.handle()`은 `answer_type="summarize"`를 반환하지만, `query.py`의 `valid_answer_types` 집합에는 `"summary"`만 존재한다. 결과적으로 모든 정상 요약 요청의 응답이 `"summarize"` 대신 `"clarify"`로 silently 변환된다. P3-BUG-04에서 수정된 `"not_found"` 버그와 동일한 패턴의 잔존 결함이다.
- **Reproduction Steps**:
  1. summarize intent 처리 파이프라인 실행
  2. `SummarizeHandler.handle()` 반환값: `answer_type="summarize"`
  3. `_build_response()` 진입 시 `"summarize" not in {"fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"}`
  4. 결과: `answer_type="clarify"` 반환
- **Expected vs Actual**:
  - Expected: `answer_type="summarize"` (또는 의도된 값 `"summary"`)
  - Actual: `answer_type="clarify"` (silent 변환)
- **Recommendation**: `SummarizeHandler`의 반환값을 `"summary"`로 통일하거나, `valid_answer_types`와 Literal에 `"summarize"`를 추가해야 한다. handler 반환값과 허용 목록의 정규화 필요. 현재 테스트(`test_summarize_handler.py`)는 `"summarize"` 기준으로 작성되어 있으므로 handler 반환값을 수정할 경우 테스트도 함께 수정해야 한다.

### Issue #2: _build_response() 직접 단위 테스트 부재 (code reviewer 지적 미반영)
- **Severity**: 🟡 MEDIUM
- **Location**: `src/api/routes/query.py:25-57` / `tests/` (신규 파일 미존재)
- **Description**: 이번 버그 발생 지점인 `_build_response()` 함수에 대한 직접 단위 테스트가 없다. code reviewer가 `tests/test_query_route.py` 신규 작성을 권고했으나 미반영 상태다. 동일 패턴 회귀(새로운 answer_type이 valid_answer_types에 누락되는 경우) 발생 시 자동 감지 불가능.
- **Reproduction Steps**: `tests/` 디렉터리에 `test_query_route.py` 파일 없음 확인.
- **Expected vs Actual**:
  - Expected: `_build_response(HandlerResult(answer_type="not_found"), intent="extract")` → `answer_type="not_found"` 검증하는 테스트 존재
  - Actual: 해당 테스트 없음
- **Recommendation**: code reviewer 제안대로 `tests/test_query_route.py` 신규 작성. 최소한 다음 두 케이스 포함: (1) valid answer_type이 그대로 통과하는지, (2) invalid answer_type이 `"clarify"`로 fallback되는지.

### Issue #3: valid_answer_types와 QueryResponse.answer_type Literal 이중 관리 (code reviewer 지적 미반영)
- **Severity**: 🟢 LOW
- **Location**: `src/api/routes/query.py:48`, `src/api/models.py:50`
- **Description**: 허용 answer_type 목록이 `query.py`의 `set`과 `models.py`의 `Literal` 두 곳에 중복 정의되어 있다. 이번 수정은 두 곳 모두 올바르게 업데이트했으나, `SummarizeHandler` 불일치 버그(Issue #1)처럼 새 값 추가 시 한쪽을 누락하면 즉시 재발하는 구조적 취약점이다. code reviewer가 `ANSWER_TYPE_LITERAL` 공유 상수 추출을 권고했으나 미반영 상태.
- **Reproduction Steps**: 두 파일을 비교하면 현재는 일치하지만 단일 진실 공급원이 없어 다음 수정 시 동기화 실패 위험 존재.
- **Expected vs Actual**:
  - Expected: `models.py`에 단일 `ANSWER_TYPE_LITERAL` 상수, `query.py`에서 `set(get_args(ANSWER_TYPE_LITERAL))`로 파생
  - Actual: 두 곳에 각각 선언
- **Recommendation**: 즉각 수정 불필요하나 다음 answer_type 추가 작업 시 리팩토링 포함할 것.

### Issue #4: HandlerResult.answer_type 타입 안전망 없음 (code reviewer 지적, 범위 외)
- **Severity**: 🟢 LOW
- **Location**: `src/convention_qa/action_routing/base_handler.py:49`
- **Description**: `HandlerResult.answer_type`이 `str`로 선언되어 Pydantic이 잘못된 값을 잡지 못한다. `"summarize"` 등의 오타나 잘못된 값이 handler에서 반환되어도 런타임까지 에러 없이 진행된다.
- **Recommendation**: 향후 `AnswerType = Literal[...]` 공유 상수 확정 후 `base_handler.py`의 `answer_type` 필드 타입을 구체화.

## Code Review Compliance

code reviewer 지적사항과의 이행 상태:

| 지적사항 | 심각도 | 이행 여부 |
|---------|--------|----------|
| "compare" answer_type이 valid_answer_types 및 Literal에 누락 | 🟠 Major | 이행 완료 — 수정 파일에 "compare" 포함 확인 |
| valid_answer_types와 Literal 이중 관리 구조 | 🟡 Minor | 미이행 — 이중 관리 구조 잔존 |
| _build_response() 직접 단위 테스트 부재 | 🟡 Minor | 미이행 — tests/test_query_route.py 미작성 |
| HandlerResult.answer_type str→Literal 구체화 | 🟢 Suggestion | 미이행 — str 타입 유지 |
| type: ignore[arg-type] 주석 제거 | 🟢 Suggestion | 미이행 — 주석 잔존 |

코드 리뷰의 Major 지적사항("compare" 누락)은 완료 기준에 포함되어 이미 반영되었다. Minor 및 Suggestion 항목은 미반영 상태이며, 이 중 _build_response() 단위 테스트 부재는 기존 버그 재발 방지 관점에서 MEDIUM 수준의 위험이다.

## Risk Assessment

- 이번 수정의 핵심 범위(not_found, compare 허용 목록 추가)는 정확하게 구현되었고 회귀 위험 없음.
- `SummarizeHandler`의 `"summarize"` vs `"summary"` 불일치(Issue #1)는 이번 수정과 무관하게 기존부터 존재하던 버그로, 현재 요약 API 응답이 항상 `"clarify"`로 반환되는 상태다. 별도 수정 필요.
- `_build_response()` 직접 단위 테스트 부재(Issue #2)는 동일 패턴 회귀 발생 시 자동 감지를 불가능하게 하는 구조적 취약점이다.
- 전반적으로 배포는 가능하나 Issue #1 해결 후 배포를 권고한다.

## Recommendations

1. **[즉시 수정 권고]** `SummarizeHandler.answer_type` 반환값을 `"summary"`로 수정하거나, `valid_answer_types`와 `models.py Literal`에 `"summarize"` 추가. 단, 테스트 파일도 함께 수정해야 함. (Issue #1)
2. **[다음 PR에 포함]** `tests/test_query_route.py` 신규 작성 — `_build_response()`의 not_found, compare, unknown fallback 케이스 최소 3개 포함. (Issue #2)
3. **[리팩토링 시]** `ANSWER_TYPE_LITERAL` 공유 상수 추출로 이중 관리 구조 제거. (Issue #3)

## Sign-off
- **QA Engineer (AI)**: qa-reporter
- **Verdict**: CONDITIONAL PASS — Issue #1 (SummarizeHandler "summarize" vs "summary" 불일치) 수정 후 APPROVED FOR DEPLOYMENT
