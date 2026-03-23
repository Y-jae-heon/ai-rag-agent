# RAG 문서 요약 및 전문 응답 실패 분석과 다음 설계 플랜

작성일: 2026-03-23
작성자: Dev
범위: 문서 전반 설명 요청과 문서 전문 출력 요청에 대해 현재 RAG가 요구사항 의도대로 동작하지 않는 원인과 후속 설계 방향

## 1. 문제 정의

현재 시스템은 다음과 같은 사용자 요청에서 기대와 다른 응답을 낸다.

- `프론트엔드 파일 네이밍 컨벤션 문서 안의 내용을 알려줘`
- `프론트엔드 파일 네이밍 컨벤션 문서 안의 내용 전문 보여줘`

사용자 기대는 다음과 같다.

- 문서명을 명시한 경우 해당 문서를 식별한다.
- `내용 알려줘`는 문서 전반의 구조와 핵심 규칙을 설명한다.
- `전문 보여줘`는 해당 문서의 원문 전체를 보여준다.

현재 실제 동작은 다음 쪽으로 기운다.

- 관련 문서명과 경로만 보여준다.
- 현재 corpus 기준으로 확인할 수 없다고 fallback 한다.
- 전문 요청을 받아도 원문을 직접 반환하지 못한다.

핵심 진단은 다음 한 문장으로 요약할 수 있다.

현재 구현은 `문서 브라우저`나 `문서 전달기`가 아니라, `retrieved chunk 근거 기반의 규칙 QA 시스템`에 가깝다.

## 2. 요구사항 의도와 현재 제품 의미의 불일치

이번 요구사항의 본질은 `질문에 답하는 것`이 아니라 `문서를 식별하고, 문서 단위로 이해하거나 전달하는 것`이다.

즉 사용자의 실제 의도는 다음 네 가지 중 하나다.

- `discover`: 어떤 문서인지 찾고 위치를 확인
- `summarize`: 문서 전반 내용 설명
- `extract`: 특정 섹션 또는 규칙만 추출
- `fulltext`: 문서 원문 전체 출력

하지만 현재 시스템은 이 요청들을 거의 모두 하나의 흐름으로 처리한다.

- 자연어 질문 입력
- query hint 추론
- chunk retrieval
- response gate 판정
- answer 또는 fallback

이 구조는 `세부 규칙 QA`에는 일정 부분 맞지만, `문서 전반 설명`과 `전문 출력`에는 맞지 않는다.

## 3. 현재 시스템이 실제로 잘하는 일

현재 구현은 아래 목적에는 비교적 적합하다.

- 특정 규칙 질의에 대해 관련 chunk를 검색
- domain, stack, topic을 보조 신호로 사용
- 약한 근거나 충돌 상황에서 보수적으로 fallback
- retrieved context만 근거로 답변 생성

관련 구현 근거:

- retrieval와 ranking: [retrieval.py](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/src/convention_qa/retrieval.py)
- 응답 상태 판정: [response_gate.py](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/src/convention_qa/response_gate.py)
- prompt 기반 answer 생성: [prompting.py](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/src/convention_qa/prompting.py)
- deterministic payload 생성: [payloads.py](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/src/convention_qa/payloads.py)

즉 현재 제품의 중심 명제는 다음과 같다.

- `찾은 근거 chunk로 확정 가능한 규칙만 말한다.`

하지만 이번 요구사항의 중심 명제는 다음과 다르다.

- `지정된 문서를 찾아 문서 전체를 설명하거나 원문 그대로 보여준다.`

## 4. 우리가 현재까지 시도한 것

현재 코드베이스에서 이미 반영했거나 명확히 시도한 방향은 다음과 같다.

### 4-1. query hint 해석 보정

- explicit frontend와 backend alias 우선순위 조정
- 한국어 FE, BE alias 확장
- `test`, `spec`, `테스트`를 domain 결정이 아니라 topic 신호로 다루도록 보정

관련 근거:

- [normalization.py](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/src/convention_qa/normalization.py)
- [tests/test_retrieval_realignment.py](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/tests/test_retrieval_realignment.py)
- [TK-G-korean-domain-alias-coverage.md](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/ai-work/tickets/TK-G-korean-domain-alias-coverage.md)

### 4-2. request metadata와 question 분리

- 운영용 metadata를 자연어 질문 본문에 합치지 않도록 정리
- prompt 입력에서 metadata를 별도 블록으로 전달

관련 근거:

- [prompting.py](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/src/convention_qa/prompting.py)
- [TK-F-request-metadata-consumption-contract.md](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/ai-work/tickets/TK-F-request-metadata-consumption-contract.md)
- [rag-test-file-retrieval-followup-dev-report-2026-03-23.md](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/ai-work/reports/rag-test-file-retrieval-followup-dev-report-2026-03-23.md)

### 4-3. 문서 path 기준 dedupe와 heading-aware metadata 보강

- 동일 문서의 여러 chunk가 top-k를 점유하지 않도록 path 기반 dedupe
- markdown heading 단위 section metadata 추출
- `section_heading`, `rule_type`, `filename_pattern` 보강

관련 근거:

- [indexing.py](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/src/convention_qa/indexing.py)
- [retrieval.py](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/src/convention_qa/retrieval.py)
- [tests/test_retrieval_realignment.py](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/tests/test_retrieval_realignment.py)
- [TK-B-document-dedupe-ranking.md](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/ai-work/tickets/TK-B-document-dedupe-ranking.md)
- [TK-C-heading-aware-metadata.md](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/ai-work/tickets/TK-C-heading-aware-metadata.md)

### 4-4. prompt와 policy를 보수적으로 유지

- retrieved context만 authority로 사용
- undocumented policy 생성 금지
- 약근거, 충돌, 스코프 불일치 시 fallback 또는 clarify

관련 근거:

- [rag-answer-policy.md](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/ai-docs/rules/rag-answer-policy.md)
- [prompt-rulebook.md](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/ai-docs/rules/prompt-rulebook.md)
- [rag-conventions-answer-system.txt](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/ai-work/prompts/rag-conventions-answer-system.txt)

## 5. 위 시도들이 무엇을 개선했고, 무엇을 개선하지 못했는가

현재까지의 시도는 분명 의미가 있었다.

- FE 질문을 BE로 오분류하는 문제를 줄였다.
- metadata 문구가 question을 오염시키는 문제를 줄였다.
- 특정 섹션 규칙 질의에서 section-level evidence를 더 잘 잡도록 만들었다.
- 같은 문서 조각이 상위 결과를 독점하는 문제를 줄였다.

하지만 이 시도들이 해결한 것은 `retrieval precision`과 `규칙 QA 안정성`이지, `문서 전반 설명`과 `전문 제공`이 아니다.

즉 현재까지의 시도는 아래 문제에는 효과가 있지만:

- `FE 파일 네이밍 컨벤션에서 Test 파일 규칙 알려줘`

아래 문제에는 본질적으로 부족하다.

- `프론트엔드 파일 네이밍 컨벤션 문서 안의 내용을 알려줘`
- `프론트엔드 파일 네이밍 컨벤션 문서 전문 보여줘`

## 6. 왜 요구사항 의도대로 가지 못하고 실패했는가

실패 원인은 retrieval tuning 부족보다 더 상위 레벨의 제품 설계 불일치다.

### 원인 A. intent를 분기하지 않았다

현재 시스템은 `문서 찾기`, `문서 요약`, `규칙 추출`, `전문 출력`을 서로 다른 작업으로 취급하지 않는다.

결과:

- 문서 전반 설명 요청도 일반 QA처럼 처리된다.
- 전문 요청도 일반 QA처럼 처리된다.
- system은 적절한 실행 경로를 선택할 수 없다.

정확한 진단 문장:

`현재 시스템은 사용자의 질문을 answer-generation 문제로만 해석하고, document-resolution 또는 file-delivery 문제로 해석하지 않는다.`

### 원인 B. retrieval 단위가 문서가 아니라 chunk 중심이다

현재 retrieval는 근본적으로 chunk 기반이다.

결과:

- 문서 전체를 대표하는 증거 세트를 안정적으로 모으기 어렵다.
- `문서 전반 설명` 요청에도 일부 excerpt만 근거로 전달된다.
- LLM은 전체 문서를 보지 못했기 때문에 문서 전반을 자신 있게 설명하기 어렵다.

정확한 진단 문장:

`문서 수준 요청에 대해 chunk 수준 retrieval만으로 대응하면서 evidence coverage가 요구사항 수준에 미달했다.`

### 원인 C. fulltext는 생성 문제가 아니라 파일 전달 문제인데, 이를 QA로 풀려고 했다

`전문 보여줘`는 원문 전체를 반환해야 하는 요구다.

하지만 현재 파이프라인은:

- 검색된 chunk를 model prompt에 넣고
- `Answer concisely`
- `Use only the retrieved context`

를 강제한다.

이 구조에서는 모델이 전문을 생성하는 순간 두 가지 문제가 생긴다.

- 실제로는 문서 전체를 받지 않았기 때문에 전문을 복원할 수 없다.
- 받은 범위를 넘는 텍스트를 생성하면 정책 위반이 된다.

정확한 진단 문장:

`fulltext requirement를 retrieval-augmented generation으로 해결하려고 시도한 것이 구조적으로 잘못된 접근이었다.`

### 원인 D. deterministic 응답 경로가 본문 설명이 아니라 문서 목록 출력에 가깝다

[payloads.py](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v2/src/convention_qa/payloads.py)의 deterministic answer는 `관련 문서: 제목 (경로)`를 반환한다.

결과:

- 사용자는 내용을 물었는데 주소만 받는다.
- 시스템은 정보를 준다고 생각하지만, 사용자 의도는 충족되지 않는다.

정확한 진단 문장:

`deterministic fallback-safe answer path가 content answer가 아니라 document listing path로 설계돼 있었다.`

### 원인 E. response gate가 재탐색보다 종료를 우선한다

현재 gate는 다음 상황에서 빠르게 fallback 또는 clarify로 전환한다.

- 약한 점수
- 스코프 불일치
- 충돌

이 판단 자체는 QA 안전성 측면에서는 타당하다. 그러나 문서 찾기나 문서 설명 제품에서는 다음 동작이 먼저여야 한다.

- 문서명 exact match 재시도
- alias match 재시도
- 문서 단위 검색 재시도
- 문서 내부 section 수집 재시도

정확한 진단 문장:

`현재 gate는 orchestration 단계가 아니라 termination 단계로 동작하고 있어, document-level recovery path를 충분히 시도하지 못한다.`

## 7. 이번 실패를 한 문장으로 정리

이번 실패는 `문서를 못 찾는 retrieval 문제`가 아니라, `문서 단위 사용자 의도를 규칙 QA 파이프라인에 억지로 태운 제품 설계 문제`다.

## 8. 다음 설계 원칙

다음 단계에서는 아래 원칙을 명시적으로 채택해야 한다.

### 원칙 1. 질문보다 의도를 먼저 분류한다

최소 intent 집합:

- `discover`
- `summarize`
- `extract`
- `fulltext`
- `compare`

### 원칙 2. 문서 식별과 답변 생성을 분리한다

파이프라인을 다음 두 단계로 분리한다.

- `document resolution`: 어떤 문서가 대상인지 확정
- `action execution`: 요약, 발췌, 전문 출력 등 의도별 실행

### 원칙 3. 문서 수준 retrieval를 1급 객체로 도입한다

검색 단위를 분리한다.

- document index
- section index
- chunk index

### 원칙 4. fulltext는 생성하지 않고 파일에서 읽어 전달한다

전문 요청은 model completion이 아니라 file-serving 경로로 처리한다.

### 원칙 5. gate는 실패 판정기보다 재시도 조정기로 쓴다

fallback 전에 recovery strategy를 먼저 실행한다.

## 9. 권장 목표 아키텍처

권장 흐름은 다음과 같다.

1. Query Understanding
   - intent classification
   - document title candidate extraction
   - domain and stack and topic hints extraction

2. Document Resolution
   - exact title match
   - alias match
   - document-level semantic retrieval
   - reranking for canonical document selection

3. Action Routing
   - discover handler
   - summarize handler
   - extract handler
   - fulltext handler
   - compare handler

4. Evidence Loading
   - full document load
   - representative section set load
   - fine-grained section load
   - chunk load only when needed

5. Response Generation or Delivery
   - summarize and extract: LLM 또는 deterministic formatter
   - fulltext: file read result direct return
   - discover: document metadata card return

6. Validation
   - wrong document suppression
   - insufficient evidence check
   - unsupported fulltext policy check

## 10. 실행 플랜

### Phase 1. 제품 계약 재정의

목표:

- 시스템이 무엇을 할 수 있는지 질문 유형별로 명시
- `요약`과 `전문`을 별도 capability로 문서화

산출물:

- feature spec 업데이트
- service policy 업데이트
- prompt spec 업데이트

핵심 문장:

`문서명 명시 질의는 우선 document-resolution flow를 타며, summary와 fulltext는 서로 다른 응답 계약을 가진다.`

### Phase 2. request schema 확장

목표:

- 자연어 question 외에 intent와 target document entity를 구조화

추가 권장 필드:

- `intent`
- `document_query`
- `document_id`
- `resolved_document_path`
- `resolution_confidence`

핵심 문장:

`question` 하나에 모든 의미를 과적재하지 말고, resolution 결과를 구조화된 필드로 후속 단계에 전달해야 한다.

### Phase 3. document index 도입

목표:

- chunk index 외에 문서 단위 인덱스를 별도로 구축

문서 메타데이터 권장 필드:

- `canonical_doc_id`
- `title`
- `aliases`
- `path`
- `domain`
- `stack`
- `topic`
- `doc_type`
- `section_headings`
- `language`

핵심 문장:

`문서 전반 설명은 chunk recall의 부산물이 아니라 document resolution의 직접 결과여야 한다.`

### Phase 4. section index 보강

목표:

- 문서 전체와 특정 규칙 요청을 모두 안정적으로 처리

section 메타데이터 권장 필드:

- `canonical_doc_id`
- `section_heading`
- `section_summary`
- `rule_type`
- `filename_pattern`
- `content_span`

### Phase 5. fulltext delivery 경로 추가

목표:

- 전문 요청 시 실제 markdown 파일 전체를 안전하게 반환

동작 규칙:

- resolved document가 1개로 확정되면 해당 path를 읽는다.
- corpus 허용 경로 안의 markdown만 fulltext 출력 허용
- unresolved 또는 다중 후보면 먼저 clarify

핵심 문장:

`fulltext는 prompt completion이 아니라 controlled file read다.`

### Phase 6. intent-specific answer policy 분리

목표:

- 같은 answer policy를 모든 요청에 적용하지 않음

정책 예시:

- `discover`: 문서명, 경로, 관련 문서
- `summarize`: 문서 구조, 핵심 규칙, 주요 섹션
- `extract`: 질문 대상 규칙과 근거 section
- `fulltext`: 원문 그대로
- `compare`: 차이점과 충돌 지점

### Phase 7. gate 재설계

목표:

- fallback 직행보다 recovery sequence 우선

권장 recovery sequence:

1. exact title lookup
2. alias lookup
3. document index semantic search
4. section index search
5. chunk search
6. clarify
7. fallback

## 11. 우선순위별 권장 티켓 분해

### P0

- intent classification과 action routing 도입
- document resolution 단계 도입
- fulltext delivery 경로 도입

### P1

- document index와 alias schema 도입
- summary 전용 representative section assembly 도입
- discover와 summarize 응답 포맷 분리

### P2

- compare intent 도입
- 문서 간 충돌 설명 개선
- section summary 자동 생성과 manifest 확장

## 12. 성공 기준

다음 질문들이 아래처럼 동작해야 한다.

### 케이스 A

질문:

- `프론트엔드 파일 네이밍 컨벤션 문서 안의 내용을 알려줘`

성공 기준:

- target document를 정확히 식별
- 문서 전반 구조를 3~6개 핵심 항목으로 요약
- 주요 파일 규칙과 대표 section을 포함

### 케이스 B

질문:

- `프론트엔드 파일 네이밍 컨벤션 문서 안의 내용 전문 보여줘`

성공 기준:

- target document를 정확히 식별
- 실제 markdown 원문 전체를 반환
- 요약 응답이나 citation-only 응답으로 대체하지 않음

### 케이스 C

질문:

- `프론트엔드 파일 네이밍 컨벤션 문서에서 Test 파일 규칙만 알려줘`

성공 기준:

- 해당 문서의 `Test 파일` section을 우선 근거로 사용
- `{kebab-case}.spec.ts`와 예시를 제시
- 다른 backend 테스트 문서로 오염되지 않음

## 13. 최종 결론

현재까지의 시도는 retrieval 품질 개선 측면에서는 유효했다. 그러나 이번 요구사항 실패의 본질은 retrieval tuning의 부족이 아니다.

본질은 다음과 같다.

- 제품이 `규칙 QA 시스템`으로 설계되어 있음
- 사용자는 `문서 탐색 + 문서 요약 + 문서 전문 제공`을 기대함
- 두 제품 의미가 다르기 때문에, 일부 retrieval 개선으로는 요구사항을 충족할 수 없음

따라서 다음 단계의 핵심은 `더 잘 찾는 RAG`가 아니라, `document-resolution + intent-specific execution` 아키텍처로의 전환이다.
