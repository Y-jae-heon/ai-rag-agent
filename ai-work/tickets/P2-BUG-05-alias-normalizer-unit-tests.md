# P2-BUG-05: alias_normalizer 단위 테스트 파일 미존재

우선순위: P2
작성일: 2026-03-24
출처: QA Report — ai-work/qa/qa-report-P1-BUG-02-alias-normalizer-re-ascii-2026-03-24.md Issue #2

## 현상

`tests/convention_qa/query_understanding/test_alias_normalizer.py` 파일이 존재하지 않는다.

P1-BUG-02 완료 기준에 "테스트 케이스 전원 통과"가 명시되어 있으나, 자동화 단위 테스트로 검증되지 않아 향후 동일 버그 재발 시 감지 불가 상태다.

## 원인

alias_normalizer.py에 대한 테스트 파일이 한 번도 생성된 적 없다. `re.ASCII` 플래그처럼 정규표현식 플래그 하나의 변경이 한국어 입력과의 상호작용에 영향을 주는 경우, 자동화 테스트 없이는 회귀를 탐지할 수 없다.

## 영향 범위

- **파일**: `src/convention_qa/query_understanding/alias_normalizer.py` 전체
- **위험**: 향후 `_matches_alias()` 수정 시 `re.ASCII` 플래그 제거 등 회귀가 발생해도 CI에서 감지 불가

## 수정 대상

**신규 파일**: `tests/convention_qa/query_understanding/test_alias_normalizer.py`

포함해야 할 최소 테스트 케이스:

| 테스트                 | 입력                                               | 기대값       |
| ---------------------- | -------------------------------------------------- | ------------ |
| 핵심 버그 회귀         | `_matches_alias("Java에서 트랜잭션", "Java")`      | `True`       |
| 부분 일치 방지         | `_matches_alias("JavaScript", "Java")`             | `False`      |
| 부분 일치 방지         | `_matches_alias("JavaEE에서 트랜잭션", "Java")`    | `False`      |
| 비ASCII alias (한국어) | `_matches_alias("스프링으로 개발", "스프링")`      | `True`       |
| stack 정규화           | `normalize_stack("Java에서 트랜잭션 관리하는 법")` | `"spring"`   |
| stack 정규화           | `normalize_stack("Kotlin으로 테스트 작성")`        | `"kotlin"`   |
| stack 정규화           | `normalize_stack("React 컴포넌트 구조")`           | `"react"`    |
| stack 정규화           | `normalize_stack("파이썬으로 API 만들기")`         | `None`       |
| domain 정규화          | `normalize_domain("FE에서 처리")`                  | `"frontend"` |
| domain 정규화          | `normalize_domain("BE에서 API")`                   | `"backend"`  |

## 완료 기준

- [x] `tests/convention_qa/query_understanding/test_alias_normalizer.py` 파일 생성
- [x] 위 테스트 케이스 전원 `pytest` 통과
- [x] `__init__.py` 파일 필요 시 함께 생성
