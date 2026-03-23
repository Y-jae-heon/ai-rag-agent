# Product Contract v3

작성일: 2026-03-23
관련 문서: ai-work/plans/architecture-v3.md, ai-docs/rag-init-document.md §8 §9

## 제품 정의

Developer Convention Chat Bot v3는 팀 개발 컨벤션 문서를 탐색하고, 요약하고, 원문을 제공하는 **문서 탐색 + 의도별 실행 시스템**이다.

v2와의 핵심 차이:
- v2: retrieved chunk 근거 기반의 규칙 QA 시스템
- v3: document-resolution + intent-specific execution 시스템

---

## 지원하는 Intent 유형

### discover
문서가 존재하는지 확인하고 위치를 반환한다.

**트리거 예시**:
- "어떤 네이밍 컨벤션 문서가 있어?"
- "FSD 관련 문서 있어?"
- "프론트엔드 문서 목록 보여줘"

**응답 계약**:
- 문서 제목, 경로, 도메인/스택, 주요 섹션 목록
- 관련 문서 링크
- LLM 생성 없음 (결정적 포맷)

---

### summarize
지정된 문서의 전반적인 구조와 핵심 규칙을 설명한다.

**트리거 예시**:
- "파일 네이밍 컨벤션 내용 알려줘"
- "FSD 아키텍처 문서 설명해줘"
- "Java Spring 네이밍 컨벤션 뭐가 있어"

**응답 계약**:
- 문서명 명시 + 문서가 resolved된 경우에만 실행
- 3~6개 핵심 항목으로 요약
- 주요 섹션과 대표 규칙 포함
- 요약 출처(문서명) 명시

**제약**:
- document resolution 실패 시 clarify 응답
- section_index 기반 (chunk 기반 아님)

---

### extract
문서 내 특정 규칙이나 섹션을 추출한다.

**트리거 예시**:
- "파일 네이밍 컨벤션에서 테스트 파일 규칙만 알려줘"
- "Java Spring에서 서비스 클래스 네이밍 방법"
- "FSD에서 feature 레이어 구조"

**응답 계약**:
- 질문 대상 규칙과 근거 섹션 명시
- retrieved context만 authority
- 문서 미명시 시 domain/stack 기반 일반 extract

---

### fulltext
지정된 문서의 원문 전체를 반환한다.

**트리거 예시**:
- "파일 네이밍 컨벤션 전문 보여줘"
- "FSD 아키텍처 개요 원문 줘"
- "Java Spring 네이밍 컨벤션 문서 전체 보여줘"

**응답 계약**:
- document resolution 1개 확정 후에만 실행
- 파일 원문 그대로 반환 (LLM 생성 없음)
- corpus 허용 경로(docs/) 내 파일만 제공

**제약**:
- document unresolved → clarify 요청
- 다중 후보 → 문서 선택 요청
- corpus 외 경로 → 거부

---

### compare
두 문서 간의 차이점과 충돌 지점을 설명한다.

**트리거 예시**:
- "Java와 Kotlin 네이밍 컨벤션 차이점"
- "FE vs BE 테스트 파일 규칙 비교"

**응답 계약**:
- 비교 대상 두 문서 명시
- 차이점과 충돌 지점 강조
- 각 문서 출처 명시

---

## 지원하지 않는 것

- 컨벤션 문서에 없는 규칙 생성 (undocumented policy 금지)
- corpus 외부 파일 접근
- 여러 문서 동시 fulltext 출력
- 실시간 코드 검토 (코드 분석 기능 없음)

---

## Clarify 정책

다음 상황에서 시스템은 사용자에게 명확화를 요청한다:

1. **document_query unresolved**: 문서명을 특정할 수 없을 때
2. **다중 후보**: 2개 이상의 후보 문서가 있을 때
3. **intent 모호**: discover와 summarize 구분이 불가능할 때
4. **도메인 불명확**: FE/BE 중 어떤 영역인지 불분명할 때

clarify 응답은 후보 목록과 함께 선택을 유도한다.

---

## 응답 품질 기준

| 항목 | 기준 |
|------|------|
| document resolution 정확도 | 문서명 명시 시 95% 이상 |
| fulltext 원문 일치 | 100% (변형 금지) |
| summarize 섹션 커버리지 | 문서 주요 섹션 80% 이상 포함 |
| extract 근거 정확도 | retrieved context 이탈 금지 |
| 응답 시간 | fulltext 2초 이내, 나머지 5초 이내 |
