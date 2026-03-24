# P3-BUG-04: answer_type "not_found" silent 변환 — clarify 오분류

우선순위: P3
작성일: 2026-03-24
관련 분석: ai-work/plans/post-fix-debug-analysis.md §Bug 3

## 현상

`ExtractHandler`, `CompareHandler` 등이 `answer_type="not_found"`를 반환하지만,
API 응답에서 `answer_type="clarify"`로 silently 변환된다.

## 원인

`query.py`의 `_build_response()`에서 허용 목록에 없는 `answer_type`을 `"clarify"`로 치환한다.

```python
# src/api/routes/query.py:48-49 (현재)
valid_answer_types = {"fulltext", "summary", "extract", "discover", "clarify"}
answer_type = handler_result.answer_type if handler_result.answer_type in valid_answer_types else "clarify"
# "not_found" ∉ valid_answer_types → "clarify"로 치환
```

handler가 반환하는 `"not_found"`는 "문서를 찾지 못했다"는 명확한 상태이나,
`"clarify"`는 "추가 정보가 필요하다"는 다른 의미이므로 클라이언트 오해를 유발한다.

## 수정 대상

**파일**: `src/api/routes/query.py:48`

`valid_answer_types`에 `"not_found"` 추가:

```python
valid_answer_types = {"fulltext", "summary", "extract", "discover", "clarify", "not_found"}
```

아울러 `src/api/models.py`의 `QueryResponse.answer_type` Literal에도 `"not_found"` 추가 필요.

## 확인 대상 파일

- `src/api/routes/query.py:48`
- `src/api/models.py` — `QueryResponse.answer_type` Literal 정의 위치 확인 후 수정

## 테스트 케이스

| 시나리오                             | 기대 answer_type |
| ------------------------------------ | ---------------- |
| 존재하지 않는 문서 extract 요청      | `"not_found"`    |
| compare 요청 + document_queries 부족 | `"not_found"`    |

## 완료 기준

- [x] `query.py` `valid_answer_types`에 `"not_found"` 추가
- [x] `api/models.py` `QueryResponse.answer_type` Literal에 `"not_found"` 추가
- [x] 문서 미발견 시 응답 `answer_type`이 `"clarify"` 아닌 `"not_found"` 반환
