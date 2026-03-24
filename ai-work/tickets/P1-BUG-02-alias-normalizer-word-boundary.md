# P1-BUG-02: alias_normalizer ASCII 단어 경계 — 한국어 접사 미인식

우선순위: P1
작성일: 2026-03-24
관련 분석: ai-work/plans/post-fix-debug-analysis.md §Bug 1

## 현상

`normalize_stack("Java에서 트랜잭션 관리하는 법 알려줘")` → `None`

기대값은 `"spring"` (`"Java"` alias → `"spring"` 정규화).

## 원인

`_matches_alias()`에서 ASCII alias 매칭 시 Python `re`의 `\b`를 사용하는데,
`re`의 기본 `\b`는 유니코드 `\w`를 기준으로 동작하므로 한국어 글자(`에`)도 `\w`로 분류된다.

```python
# src/convention_qa/query_understanding/alias_normalizer.py:135-136 (현재)
pattern = r"\b" + re.escape(alias) + r"\b"
return bool(re.search(pattern, text))
# "Java에서" → 'a'(\\w) 와 '에'(\\w) 사이에 \\b 없음 → 매칭 실패
```

ASCII alias에 `re.ASCII` 플래그를 적용하면 `\w = [a-zA-Z0-9_]`로 제한되어
`'에'`가 `\W`로 분류되고 `Java` 뒤에 단어 경계가 발생한다.

```python
# 수정 방향
return bool(re.search(pattern, text, re.ASCII))
```

## 연쇄 영향

```
normalize_stack(question) = None
  → Fix 3 pre_stack 보정 미동작
  → LLM 반환 stack='Java' 그대로 사용
  → semantic_search(filter={'stack': 'Java'}) → 0건 (ChromaDB에는 'spring' 저장)
  → fallback 검색 → 관련 없는 문서 5건 반환
  → resolved=False → ExtractHandler → not_found
```

## 수정 대상

**파일**: `src/convention_qa/query_understanding/alias_normalizer.py:135-136`

```python
# 수정 후
pattern = r"\b" + re.escape(alias) + r"\b"
return bool(re.search(pattern, text, re.ASCII))
```

## 테스트 케이스

| 입력                                                      | 기대값                                  |
| --------------------------------------------------------- | --------------------------------------- |
| `normalize_stack("Java에서 트랜잭션 관리하는 법 알려줘")` | `"spring"`                              |
| `normalize_stack("Java Spring 트랜잭션")`                 | `"spring"` (기존 정상 케이스 회귀 없음) |
| `normalize_stack("Kotlin으로 테스트 작성")`               | `"kotlin"`                              |
| `normalize_stack("React 컴포넌트 구조")`                  | `"react"`                               |

## 완료 기준

- [x] `_matches_alias()`: ASCII alias 매칭에 `re.ASCII` 플래그 적용
- [x] 위 테스트 케이스 전원 통과
- [x] `"Java에서 트랜잭션 관리하는 법 알려줘"` 요청 시 `resolved=True`, `answer_type="extract"` 반환
