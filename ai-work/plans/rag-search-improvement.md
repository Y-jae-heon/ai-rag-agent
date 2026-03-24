# RAG 검색 리스크 개선 계획

> 출처: `ai-docs/2026-03-24-15:11-feedback-report.md`
> 작성일: 2026-03-24

---

## 근본 원인 분석

### Scenario A — "Java에서 트랜잭션 관리하는 법 알려줘"

**증상**: 시맨틱 검색 진입 불가, `resolution_strategy='unresolved'`, "not found" 반환

**코드 레벨 트레이스**:

```
IntentClassifier.classify()
  → intent='extract', document_query=None, topic='트랜잭션 관리', stack='Java'

query.py:95 document_resolver.resolve(understanding.document_query)
  → resolve(document_query=None)   # domain, stack도 주석 처리되어 미전달

resolver.py:91
  if document_query is None:
      return DocumentResolutionResult(resolved=False, resolution_strategy="unresolved")
      # ← 여기서 즉시 종료, 시맨틱 검색 미진입

ActionRouter → ExtractHandler (intent='extract', resolved=False)
ExtractHandler._mmr_search(canonical_doc_id="")
  → if not canonical_doc_id: return []   # 빈 canonical_doc_id
  → format_not_found() → answer_type='not_found'
```

**핵심 원인**:

- `document_query=None`이면 resolver가 시맨틱 검색을 시도하지 않고 즉시 반환
- `topic` 필드("트랜잭션 관리")가 classifier에서 추출되지만 resolver에 전달되지 않음
- `domain`/`stack` 필터 비활성화 문제 — 주석 해제 시 오히려 더 큰 문제 발생 (Fix 3 참조)

---

### Scenario B — "FSD 구조 규칙 알려줘"

**증상**: 시맨틱 검색 실행되나 점수 격차 부족으로 `resolved=False`, "not found" 반환

**코드 레벨 트레이스**:

```
IntentClassifier.classify()
  → intent='extract', document_query='FSD 구조 규칙', domain=None

semantic_search(query='FSD 구조 규칙')
  → 5개 후보 반환:
     [1] 'Git PR 템플릿'           score=0.3465
     [2] 'FSD 레이어드 아키텍처 개요' score=0.3413
     [3] 'Kotlin(Spring) 테스트...' score=0.3411
     ...

resolver._evaluate_candidates():
  best.score=0.3465, second.score=0.3413
  score_gap = 0.3465 - 0.3413 = 0.0052  <  0.15 (임계값 미달)
  → resolved=False, resolution_strategy='semantic'

ExtractHandler: canonical_doc_id="" → chunks 없음 → format_not_found()
```

**핵심 원인**:

- document_index는 `title + aliases + section_headings`를 임베딩 (document_indexer.py:39-44)
- "FSD 구조 규칙"과 "FSD 레이어드 아키텍처 개요" 간 임베딩 거리가 커서 유사도 낮음
- 5개 후보 점수가 0.3391~0.3465로 매우 근접 → score_gap 0.0052 << 임계값 0.15
- 결과적으로 복수 후보에서 단독 resolved 불가

---

---

## domain/stack 필터 비활성화 배경 분석

> rag-retriever 서브에이전트와 협업하여 추가 확인된 사항

**document_index에 저장되는 stack canonical 값** (`markdown_parser.py:_detect_stack`):

| 파일명 패턴               | 저장되는 stack 값        |
| ------------------------- | ------------------------ |
| `Java(Spring)` 포함       | `"spring"`               |
| `Kotlin(Spring)` 포함     | `"spring"` (kotlin 아님) |
| `Typescript(NestJS)` 포함 | `"nestjs"`               |
| `fe_chunk_docs` 내 나머지 | `"react"`                |
| 그 외                     | `""` (빈 문자열)         |

**IntentClassifier stack 정규화 문제** (`intent_classifier.py:85`):

```
사용자: "Java에서 트랜잭션 관리하는 법 알려줘"
    ↓
alias_normalizer.normalize_stack("Java") → "spring"  (정규화 성공)
LLM 분류                               → stack="Java" (비정규화 반환)
    ↓
보강 조건: if pre_stack is not None and result.stack is None:
    → result.stack("Java") is None → False → 보강 안 됨
    ↓
최종 result.stack = "Java"
    ↓
semantic_search(stack="Java")
ChromaDB 필터: {"stack": {"$eq": "Java"}} → ZERO MATCH
(document_index에는 "spring"으로 저장됨)
```

**결론**: `query.py`에서 `domain`/`stack`을 주석 처리한 것은 이 필터 불일치를 우회하기 위한 임시 조치였으나, 해결책이 아닌 회피임. 근본 원인은 `IntentClassifier`가 LLM의 비정규화 stack 값을 alias_normalizer로 override하지 않는 조건부 로직에 있음.

---

## 개선 방안

### Fix 1 — Topic-based Semantic Fallback (Scenario A 해결)

**대상 파일**:

- `src/convention_qa/document_resolution/resolver.py`
- `src/api/routes/query.py`

**변경 내용**:

`resolver.resolve()` 시그니처 확장:

```python
def resolve(
    self,
    document_query: str | None,
    domain: str | None = None,
    stack: str | None = None,
    topic: str | None = None,          # 추가
    raw_question: str | None = None,   # 추가
) -> DocumentResolutionResult:
```

`document_query is None` 분기 수정 (즉시 unresolved 대신 fallback 실행):

```python
if document_query is None:
    fallback_query = topic or raw_question
    if fallback_query is None:
        return DocumentResolutionResult(resolved=False, resolution_strategy="unresolved")
    # topic 또는 raw_question으로 시맨틱 검색 실행
    candidates = semantic_search(
        document_query=fallback_query,
        persist_dir=self._persist_dir,
        domain=domain,
        stack=stack,
        threshold=self._threshold,
    )
    return self._evaluate_candidates(candidates, question=fallback_query)
```

`query.py` resolver 호출 수정:

```python
resolution = document_resolver.resolve(
    understanding.document_query,
    understanding.domain,    # 주석 해제
    understanding.stack,     # 주석 해제
    topic=understanding.topic,
    raw_question=understanding.raw_question,
)
```

**기대 효과**: "Java에서 트랜잭션 관리하는 법" → topic="트랜잭션 관리", stack="Java"로 백엔드 문서에서 시맨틱 검색 → 관련 문서 후보 반환

---

### Fix 2 — Title Keyword Tiebreaker (Scenario B 해결, MVP 적용)

> LLM re-ranking은 추가 API 호출 비용 및 응답 지연 문제로 MVP 단계에서 제외.
> 대안으로 추가 LLM 호출 없이 순수 키워드 매칭 방식을 적용.
> LLM re-ranking은 별도 권장 사항 문서(`rag-llm-reranking-recommendation.md`) 참조.

**실패 패턴 분석**:

"FSD 구조 규칙" 검색 시 임베딩 랭킹이 잘못됨:

- [1] **Git PR 템플릿** score=0.3465 ← 관련 없음, 1위
- [2] **FSD 레이어드 아키텍처 개요** score=0.3413 ← 정답, 2위

원인: "PR 작성 규칙" 같은 section heading의 "규칙" 키워드가 우연히 "Git PR 템플릿"의 임베딩 점수를 올림.
해결: 점수 격차가 작을 때, **판별력 있는 쿼리 키워드가 문서 타이틀에 포함된 후보를 우선** 선택.

**rag-retriever 재검토에서 발견된 추가 실패 케이스**:

```
query = "FSD 구조 규칙"
query_tokens = {"FSD", "구조", "규칙"}  ← len >= 2 기준 시

후보:
  [2] "FSD 레이어드 아키텍처 개요"                    → "FSD" ∈ 타이틀 → 매칭 ✓
  [5] "Typescript(NestJS) 레이어드 아키텍처 디렉토리 구조" → "구조" ∈ 타이틀 → 매칭 ✓

matched = 2개 → tiebreaker 실패!
```

"구조", "규칙" 등 한국어 2글자 단어는 여러 문서 타이틀에 등장하는 범용 단어임.
판별력 있는 토큰(고유명사, 기술 용어)만 사용해야 함.

**토큰 필터링 규칙**:

| 토큰 종류   | 기준                | 예시                         |
| ----------- | ------------------- | ---------------------------- |
| ASCII 토큰  | `len >= 2`          | FSD, BE, React, Java, NestJS |
| 한국어 토큰 | `len >= 3`          | 트랜잭션, 아키텍처, 레이어드 |
| 제외 대상   | 한국어 2글자 범용어 | 구조, 규칙, 관리, 방법, 내용 |

**대상 파일**:

- `src/convention_qa/document_resolution/resolver.py`

**변경 내용**:

`_evaluate_candidates()` 내 score_gap < 0.15 분기에 keyword tiebreaker 삽입:

```python
# 복수 후보 & 격차 부족 → keyword tiebreaker 시도
tiebreak = _keyword_tiebreak(query, candidates)
if tiebreak is not None:
    return DocumentResolutionResult(
        resolved=True,
        canonical_doc_id=tiebreak.canonical_doc_id,
        path=tiebreak.path,
        title=tiebreak.title,
        confidence=tiebreak.score,
        resolution_strategy="keyword_tiebreak",
        candidates=candidates,
    )
# tiebreaker도 결정 불가 → clarify
return DocumentResolutionResult(
    resolved=False,
    resolution_strategy="semantic",
    candidates=candidates,
)
```

`_keyword_tiebreak()` 함수 (resolver.py 내 private 함수로 추가):

```python
def _keyword_tiebreak(
    query: str,
    candidates: list[DocumentCandidate],
) -> DocumentCandidate | None:
    """판별력 있는 쿼리 키워드가 타이틀에 포함된 후보를 반환한다.

    score_gap이 작아 점수로 결정 불가 시 사용.
    - ASCII 토큰: len >= 2 (FSD, Java, React 등 기술 고유명)
    - 한국어 토큰: len >= 3 (트랜잭션, 아키텍처 등 — 범용 2글자어 제외)
    타이틀 매칭 후보가 정확히 1개일 때만 resolved=True로 처리.
    """
    raw_tokens = query.replace("(", " ").replace(")", " ").split()
    specific_tokens = [
        t for t in raw_tokens
        if (t.isascii() and len(t) >= 2) or (not t.isascii() and len(t) >= 3)
    ]
    if not specific_tokens:
        return None
    matched = [
        c for c in candidates
        if any(token in c.title for token in specific_tokens)
    ]
    return matched[0] if len(matched) == 1 else None
```

`_evaluate_candidates()`에 `query: str` 파라미터 추가 필요.

**동작 예시**:

```
query = "FSD 구조 규칙"
raw_tokens = ["FSD", "구조", "규칙"]
specific_tokens = ["FSD"]  ← "구조"(한국어 2글자), "규칙"(한국어 2글자) 제외

후보:
  [1] "Git PR 템플릿"                                → "FSD" ∉ → 미매칭
  [2] "FSD 레이어드 아키텍처 개요"                    → "FSD" ∈ → 매칭 ✓
  [5] "Typescript(NestJS) 레이어드 아키텍처 디렉토리 구조" → "FSD" ∉ → 미매칭

matched = ["FSD 레이어드 아키텍처 개요"] (1개) → resolved=True ✓
```

**기대 효과**: 추가 LLM 호출 없이 "FSD 레이어드 아키텍처 개요" 선택 → resolved=True → ExtractHandler 정상 답변

---

### Fix 3 — Stack 정규화 보강 로직 수정 (domain/stack 필터 정확도 복원)

**대상 파일**:

- `src/convention_qa/query_understanding/intent_classifier.py`
- `src/api/routes/query.py`

**변경 내용**:

`intent_classifier.py` 보강 조건 수정 — LLM 반환값과 무관하게 alias_normalizer 값으로 항상 override:

```python
# 현재 (결함 있는 조건)
if pre_stack is not None and result.stack is None:
    result = result.model_copy(update={"stack": pre_stack})

# 수정 후 (항상 정규화된 값으로 override)
if pre_stack is not None:
    result = result.model_copy(update={"stack": pre_stack})
```

같은 방식으로 `domain`도 동일하게 수정:

```python
# 현재
if pre_domain is not None and result.domain is None:

# 수정 후
if pre_domain is not None:
```

`query.py` domain/stack 주석 해제:

```python
resolution = document_resolver.resolve(
    understanding.document_query,
    understanding.domain,    # 주석 해제 (Fix 3 적용 후 안전)
    understanding.stack,     # 주석 해제 (Fix 3 적용 후 안전)
    topic=understanding.topic,
    raw_question=understanding.raw_question,
)
```

**기대 효과**:

- LLM이 "Java" 반환 → alias_normalizer가 "spring"으로 override → 필터 정확 매칭
- domain/stack 필터 재활성화로 검색 정밀도 향상
- Step 4 (필터 없는 retry)는 여전히 유지되어 domain/stack 불명확 시 fallback 보장

---

## 변경 파일 목록

| 파일                                                         | 변경 유형 | 내용 요약                                                                                   |
| ------------------------------------------------------------ | --------- | ------------------------------------------------------------------------------------------- |
| `src/convention_qa/query_understanding/intent_classifier.py` | 수정      | domain/stack 보강 조건 수정 — alias_normalizer 값으로 항상 override (Fix 3)                 |
| `src/convention_qa/document_resolution/resolver.py`          | 수정      | `resolve()` 시그니처 확장, topic fallback, `_evaluate_candidates()` keyword tiebreaker 삽입 |
| `src/api/routes/query.py`                                    | 수정      | domain/stack 주석 해제, `topic`/`raw_question` 추가 전달                                    |

---

## 검증 방법

서버 실행:

```bash
uvicorn src.api.main:app --reload
```

Scenario A 검증:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Java에서 트랜잭션 관리하는 법 알려줘"}'
```

기대값:

- `resolution_strategy` ≠ `"unresolved"`
- `answer_type` = `"extract"` (not_found 아님)

Scenario B 검증:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "FSD 구조 규칙 알려줘"}'
```

기대값:

- `resolved_document.title` 포함 FSD 관련 문서
- `answer_type` = `"extract"`

로그 확인 포인트:

- `RESOLVE STEP 1 :: None` → topic fallback 진입 확인
- `resolution_strategy='keyword_tiebreak'` → tiebreaker 동작 확인

## 미결 사항 / 고려사항

1. **keyword tiebreaker의 specific_tokens 부재 케이스**: 쿼리가 한국어 2글자 단어로만 구성된 경우 specific_tokens가 빈 리스트 → tiebreaker 동작 안 함 → clarify 반환. (예: "구조 규칙 알려줘")
2. **topic fallback 결과도 복수 후보 + tiebreaker 실패 가능**: Scenario A의 topic 기반 검색에서도 동일한 복수 후보 문제가 발생할 수 있음. LLM re-ranking으로 해소 가능.

---

## 권장 사항 (MVP 이후)

- **LLM re-ranking**: keyword tiebreaker가 커버 못하는 케이스 해결 → `ai-work/plans/rag-llm-reranking-recommendation.md` 참조
- **chunk_index 기반 document resolution**: document_index(title+headings 임베딩) 대신 chunk_index(실제 내용 임베딩)로 검색하여 집계하는 방식. 의미적 정확도가 더 높으나 집계 로직 추가 필요. LLM 추가 비용 없이 근본적 유사도 개선 가능하므로 중장기 검토 권장.
