# P2-BUG-03: HandlerContext.understanding 주석 처리 — compare 기능 전체 불능

우선순위: P2
작성일: 2026-03-24
관련 분석: ai-work/plans/post-fix-debug-analysis.md §Bug 4

## 현상

compare intent 요청 시 `document_queries`를 읽지 못해 항상 `not_found` 반환.

## 원인

`router.py`에서 `HandlerContext` 생성 시 `understanding` 필드가 주석 처리되어 있다.

```python
# src/convention_qa/action_routing/router.py:132-137 (현재)
context = HandlerContext(
    question=question,
    intent=understanding.intent,
    resolution=resolution,
    # understanding=understanding,  ← 주석 처리됨
)
```

`CompareHandler.handle()`에서:
```python
understanding = context.understanding  # None
document_queries = getattr(understanding, "document_queries", None) if understanding else None
# → 항상 None → not_found fallback
```

## 수정 대상

**파일**: `src/convention_qa/action_routing/router.py:136`

주석 해제:
```python
context = HandlerContext(
    question=question,
    intent=understanding.intent,
    resolution=resolution,
    understanding=understanding,
)
```

## 테스트 케이스

| 입력 | 기대 결과 |
|------|-----------|
| `"FE vs BE 네이밍 차이점 알려줘"` | `intent="compare"`, `answer_type` != `"not_found"` |

## 완료 기준

- [x] `router.py:136` `understanding=understanding` 주석 해제
- [x] compare intent 요청 시 `context.understanding`이 `None`이 아님 확인
- [x] `CompareHandler`가 `document_queries`를 정상적으로 참조
