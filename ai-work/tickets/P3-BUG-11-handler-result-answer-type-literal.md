# P3-BUG-11: HandlerResult.answer_type str → Literal 구체화

우선순위: P3
심각도: LOW
작성일: 2026-03-24
출처: QA Report — ai-work/qa/qa-report-P3-BUG-04-not-found-answer-type-2026-03-24.md Issue #4
관련: Code Review — ai-work/review/2026-03-24_p3-bug04-not-found-answer-type-review.md

## 현상

`HandlerResult.answer_type`이 `str`로 선언되어 있어 Pydantic이 잘못된 값을 잡지 못한다.

```python
# src/convention_qa/action_routing/base_handler.py:49 (현재)
answer_type: str
```

`"summarize"` 등의 오타나 허용 목록 외 값이 handler에서 반환되어도
런타임까지 에러 없이 통과되어 `_build_response()`에서 silent fallback이 발생한다.

## 원인

handler 레이어에 타입 안전망이 없어 잘못된 answer_type이 조기에 감지되지 않음.

## 수정 대상

**파일**: `src/convention_qa/action_routing/base_handler.py:49`

P3-BUG-10(ANSWER_TYPE_LITERAL 공유 상수) 완료 후 적용:

```python
from src.api.models import ANSWER_TYPE_LITERAL

class HandlerResult(BaseModel):
    answer_type: ANSWER_TYPE_LITERAL
    ...
```

## 완료 기준

- [ ] `HandlerResult.answer_type` 타입이 `str`에서 구체적 Literal로 변경
- [ ] 허용 목록 외 answer_type 반환 시 Pydantic ValidationError 발생
- [ ] `pytest tests/` 전체 통과

## 참고

P3-BUG-10(ANSWER_TYPE_LITERAL 공유 상수 추출) 완료 후 진행 권고.
