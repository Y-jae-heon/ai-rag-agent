# P3-BUG-08: SummarizeHandler answer_type "summarize" vs "summary" 불일치

우선순위: P3 (즉시 수정 권고)
심각도: HIGH
작성일: 2026-03-24
출처: QA Report — ai-work/qa/qa-report-P3-BUG-04-not-found-answer-type-2026-03-24.md Issue #1

## 현상

요약(summarize) 요청의 API 응답 `answer_type`이 항상 `"clarify"`로 silently 변환된다.
정상 요약 처리가 완료되었음에도 클라이언트는 "추가 정보 필요" 상태로 오인한다.

## 원인

`SummarizeHandler.handle()`이 `answer_type="summarize"`를 반환하지만,
`query.py`의 `valid_answer_types` 집합에는 `"summary"`만 존재한다.

```python
# src/convention_qa/action_routing/summarize_handler.py:59 (현재)
return HandlerResult(answer=..., answer_type="summarize", ...)

# src/api/routes/query.py:48 (현재)
valid_answer_types = {"fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"}
# "summarize" ∉ valid_answer_types → "clarify"로 silent 변환
```

P3-BUG-04(not_found silent 변환)와 동일한 패턴의 잔존 결함이다.

## 수정 방향

두 가지 선택지 중 하나를 선택하여 일관성 있게 수정:

**Option A — handler 반환값을 "summary"로 통일 (권고)**
- `summarize_handler.py:59`: `answer_type="summarize"` → `answer_type="summary"`
- 테스트 파일 `tests/test_summarize_handler.py`의 `"summarize"` 기댓값도 `"summary"`로 수정

**Option B — "summarize"를 허용 목록에 추가**
- `query.py` `valid_answer_types`에 `"summarize"` 추가
- `models.py` `QueryResponse.answer_type` Literal에 `"summarize"` 추가
- `"summary"`와 `"summarize"` 중복 의미 혼재 주의

## 수정 대상 파일

- `src/convention_qa/action_routing/summarize_handler.py:59`
- `src/api/routes/query.py:48` (Option B 선택 시)
- `src/api/models.py:50` (Option B 선택 시)
- `tests/test_summarize_handler.py` (Option A 선택 시)

## 수정 내역 (Option A 적용)

- `src/convention_qa/action_routing/summarize_handler.py:59`: `answer_type="summary"` (이미 수정 완료 상태)
- `tests/test_summarize_handler.py`: 기댓값 `"summarize"` → `"summary"` 4곳 수정

## 완료 기준

- [x] `SummarizeHandler` 반환 `answer_type`과 `valid_answer_types`가 일치
- [x] 정상 요약 요청 응답의 `answer_type`이 `"clarify"`로 변환되지 않음
- [x] 관련 테스트 통과 (6/6 passed)
