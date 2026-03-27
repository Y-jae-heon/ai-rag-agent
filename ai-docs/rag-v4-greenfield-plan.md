# RAG v4 Greenfield Plan

작성일: 2026-03-26

## 1. 목표

v4는 v3 코드를 이관하지 않고, 검색 중심 MVP를 greenfield로 다시 설계한다.

핵심 목표는 다음과 같다.

- 질문 표현이 조금 달라져도 같은 문서군을 안정적으로 찾는다.
- `frontend`, `backend`, `framework` 같은 단어가 strict mode처럼 동작하며 후보를 폐기하지 않게 한다.
- 문서 파싱 단위와 검색 단위를 다시 설계해 고맥락 문서를 더 자연스럽게 다룬다.
- local Chroma 환경에서 hybrid retrieval을 현실적으로 운영 가능하게 구성한다.
- 디버깅 가능한 trace와 benchmark를 함께 설계한다.

---

## 2. 현재 문제 재정리

### 2-1. 단어 하나 차이로 retrieval 결과가 쉽게 흔들린다

예시:

- `FSD 구조 규칙 알려줘`
- `프론트엔드 FSD 구조 규칙 알려줘`

사용자 의도는 거의 같지만, qualifier 단어 하나가 ranking 또는 gating에 영향을 주며 결과가 흔들린다.

### 2-2. alias 및 strict filtering이 retrieval을 돕기보다 방해한다

문제는 alias 자체가 아니라, alias/metadata가 hard gate로 동작하는 구조다.

- qualifier 단어가 retrieval hint가 아니라 엄격 모드처럼 동작함
- 문서명을 정확히 못 맞추면 전체 후보가 버려짐
- soft boost여야 할 정보가 hard reject 조건이 됨

### 2-3. 문서 파싱 자체가 문서 구조를 충분히 반영하지 못한다

현재 문서들에는 다음과 같은 H1 기반 구조가 많다.

- `# Title`
- `# Rule`
- `# Rationale`
- `# Exception`
- `# Override`

이 구조를 semantic section으로 올바르게 다루지 않으면, FSD 개요 같은 핵심 문서가 section 수준 retrieval에서 불리해진다.

### 2-4. metadata 분류가 retrieval 핵심 경로에 끼어드는 것이 위험하다

`domain`, `framework`, `language`를 retrieval metadata에 두고 필터에 사용하면 다음 문제가 생긴다.

- 정규화 오류가 바로 0-hit로 이어짐
- 같은 기술 계열 문서가 과도하게 분리됨
- 질문의 qualifier가 boost가 아니라 filter로 동작함

v4에서는 이 경로를 제거해야 한다.

---

## 3. v4 제품 범위

v4 1차는 검색 중심 MVP로 제한한다.

포함:

- hybrid retrieval
- answer generation
- citation
- FastAPI
- Gradio UI
- LangSmith trace
- retrieval benchmark

제외:

- v3 intent parity 전면 복구
- compare/fulltext/discover 재구축
- agentic RAG

즉, v4의 1차 목표는 “정확히 잘 찾고, 찾은 근거로 답한다”이다.

---

## 4. 아키텍처 원칙

### 4-1. v3 코드 이관 금지

v4는 별도 패키지로 새로 만든다.

- ingest
- retrieval
- answering
- api
- observability

### 4-2. metadata는 가볍게 유지한다

retrieval metadata는 최소 필드만 둔다.

- `doc_id`
- `title`
- `source_path`
- `section_id`
- `section_type`

다음 필드는 retrieval metadata에서 제거한다.

- `domain`
- `framework`
- `language`

이 정보가 필요하다면 필터가 아니라 indexed text의 lexical signal로만 반영한다.

### 4-3. qualifier는 filter가 아니라 signal이다

예:

- `프론트엔드`
- `백엔드`
- `Java`
- `Kotlin`
- `NestJS`

이 단어들은 후보를 폐기하는 기준이 아니라 ranking boost용 lexical signal이어야 한다.

### 4-4. boolean document resolution gate를 제거한다

v3처럼 문서가 먼저 단일 resolved 되어야만 답변으로 진입하는 구조는 피한다.

v4는 다음 순서를 따른다.

1. hybrid retrieval
2. 문서/섹션 evidence 집계
3. evidence가 충분하면 바로 answer
4. 정말 모호할 때만 clarification

---

## 5. 파싱 설계

### 5-1. H1 기반 semantic block 파싱

v4 파서는 `##` 이상만 section으로 보지 않는다.

다음 H1 블록도 semantic section으로 취급한다.

- `Title`
- `Rule`
- `Rationale`
- `Exception`
- `Override`

### 5-2. 문서 상단 metadata block은 제외

예:

- `ID: ...`
- `버전: ...`
- `생성일: ...`

이런 front metadata는 retrieval 본문이 아니므로 section text에서 제거한다.

### 5-3. 검색 단위는 semantic section 기본

문서 전체를 무제한 chunk로 쪼개지 않는다.

기본 단위:

- semantic section 1개 = 검색 기본 단위

예외:

- 긴 section만 window 분할

설정:

- `chunk_size`: 800 token
- `chunk_overlap`: 120 token

즉, 6-2안을 채택한다.

---

## 6. Retrieval 설계

### 6-1. Dense 인덱스

local Chroma에 dense 인덱스 2개를 둔다.

- `document_dense`
- `section_dense`

용도:

- `document_dense`: 문서군 후보 찾기
- `section_dense`: 실제 evidence 찾기

### 6-2. Sparse 인덱스

문서 요구사항상 BM25 계열 lexical retrieval이 필요하다.

참고 문서:

- [Chroma BM25](https://docs.trychroma.com/integrations/embedding-models/chroma-bm25)

다만 local Chroma에서는 hybrid search API가 직접 완성된 형태로 동작하지 않을 수 있으므로, v4에서는 다음 원칙으로 간다.

- Chroma BM25 embedding/tokenization 규칙을 기준으로 sparse retrieval을 구성한다.
- 최종 fusion은 애플리케이션 레이어에서 수행한다.

즉, “Chroma가 하이브리드를 알아서 해주는 구조”가 아니라, “dense와 sparse를 분리 조회하고 Python에서 fuse하는 구조”가 기준이다.

### 6-3. Fusion 방식

retrieval은 세 경로를 병렬 실행한다.

- `document_dense`
- `section_dense`
- `section_sparse`

문서 단위 최종 ranking은 weighted RRF를 사용한다.

초기 가중치:

- `section_dense = 0.50`
- `section_sparse = 0.35`
- `document_dense = 0.15`

이 비중의 의미는 다음과 같다.

- 실제 answer 근거는 section evidence가 중심
- lexical 보강은 필요하지만 semantic을 완전히 덮지 않음
- document_dense는 coarse candidate recall 용도

### 6-4. alias 처리 원칙

alias는 유지하더라도 strict rule로 쓰지 않는다.

사용 원칙:

- lexical expansion
- query/document text augmentation
- boost only

금지:

- exact title fallback 강제
- alias miss 시 candidate 폐기
- qualifier 기반 strict retrieval mode

---

## 7. 질의 정규화 설계

v4 질의 정규화는 taxonomy classifier가 아니다.

목표:

- 표기 흔들림 완화
- 약어 확장
- punctuation normalization
- 한국어/영문 혼용 완화

예시:

- `FSD` ↔ `Feature-Sliced Design`
- `PR` ↔ `Pull Request`
- `front-end` ↔ `frontend`
- 괄호, 하이픈, 대소문자 정리

중요한 점:

- 정규화 결과가 filter로 사용되면 안 됨
- query text를 더 풍부하게 만드는 방향이어야 함

---

## 8. 임베딩 모델 재검토

### 결론

v4 1차 baseline에서는 `text-embedding-3-small` 유지가 타당하다.

### 이유

현재 리스크의 중심은 아래 순서다.

1. 문서 파싱 단위 문제
2. hard filtering / strict gating 문제
3. lexical recall 부족
4. metadata 오남용
5. 그 다음이 embedding capacity

즉, 지금은 embedding 모델보다 retrieval 구조 문제가 더 크다.

### 재검토 방침

그래도 A/B benchmark는 설계에 포함한다.

비교 대상:

- `text-embedding-3-small`
- `text-embedding-3-large`

평가 기준:

- top-1 정확도
- top-3 recall
- FSD 리스크 케이스 안정성
- 한국어/영문 혼합 질의 안정성
- 비용 대비 개선폭

판단 원칙:

- large가 명확한 개선을 보이지 않으면 baseline 유지
- 구조 개선 없이 모델만 교체하는 접근은 채택하지 않음

---

## 9. API / UI 설계

### 9-1. FastAPI

제공 endpoint:

- `POST /api/v4/query`
- `GET /health`

요청 모델:

- `question`
- optional `debug`

제외:

- `domain_hint`
- `framework_hint`
- `stack_hint`

응답 모델:

- `answer`
- `citations`
- `top_documents`
- `confidence`
- `needs_clarification`
- optional `trace_id`
- optional `debug`

### 9-2. Gradio UI

UI는 API만 호출하는 thin client로 둔다.

구성:

- 채팅 입력
- 답변 출력
- optional debug 보기

제거:

- domain dropdown
- framework dropdown
- hard hint UI

---

## 10. Trace / Observability 설계

LangSmith는 단계별 trace 용도로 붙인다.

trace 단계:

- `normalize`
- `retrieve_dense_doc`
- `retrieve_dense_section`
- `retrieve_sparse_section`
- `fuse`
- `answer`
- `format_response`

목적:

- 어떤 질의가 어떤 normalized text로 바뀌었는지 확인
- dense/sparse 각각 어떤 결과를 냈는지 확인
- fusion 이후 어떤 문서가 왜 올라왔는지 확인
- answer가 어떤 evidence에 기반했는지 확인

---

## 11. Benchmark / 테스트 설계

최소 포함 benchmark 케이스:

- `FSD 구조 규칙 알려줘`
- `프론트엔드 FSD 구조 규칙 알려줘`
- `Java에서 트랜잭션 관리하는 법 알려줘`
- Java/Kotlin/Spring/NestJS 혼합 질의
- 한국어/영문 약어 변형
- H1 중심 문서

회귀 테스트 범주:

- H1 semantic block parsing
- metadata 최소화 후 retrieval 유지
- alias boost 비엄격 처리
- hybrid fusion ordering
- citation selection
- FastAPI contract
- Gradio API 연동

acceptance 기준:

- 두 FSD 케이스가 같은 FSD 문서군을 top-3 안에 올릴 것
- qualifier 단어가 후보를 0건으로 만들지 않을 것
- hybrid가 dense-only보다 top-1 정확도를 개선하거나 최소 유지할 것
- answer 성공 시 citation 1개 이상과 trace id를 남길 것

---

## 12. 구현 순서 제안

1. v4 parser 구현
2. semantic section/window index 설계
3. dense document/section 인덱스 구현
4. sparse retrieval 경로 구현
5. hybrid fusion 구현
6. answer + citation 구현
7. `/api/v4/query` + `/health`
8. Gradio UI 단순화
9. LangSmith tracing
10. benchmark 및 A/B 평가

---

## 13. 최종 권고

v4의 성공 여부는 임베딩 모델 교체보다 다음 3가지에 달려 있다.

- H1 중심 문서까지 올바르게 파싱하는가
- domain/framework를 metadata filter에서 제거하는가
- dense + sparse + RRF를 통해 qualifier 단어를 soft signal로만 처리하는가

따라서 v4의 핵심 설계 결정은 다음과 같이 고정한다.

- greenfield rewrite
- metadata 최소화
- strict filtering 제거
- semantic section 기본 단위
- local hybrid retrieval with Python-side fusion
- `text-embedding-3-small` baseline + `3-large` benchmark 검증

