# P1-TK-05: Discover & Summarize 응답 포맷 분리

우선순위: P1
작성일: 2026-03-23
선행: P0-TK-01, P0-TK-02
관련 플랜: ai-work/plans/architecture-v3.md §[5], Phase 6

## 배경

v2의 deterministic 응답은 "관련 문서: 제목 (경로)"만 반환하여 사용자 의도를 충족하지 못했다.
(rag-init-document.md 원인D: deterministic fallback이 content answer가 아니라 document listing path)

## 목표

각 intent별로 명확히 다른 응답 포맷과 정책을 분리한다.

## intent별 응답 포맷 정의

### discover
```markdown
## 문서 발견 결과

**제목**: 파일 네이밍 컨벤션
**경로**: docs/fe_chunk_docs/파일 네이밍 컨벤션 325e63c6...md
**도메인**: Frontend / React
**주요 섹션**: 컴포넌트 파일, 훅 파일, 유틸리티 파일, 테스트 파일

관련 문서:
- 폴더 네이밍 컨벤션
- 네이밍 컨벤션 개요
```

### summarize
```markdown
## 파일 네이밍 컨벤션 요약

이 문서는 React 프론트엔드 프로젝트의 파일 네이밍 규칙을 정의합니다.

### 핵심 규칙
1. **컴포넌트 파일**: PascalCase (`UserProfile.tsx`)
2. **훅 파일**: camelCase, use 접두사 (`useUserData.ts`)
3. **유틸리티**: camelCase (`formatDate.ts`)
4. **테스트 파일**: kebab-case + .spec.ts (`user-profile.spec.ts`)
...

> 출처: 파일 네이밍 컨벤션 (docs/fe_chunk_docs/...)
```

### extract (기존 QA 포맷 유지)
```markdown
## Test 파일 네이밍 규칙

테스트 파일은 `{kebab-case}.spec.ts` 형식을 따릅니다.

예시: `user-profile.spec.ts`, `use-auth.spec.ts`

> 근거: 파일 네이밍 컨벤션 §테스트 파일 섹션
```

### fulltext
```markdown
## [원문] 파일 네이밍 컨벤션

> 경로: docs/fe_chunk_docs/파일 네이밍 컨벤션 325e63c6...md

---

[원문 그대로]
```

### clarify (document unresolved)
```markdown
어떤 문서를 찾으시나요?

다음 중 하나를 선택하거나 더 구체적으로 질문해주세요:
1. 파일 네이밍 컨벤션 (Frontend)
2. 폴더 네이밍 컨벤션 (Frontend)
3. Java(Spring) 네이밍 컨벤션 (Backend)
```

## 구현 대상

**`src/convention_qa/response/`**
- `formatters.py`: 각 intent별 포맷터 함수
- `models.py`: `QueryResponse` Pydantic 모델

## 완료 기준

- [ ] 5개 intent 포맷터 구현 완료
- [ ] `QueryResponse` 모델 정의
- [ ] FastAPI endpoint에서 포맷터 연동
- [ ] 각 포맷 단위 테스트 통과
