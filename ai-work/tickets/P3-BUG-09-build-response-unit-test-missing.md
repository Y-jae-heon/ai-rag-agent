# P3-BUG-09: _build_response() 직접 단위 테스트 부재

우선순위: P3
심각도: MEDIUM
작성일: 2026-03-24
출처: QA Report — ai-work/qa/qa-report-P3-BUG-04-not-found-answer-type-2026-03-24.md Issue #2
관련: Code Review — ai-work/review/2026-03-24_p3-bug04-not-found-answer-type-review.md

## 현상

P3-BUG-04의 버그 발생 지점인 `_build_response()` 함수에 대한 직접 단위 테스트가 없다.
동일 패턴 회귀(새 answer_type이 valid_answer_types에 누락)가 발생해도 자동 감지 불가능하다.

## 원인

`tests/test_query_route.py` 파일이 존재하지 않는다.
code reviewer가 신규 작성을 권고했으나 미이행 상태.

## 수정 대상

**신규 파일**: `tests/test_query_route.py`

최소 포함 케이스:

| 테스트 케이스 | 입력 | 기대 결과 |
|-------------|------|---------|
| valid answer_type 통과 | `answer_type="not_found"` | `answer_type="not_found"` |
| valid answer_type 통과 | `answer_type="compare"` | `answer_type="compare"` |
| invalid answer_type fallback | `answer_type="unknown_type"` | `answer_type="clarify"` |
| summarize 정상 통과 | `answer_type="summary"` | `answer_type="summary"` |

## 완료 기준

- [ ] `tests/test_query_route.py` 신규 작성
- [ ] `_build_response()` valid answer_type 통과 케이스 최소 3개 포함
- [ ] `_build_response()` invalid → clarify fallback 케이스 포함
- [ ] `pytest tests/` 전체 통과
