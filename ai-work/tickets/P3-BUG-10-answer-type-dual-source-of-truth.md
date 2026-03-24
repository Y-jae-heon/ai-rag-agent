# P3-BUG-10: valid_answer_types / QueryResponse Literal 이중 관리 구조

우선순위: P3
심각도: LOW
작성일: 2026-03-24
출처: QA Report — ai-work/qa/qa-report-P3-BUG-04-not-found-answer-type-2026-03-24.md Issue #3
관련: Code Review — ai-work/review/2026-03-24_p3-bug04-not-found-answer-type-review.md

## 현상

허용 answer_type 목록이 두 곳에 각각 선언되어 있다.

```python
# src/api/routes/query.py:48
valid_answer_types = {"fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"}

# src/api/models.py:50
answer_type: Literal["fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"]
```

새 answer_type 추가 시 한쪽을 누락하면 P3-BUG-04, P3-BUG-08과 동일한 silent 변환 버그가 재발한다.

## 원인

단일 진실 공급원(single source of truth) 없이 동일 목록을 두 파일에 중복 선언.

## 수정 대상

**파일**: `src/api/models.py`, `src/api/routes/query.py`

`models.py`에 공유 상수 추출:

```python
# src/api/models.py
from typing import Literal, get_args

ANSWER_TYPE_LITERAL = Literal["fulltext", "summary", "extract", "discover", "clarify", "not_found", "compare"]
```

`query.py`에서 파생:

```python
# src/api/routes/query.py
from src.api.models import ANSWER_TYPE_LITERAL
valid_answer_types = set(get_args(ANSWER_TYPE_LITERAL))
```

## 완료 기준

- [ ] `models.py`에 `ANSWER_TYPE_LITERAL` 공유 상수 추출
- [ ] `query.py`의 `valid_answer_types`가 `ANSWER_TYPE_LITERAL`에서 파생
- [ ] `QueryResponse.answer_type` 타입 어노테이션이 `ANSWER_TYPE_LITERAL` 사용
- [ ] `pytest tests/` 전체 통과
- [ ] 두 파일의 허용 목록이 자동으로 동기화됨

## 참고

즉각 수정 불필요. 다음 answer_type 추가 작업 시 리팩토링에 포함할 것.
