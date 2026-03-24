# P0-BUG-01: DocumentResolutionResult.resolution_strategy Literal 누락

우선순위: P0
작성일: 2026-03-24
관련 분석: ai-work/plans/post-fix-debug-analysis.md §Bug 2

## 현상

`keyword_tiebreak` 성공 후 `DocumentResolutionResult` 생성 시 Pydantic ValidationError 발생 → HTTP 500 반환.

```
1 validation error for DocumentResolutionResult
resolution_strategy
  Input should be 'exact', 'alias', 'semantic' or 'unresolved'
  [type=literal_error, input_value='keyword_tiebreak', input_type=str]
```

## 원인

`resolver.py`에서 tiebreak 성공 시 `resolution_strategy="keyword_tiebreak"`를 반환하지만,
`models.py`의 Literal 타입 정의에 해당 값이 없다.

```python
# src/convention_qa/document_resolution/models.py:23 (현재)
resolution_strategy: Literal["exact", "alias", "semantic", "unresolved"]
#                                       ↑ "keyword_tiebreak" 미포함
```

## 수정 대상

**파일**: `src/convention_qa/document_resolution/models.py:23`

```python
# 수정 후
resolution_strategy: Literal["exact", "alias", "semantic", "keyword_tiebreak", "unresolved"]
```

## 테스트 케이스

| 입력 | 기대 결과 |
|------|-----------|
| `"FSD 구조 규칙 알려줘"` | HTTP 200, `resolved=True`, `resolution_strategy="keyword_tiebreak"` |

## 완료 기준

- [x] `models.py` Literal에 `"keyword_tiebreak"` 추가
- [x] `"FSD 구조 규칙 알려줘"` 요청 시 HTTP 500 → HTTP 200 전환
- [x] 기존 `exact`, `alias`, `semantic`, `unresolved` 케이스 회귀 없음 (44 passed)
