# P3-BUG-07: \_matches_alias docstring에 re.ASCII 적용 이유 미문서화

우선순위: P3
작성일: 2026-03-24
출처: QA Report — ai-work/qa/qa-report-P1-BUG-02-alias-normalizer-re-ascii-2026-03-24.md Issue #3

## 현상

`_matches_alias()` 함수 docstring에 `re.ASCII` 플래그의 존재와 필요성이 언급되어 있지 않다.

```python
# src/convention_qa/query_understanding/alias_normalizer.py:121-139
# 현재 docstring: re.ASCII 관련 설명 없음
```

향후 유지보수자가 플래그를 의도치 않게 제거하거나, ASCII alias 분기에 새 정규식을 추가할 때
동일한 버그(P1-BUG-02)를 재발시킬 가능성이 있다.

## 원인

P1-BUG-02 수정 시 `re.ASCII` 플래그를 코드에 추가했으나 docstring 업데이트가 누락되었다.

## 수정 대상

**파일**: `src/convention_qa/query_understanding/alias_normalizer.py:121-139`

docstring Note 섹션에 아래 내용 추가:

```
Note:
    ASCII alias 매칭에 re.ASCII 플래그를 사용한다.
    기본 유니코드 모드에서는 한국어 글자도 \\w로 분류되어
    "Java에서" 같은 입력에서 'a'와 '에' 사이에 \\b가 성립하지 않는 문제가 있다.
    re.ASCII 적용 시 \\w = [a-zA-Z0-9_]로 제한되어 '에'가 \\W로 분류되고
    단어 경계가 올바르게 동작한다. (P1-BUG-02 참조)
```

## 완료 기준

- [x] `_matches_alias()` docstring에 `re.ASCII` 플래그 적용 이유 명시
- [x] 코드 변경 없음 (docstring 수정만)
