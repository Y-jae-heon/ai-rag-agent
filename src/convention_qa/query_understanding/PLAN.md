# Module Plan: query_understanding

## 역할

사용자 자연어 질문에서 구조화된 QueryUnderstandingResult를 추출한다.

## 구현할 파일

| 파일 | 역할 |
|------|------|
| `__init__.py` | 모듈 export |
| `models.py` | QueryUnderstandingResult Pydantic 모델 |
| `intent_classifier.py` | LangChain LCEL chain (ChatOpenAI + PydanticOutputParser) |
| `prompts.py` | Few-shot 분류 프롬프트 템플릿 |
| `alias_normalizer.py` | 한국어 FE/BE alias 정규화 |

## 핵심 클래스

```python
# models.py
class QueryUnderstandingResult(BaseModel):
    intent: Literal["discover", "summarize", "extract", "fulltext", "compare"]
    document_query: str | None
    domain: Literal["frontend", "backend"] | None
    stack: str | None
    topic: str | None
    raw_question: str
    confidence: float

# intent_classifier.py
class IntentClassifier:
    def classify(self, question: str, metadata: dict) -> QueryUnderstandingResult: ...
```

## LangChain 컴포넌트

- `ChatOpenAI(model="gpt-4o-mini", temperature=0)`
- `ChatPromptTemplate.from_messages([...])`
- `PydanticOutputParser(pydantic_object=QueryUnderstandingResult)`
- LCEL: `prompt | llm | parser`

## 테스트 위치

`tests/test_intent_classifier.py`

## 관련 티켓

P0-TK-01
