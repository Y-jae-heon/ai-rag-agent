# P0-TK-01: Intent Classification & Action Routing 도입

우선순위: P0
작성일: 2026-03-23
관련 플랜: ai-work/plans/architecture-v3.md §[1], §[3]

## 배경

v2에서 모든 질문이 단일 QA 파이프라인으로 처리되어 문서 요약/전문 요청이 실패했다.
v3의 핵심 전환: 질문보다 의도를 먼저 분류하고 intent-specific 경로로 분기한다.

## 목표

- 사용자 쿼리에서 intent를 분류하는 모듈 구현
- intent 결과에 따라 올바른 handler로 라우팅하는 ActionRouter 구현
- 5개 intent(discover/summarize/extract/fulltext/compare) 지원

## 범위

### 구현 대상

**`src/convention_qa/query_understanding/`**
- `intent_classifier.py`: LangChain LCEL chain (ChatOpenAI + PydanticOutputParser)
- `models.py`: `QueryUnderstandingResult` Pydantic 모델
- `prompts.py`: few-shot 분류 프롬프트 (케이스 A/B/C 포함)

**`src/convention_qa/action_routing/`**
- `router.py`: intent + resolved 기반 handler dispatch
- `base_handler.py`: `BaseHandler` 추상 클래스
- `clarify_handler.py`: unresolved / multi-candidate 응답

### 구현 제외 (다른 티켓)
- document-resolver 연동 (TK-02)
- 실제 handler 로직 (TK-02, TK-03 이후)

## 입출력 계약

### QueryUnderstandingResult
```python
class QueryUnderstandingResult(BaseModel):
    intent: Literal["discover", "summarize", "extract", "fulltext", "compare"]
    document_query: str | None
    domain: Literal["frontend", "backend"] | None
    stack: str | None
    topic: str | None
    raw_question: str
    confidence: float
```

## 테스트 케이스

| 입력 | 기대 intent | 기대 document_query |
|------|------------|---------------------|
| "프론트엔드 파일 네이밍 컨벤션 전문 보여줘" | fulltext | "파일 네이밍 컨벤션" |
| "파일 네이밍 컨벤션 내용 알려줘" | summarize | "파일 네이밍 컨벤션" |
| "FE 파일 네이밍 컨벤션에서 Test 파일 규칙" | extract | "파일 네이밍 컨벤션" |
| "어떤 컨벤션 문서가 있어?" | discover | null |
| "FE vs BE 네이밍 차이점" | compare | null |

## 완료 기준

- [ ] `intent_classifier.py` 구현 + 단위 테스트 통과
- [ ] 위 5개 테스트 케이스 전원 통과
- [ ] 한국어 FE/BE alias 분류 정확도 95% 이상 (테스트셋 20개)
- [ ] `router.py` dispatch 테이블 구현 완료
