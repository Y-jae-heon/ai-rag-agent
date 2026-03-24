---
name: alias_normalizer 반복 패턴 및 위험 영역
description: alias_normalizer.py에서 반복적으로 발견되는 결함 패턴과 QA 시 주의할 고위험 코드 영역
type: project
---

alias_normalizer.py는 regex 플래그와 한국어/ASCII 분기 처리가 얽혀 있어 단순 변경도 엣지케이스를 야기할 수 있는 고위험 파일이다.

**Why:** re.ASCII 플래그 변경 1줄로 인해 Java(Spring)으로 케이스의 우연 동작이 역전되는 등, 플래그 하나가 여러 케이스에 비선형적으로 영향을 미침.

**How to apply:** 이 파일 수정 시 반드시 아래 시나리오를 시뮬레이션할 것:
1. ASCII alias + 한국어 조사 조합 (Java에서, Kotlin으로, BE에서 등)
2. ) 로 끝나는 compound alias (Java(Spring), Kotlin(Spring) 등) — \b 미동작 원인: \W-\W 경계
3. 부분 일치 방지 (JavaScript vs Java, SpringBoot vs Spring)
4. _STACK_ALIASES dict 순회 순서 의존성 (kotlin이 spring보다 앞이어야 Kotlin(Spring) 케이스가 올바른 결과를 반환함)
5. 한국어 alias는 in 검사 경로 유지 확인

**해소된 결함 (2026-03-24 기준):**
- P1-BUG-02: re.ASCII 플래그 미사용으로 Java에서 등 한국어 조사 앞 alias 미매칭 → 해소
- P2-BUG-05: alias_normalizer.py 자동화 단위 테스트 파일 미존재 → 해소 (10개 케이스)
- P3-BUG-06: ) 로 끝나는 alias 6개 \b 미동작 및 Kotlin(Spring) 의미 오류 → 해소 (alias 제거 + dict 순서 변경)

**잔존 위험 (2026-03-24 기준):**
- _STACK_ALIASES dict 순서 의존성 경고 주석이 간략함 — 향후 alias 추가/정렬 리팩터링 시 무음 회귀 위험
- TypeScript 단독 alias 미존재 — normalize_stack("TypeScript로 개발") → None 반환 (의도 여부 미확인)
- 소문자 alias("fe", "be", "spring", "java"), 한국어 alias 단독 테스트 케이스 미포함

**테스트 파일 현황 (2026-03-24 기준):**
- tests/convention_qa/query_understanding/test_alias_normalizer.py 존재 (12개 케이스, pytest 12/12 PASS 확인)
- 회귀 방지 핵심 케이스: test_ascii_alias_followed_by_korean_matches — re.ASCII 제거 시 즉시 실패
- dict 순서 의존 케이스: test_kotlin_spring_maps_to_kotlin — _STACK_ALIASES 재정렬 시 즉시 실패
