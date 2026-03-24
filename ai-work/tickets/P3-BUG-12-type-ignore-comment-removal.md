# P3-BUG-12: type: ignore[arg-type] 주석 제거

우선순위: P3
심각도: LOW
작성일: 2026-03-24
출처: QA Report — ai-work/qa/qa-report-P3-BUG-04-not-found-answer-type-2026-03-24.md Code Review Compliance
관련: Code Review — ai-work/review/2026-03-24_p3-bug04-not-found-answer-type-review.md

## 현상

`query.py`에 `# type: ignore[arg-type]` 주석이 잔존하고 있다.
이 주석은 타입 불일치를 mypy에서 억제하는 임시 방편으로, 실제 타입 오류를 숨길 수 있다.

## 원인

P3-BUG-04 수정 시 code reviewer의 주석 제거 권고가 미이행됨.

## 수정 대상

**파일**: `src/api/routes/query.py`

`# type: ignore[arg-type]` 주석을 제거하고, 타입 불일치의 근본 원인을 해결.
P3-BUG-10(ANSWER_TYPE_LITERAL)과 P3-BUG-11(HandlerResult Literal 구체화) 완료 시
타입이 자동으로 맞춰져 주석이 불필요해질 가능성이 높다.

## 완료 기준

- [ ] `query.py`의 `# type: ignore[arg-type]` 주석 제거
- [ ] mypy 타입 검사 통과 (또는 근본 원인 해결 확인)
- [ ] `pytest tests/` 전체 통과

## 참고

P3-BUG-10, P3-BUG-11 완료 후 함께 처리 권고.
