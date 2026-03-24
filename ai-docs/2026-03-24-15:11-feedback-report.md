# RAG 검색 리스크 관련 문제지적

## 리스크 사용자 시나리오 예시

### 사용자 시나리오 A

사용자 질문: Java에서 트랜잭션 관리하는 법 알려줘
RAG 응답 시 Semantic Search 구간에 진입하지 못하고 다음과 같은 처리에서 멈추는 것을 확인

아래 코드 스니펫 로그 참조

```shell
RESOLVE STEP 1 :: None

question = 트랜잭션 관리하는 법 알려줘

understanding = intent='extract' document_query=None document_queries=None domain='backend' stack='Java' topic='트랜잭션 관리' raw_question='Java에서 트랜잭션 관리하는 법 알려줘' confidence=0.92

resolution = resolved=False canonical_doc_id=None path=None title=None confidence=0.0 resolution_strategy='unresolved' candidates=[]

handler_result = answer='요청하신 문서를 찾을 수 없습니다. 문서명을 다시 확인하거나 더 구체적인 키워드로 질문해 주세요.' answer_type='not_found' sources=[] resolved_document=None
```

- 요구되는 결과값
  Semantic Search가 들어가야하며, 트랜잭션 관련 문서가 많더라도 문서 중 유사도가 높은 문서를 찾고 답변하기를 원함
- 현재 상황
  Semantic Search 지점까지 접근하지 못하고 resolution 단계에서 종료되며 요청한 문서를 찾을 수 없다는 답변
- description:
  현재 문서는 "트랜잭션"이라는 키워드가 있는 문서는 많지만 실제 트랜잭션을 관리하는 방법에 대해서는 Kotlin(Spring) 스프링패턴 문서 [./docs/Kotlin(Spring) 스프링 패턴 321e63c6fa978063bf6cdac5931b6160.md], Typescript(NestJS) 레이어드 아키텍처 - 서비스 코드 패턴 [./docs/Typescript(NestJS) 레이어드 아키텍처 - 서비스 코드 패턴 321e63c6fa9780aebfcccd454d31c824.md] 등에 적재되어있음.

### 사용자 시나리오 B

사용자 질문: FSD 구조 규칙 알려줘
RAG 응답 시 Semantic Search 등 실제 vector DB 조회까지 정상 성공하나 요청한 문서를 찾지 못했다는 응답을 진행함

아래 코드 스니펫 로그 참조

```shell
RESOLVE STEP 1 :: FSD 구조 규칙

SEMANTIC SEARCH START
[ChromaDB] similarity_search_with_score() 호출 — query='FSD 구조 규칙', k=5, filter=None
15:17:58 [INFO] httpx — HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
[ChromaDB] similarity_search_with_score() 완료 — 결과 수=5
15:17:58 [INFO] src.convention_qa.document_resolution.semantic_retriever — [semantic_search] query='FSD 구조 규칙' | 필터=(domain=None, stack=None) | 결과 5건
15:17:58 [INFO] src.convention_qa.document_resolution.semantic_retriever —   [1] title='Git PR 템플릿'  canonical_doc_id=322e63c6fa978079af54d3d34b1fb0d2  score=0.3465  domain=frontend  stack=react
15:17:58 [INFO] src.convention_qa.document_resolution.semantic_retriever —   [2] title='FSD 레이어드 아키텍처 개요'  canonical_doc_id=325e63c6fa978067a124e0c68833a066  score=0.3413  domain=frontend  stack=react
15:17:58 [INFO] src.convention_qa.document_resolution.semantic_retriever —   [3] title='Kotlin(Spring) 테스트 코드 컨벤션'  canonical_doc_id=321e63c6fa9780348708f402e6f88dc4  score=0.3411  domain=backend  stack=spring
15:17:58 [INFO] src.convention_qa.document_resolution.semantic_retriever —   [4] title='Typescript(NestJS) 레이어드 아키텍처 - 서비스 코드 패턴'  canonical_doc_id=321e63c6fa9780aebfcccd454d31c824  score=0.3395  domain=backend  stack=nestjs
15:17:58 [INFO] src.convention_qa.document_resolution.semantic_retriever —   [5] title='Typescript(NestJS) 레이어드 아키텍처 디렉토리 구조'  canonical_doc_id=321e63c6fa978017a946c1074781b778  score=0.3391  domain=backend  stack=nestjs

question = FSD 구조 규칙 알려줘

understanding = intent='extract' document_query='FSD 구조 규칙' document_queries=None domain=None stack=None topic=None raw_question='FSD 구조 규칙 알려줘' confidence=0.85

resolution = resolved=False canonical_doc_id=None path=None title=None confidence=0.34648049164612155 resolution_strategy='semantic' candidates=[DocumentCandidate(canonical_doc_id='322e63c6fa978079af54d3d34b1fb0d2', title='Git PR 템플릿', path='docs/fe_chunk_docs/Git PR 템플릿 322e63c6fa978079af54d3d34b1fb0d2.md', score=0.34648049164612155, domain='frontend', stack='react'), DocumentCandidate(canonical_doc_id='325e63c6fa978067a124e0c68833a066', title='FSD 레이어드 아키텍처 개요', path='docs/fe_chunk_docs/FSD 레이어드 아키텍처 개요 325e63c6fa978067a124e0c68833a066.md', score=0.3412961707131824, domain='frontend', stack='react'), DocumentCandidate(canonical_doc_id='321e63c6fa9780348708f402e6f88dc4', title='Kotlin(Spring) 테스트 코드 컨벤션', path='docs/be_chunk_docs/Kotlin(Spring) 테스트 코드 컨벤션 321e63c6fa9780348708f402e6f88dc4.md', score=0.34112501610344725, domain='backend', stack='spring'), DocumentCandidate(canonical_doc_id='321e63c6fa9780aebfcccd454d31c824', title='Typescript(NestJS) 레이어드 아키텍처 - 서비스 코드 패턴', path='docs/be_chunk_docs/Typescript(NestJS) 레이어드 아키텍처 - 서비스 코드 패턴 321e63c6fa9780aebfcccd454d31c824.md', score=0.33952209293642455, domain='backend', stack='nestjs'), DocumentCandidate(canonical_doc_id='321e63c6fa978017a946c1074781b778', title='Typescript(NestJS) 레이어드 아키텍처 디렉토리 구조', path='docs/be_chunk_docs/Typescript(NestJS) 레이어드 아키텍처 디렉토리 구조 321e63c6fa978017a946c1074781b778.md', score=0.3390974920327163, domain='backend', stack='nestjs')]
```

- 요구되는 결과값
  유사도가 낮아도 맥락을 이해해서 가장 유사한 답변을 진행해야 함.
- 현재 상황
  score 점수도 생각한 것보다 낮음. 예시로 "FSD 레이어드 구조 규칙 알려줘" 와 같은 답변에서는 높은 유사도 (score = 0.9 이상)을 기록하며 응답, 그러나 "FSD Layer 구조 규칙을 알려줘", "FSD 구조 규칙을 알려줘" 라고 질문 시 0.4 아래로 떨어지며 답변하지 못하는 상황 발생, 요지는 "레이어드"라는 문서 타이틀의 키워드가 너무 명확하게 동일해야 답변하는 것을 문제 지점으로 건의
- description:
  현재 문서는 FSD 관련 문서가 [./docs/fe_chunk_docs] 에 분할되어서 보관되고 있지만 FSD 구조 규칙 등의 맥락 자체를 이해하지 못하는 현상에 대한 제어가 필요함

## 리스크 및 요구사항 분석

### RISK

1. 사용자가 시도하는 입력에서 문서에 대한 keyword가 너무 타이트하게 잡혀있는 것으로 보인다.
   - 이러한 현상은 사용자가 정확히 모르더라도 원하는 문서 내용을 빠르게 확인하는 데 pain-point가 될 가능성이 농후함.
2. 문서 명과 거의 동일 시 한 질문이어야만 답변을 한다는 점이 가장 큰 문제의 요지로 봄.
   - 원했던 RAG의 스펙과 맞지않음, 어느정도 맥락이 제공되도 유사한 문서가 나오길 원함
3. 그러나 이러한 현상을 제어할 때 이런 것이 Alias로 이중 관리되어서 풀어지길 원하지 않음
   - FSD Layer 구조 규칙을 알려줘, FSD 구조 규칙을 알려줘 등의 사용자 입력이 "레이어드"로 자동 반환되도록 지정하여 관리되기를 원하지않음. 맥락 수용에 범주
