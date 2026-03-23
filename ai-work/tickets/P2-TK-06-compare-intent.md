# P2-TK-06: Compare Intent 도입

우선순위: P2
작성일: 2026-03-23
선행: P1 전체 완료
관련 플랜: ai-work/plans/architecture-v3.md §[3] compare handler

## 배경

"FE vs BE 네이밍 차이점", "Java와 Kotlin 네이밍 비교" 등의 비교 질문에 대응한다.
두 문서를 각각 resolution한 후 차이점 중심 LLMChain으로 응답한다.

## 목표

- compare intent 분류 추가
- 두 문서 동시 resolution 로직
- 차이점/충돌 지점 강조 프롬프트로 compare 응답 생성

## 입력 예시

- "Java Spring과 Kotlin Spring 네이밍 컨벤션 차이점 알려줘"
- "프론트엔드와 백엔드 네이밍 규칙 비교해줘"
- "FSD 아키텍처와 레이어드 아키텍처 차이점"

## 구현 대상

**`src/convention_qa/action_routing/`**
- `compare_handler.py`: CompareHandler — 두 doc resolution + LLMChain

**`src/convention_qa/query_understanding/`**
- intent_classifier 프롬프트 업데이트 (compare 예시 추가)

## 완료 기준

- [ ] compare intent 분류 테스트 통과
- [ ] 두 문서 동시 resolution 로직 구현
- [ ] compare 응답 포맷 정의 및 구현
- [ ] 문서 간 충돌/차이 설명 품질 검증
