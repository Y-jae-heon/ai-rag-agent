# RAG 검색 개선 작업 보고서

> 작업일: 2026-03-24
> 계획 출처: `ai-work/plans/rag-search-improvement.md`

---

## 작업 요약

피드백 보고서에서 발견된 두 가지 실패 시나리오(Scenario A, B)를 해결하기 위한 3가지 Fix를 완료하였다.

---

## 적용된 변경 사항

### Fix 3 — Stack 정규화 보강 로직 수정

**파일**: `src/convention_qa/query_understanding/intent_classifier.py`

**변경 내용**:

`alias_normalizer`로 사전 추출된 `domain`/`stack` 값이 있을 때, LLM 반환값과 무관하게 항상 정규화된 값으로 override하도록 조건 수정.

```python
# 변경 전 (결함 있는 조건)
if pre_domain is not None and result.domain is None:
if pre_stack is not None and result.stack is None:

# 변경 후 (항상 override)
if pre_domain is not None:
if pre_stack is not None:
```

**효과**: LLM이 비정규화 값(예: `"Java"`)을 반환해도 alias_normalizer의 정규화 값(`"spring"`)으로 덮어써서 ChromaDB 필터 매칭 정확도 복원. `query.py`의 `domain`/`stack` 주석을 해제하는 Fix 1과 함께 동작한다.

---

### Fix 1 — Topic-based Semantic Fallback

**파일**: `src/convention_qa/document_resolution/resolver.py`, `src/api/routes/query.py`

**변경 내용**:

`resolver.resolve()` 시그니처에 `topic`, `raw_question` 파라미터 추가. `document_query=None`인 경우 즉시 `unresolved` 반환 대신, `topic → raw_question` 순으로 fallback 시맨틱 검색을 실행한다.

`query.py`에서 주석 처리된 `domain`, `stack`을 해제하고 `topic`, `raw_question`을 resolver에 전달한다.

**효과**: `"Java에서 트랜잭션 관리하는 법 알려줘"` 유형의 질문에서 `document_query=None` → `topic="트랜잭션 관리"`, `stack="spring"`으로 시맨틱 검색 진입. `resolution_strategy='unresolved'`로 끝나던 흐름이 정상 답변으로 전환.

---

### Fix 2 — Title Keyword Tiebreaker

**파일**: `src/convention_qa/document_resolution/resolver.py`

**변경 내용**:

`_evaluate_candidates()`에 `query` 파라미터 추가. score_gap < 0.15인 복수 후보 상황에서 `_keyword_tiebreak()` private 함수를 호출한다.

`_keyword_tiebreak()` 로직:
- ASCII 토큰 `len >= 2`, 한국어 토큰 `len >= 3`만 판별 토큰으로 사용 (범용 2글자 한국어 제외)
- 판별 토큰이 타이틀에 포함된 후보가 정확히 1개일 때만 `resolved=True`

**효과**: `"FSD 구조 규칙 알려줘"` 유형에서 `specific_tokens=["FSD"]`로 `"FSD 레이어드 아키텍처 개요"` 단독 선택 → `resolution_strategy='keyword_tiebreak'`으로 정상 답변. 추가 LLM 호출 없이 동작.

---

## 변경 파일 목록

| 파일 | 변경 내용 |
| ---- | --------- |
| `src/convention_qa/query_understanding/intent_classifier.py` | domain/stack 보강 조건 수정 — 항상 alias_normalizer 값으로 override |
| `src/convention_qa/document_resolution/resolver.py` | `resolve()` 시그니처 확장 (topic, raw_question), topic fallback 로직, `_evaluate_candidates()` query 파라미터 추가, `_keyword_tiebreak()` 함수 추가 |
| `src/api/routes/query.py` | domain/stack 주석 해제, topic/raw_question resolver에 전달 |

---

## 검증 방법

서버 실행:

```bash
uvicorn src.api.main:app --reload
```

**Scenario A 검증** (`document_query=None` → topic fallback):

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Java에서 트랜잭션 관리하는 법 알려줘"}'
```

기대값:
- `resolution_strategy` ≠ `"unresolved"`
- `answer_type` = `"extract"` (not_found 아님)
- 로그: `RESOLVE STEP 1 :: None` → fallback 진입 확인

**Scenario B 검증** (keyword tiebreaker):

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "FSD 구조 규칙 알려줘"}'
```

기대값:
- `resolved_document.title`에 FSD 관련 문서 포함
- `resolution_strategy` = `"keyword_tiebreak"`
- `answer_type` = `"extract"`

---

## 미결 사항

1. **keyword tiebreaker 미동작 케이스**: 쿼리가 한국어 2글자 단어로만 구성된 경우 (`"구조 규칙 알려줘"`) → `specific_tokens` 빈 리스트 → clarify 반환. LLM re-ranking으로 해소 가능.
2. **topic fallback에서도 복수 후보 발생 가능**: Scenario A 유형에서도 tiebreaker 실패 케이스 발생 가능. 동일하게 LLM re-ranking 권장.

자세한 권장 사항은 `ai-work/plans/rag-llm-reranking-recommendation.md` 참조.
