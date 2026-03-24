# 권장 사항: LLM Re-ranking 도입

> 상태: **MVP 이후 검토 권장** (현재 미적용)
> 관련 문서: `ai-work/plans/rag-search-improvement.md`

---

## 배경

`rag-search-improvement.md`의 Scenario B (점수 격차 부족으로 resolved 실패) 해결을 위해
LLM re-ranking이 검토되었으나, MVP 단계에서는 다음 이유로 제외:

- 복수 후보 발생마다 추가 LLM API 호출 발생 → 비용 증가
- 사용자 응답 시간 증가 (gpt-4o-mini 기준 ~0.5~1초 추가 지연)

MVP에서는 **Title Keyword Tiebreaker** (추가 LLM 호출 없음)로 대체 적용.

---

## LLM Re-ranking 도입 시 기대 효과

Keyword Tiebreaker의 한계를 극복:

| 케이스 | Keyword Tiebreaker | LLM Re-ranking |
|--------|-------------------|----------------|
| 쿼리 키워드 ∈ 타이틀 | 해결 가능 | 해결 가능 |
| 쿼리 키워드 ∉ 어느 타이틀 | **미해결** (clarify 반환) | **해결 가능** |
| 매칭 타이틀 2개 이상 | **미해결** | 해결 가능 |
| 추상적 의미 매핑 필요 | **미해결** | 해결 가능 |

예시: "Java 트랜잭션 관련 패턴 알려줘" → 후보 타이틀 모두 키워드 미포함 → tiebreaker 실패 → LLM이라면 맥락으로 선택 가능.

---

## 구현 설계

### 새 파일: `src/convention_qa/document_resolution/llm_reranker.py`

```python
def llm_rerank(
    question: str,
    candidates: list[DocumentCandidate],
) -> DocumentCandidate | None:
    """LLM을 이용해 복수 후보 중 가장 관련성 높은 문서를 선택한다.

    Args:
        question: 사용자 원본 질문
        candidates: 시맨틱 검색 후보 목록

    Returns:
        선택된 DocumentCandidate, 또는 None (관련 문서 없음 판단 시)
    """
```

**프롬프트 구성**:

```
당신은 개발 컨벤션 문서 검색 도우미입니다.
다음 질문에 가장 관련성 높은 문서를 번호로 선택하세요.
관련 문서가 없으면 "none"을 반환하세요.

질문: {question}

후보 문서:
[1] 제목: {title_1}
    섹션: {headings_1}
[2] 제목: {title_2}
    섹션: {headings_2}
...

출력 형식: 숫자(1~N) 또는 "none"
```

모델: `gpt-4o-mini`, temperature=0

### 수정 파일: `src/convention_qa/document_resolution/resolver.py`

`_evaluate_candidates()` 내 keyword tiebreaker 이후 fallback으로 LLM re-ranking 삽입:

```python
# 1차: keyword tiebreaker
tiebreak = _keyword_tiebreak(query, candidates)
if tiebreak is not None:
    return DocumentResolutionResult(resolved=True, ..., resolution_strategy="keyword_tiebreak")

# 2차: LLM re-ranking (MVP 이후 활성화)
from .llm_reranker import llm_rerank
reranked = llm_rerank(question, candidates)
if reranked is not None:
    return DocumentResolutionResult(resolved=True, ..., resolution_strategy="llm_rerank")

# 최종: clarify
return DocumentResolutionResult(resolved=False, ...)
```

---

## 비용 고려사항

- 추가 LLM 호출 빈도: 복수 후보 & keyword tiebreaker 실패 건수에 비례
- 현재 문서 corpus 규모 기준 예상 호출: 전체 쿼리의 10~20% (복수 후보 발생 비율 추정)
- 비용 절감 전략 (도입 시 검토):
  - 후보 수 제한: k=3으로 줄여 re-ranking 입력 최소화
  - 캐싱: 동일 query+후보 조합 결과 캐싱 (TTL 기반)
  - 호출 조건 강화: `best.score < 0.4` 인 경우에만 LLM re-ranking 실행
