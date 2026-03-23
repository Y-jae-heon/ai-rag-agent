# Module Plan: response

## 역할

각 handler의 결과를 intent별 응답 포맷으로 변환한다.
summarize/extract는 LLM chain 프롬프트도 이 모듈에서 관리한다.

## 구현할 파일

| 파일 | 역할 |
|------|------|
| `__init__.py` | 모듈 export |
| `models.py` | QueryResponse, SourceRef Pydantic 모델 |
| `formatters.py` | intent별 결정적 포맷터 (discover, fulltext, clarify) |
| `prompts/summarize_prompt.txt` | SummarizeHandler용 system prompt |
| `prompts/extract_prompt.txt` | ExtractHandler용 system prompt |
| `prompts/compare_prompt.txt` | CompareHandler용 system prompt (P2) |

## 핵심 모델

```python
# models.py
class SourceRef(BaseModel):
    canonical_doc_id: str
    title: str
    section: str | None
    excerpt: str | None

class QueryResponse(BaseModel):
    answer: str
    answer_type: Literal["fulltext", "summary", "extract", "discover", "clarify"]
    resolved_document: dict | None
    sources: list[SourceRef]
    intent: str
```

## LangChain 컴포넌트

### summarize 응답 chain
```
ChatPromptTemplate(summarize_prompt) | ChatOpenAI(gpt-4o) | StrOutputParser()
```

### extract 응답 chain
```
ChatPromptTemplate(extract_prompt) | ChatOpenAI(gpt-4o) | StrOutputParser()
```

## Prompt 설계 원칙

- retrieved context만 authority (rag-answer-policy.md 준수)
- undocumented policy 생성 금지
- 섹션 출처 명시
- summarize: 3~6개 핵심 항목 형식으로 구조화
- extract: 근거 섹션 인용 포함

## 관련 티켓

P1-TK-05
