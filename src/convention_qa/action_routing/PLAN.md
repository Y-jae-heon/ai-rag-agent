# Module Plan: action_routing

## 역할

intent + DocumentResolutionResult를 기반으로 올바른 handler를 선택하고 실행한다.
각 handler는 독립적인 evidence loading + response generation 전략을 가진다.

## 구현할 파일

| 파일 | 역할 |
|------|------|
| `__init__.py` | 모듈 export |
| `router.py` | ActionRouter — dispatch table 기반 handler 선택 |
| `base_handler.py` | BaseHandler 추상 클래스 |
| `discover_handler.py` | 문서 메타데이터 반환 (LLM 없음) |
| `summarize_handler.py` | section_index 로딩 + summarize LLMChain |
| `extract_handler.py` | chunk_index MMR retrieval + extract LLMChain |
| `fulltext_handler.py` | 파일 직접 read + 안전 정책 (LLM 없음) |
| `clarify_handler.py` | unresolved / 다중 후보 clarify 응답 |
| `compare_handler.py` | (P2) 두 문서 비교 LLMChain |

## 핵심 클래스

```python
# base_handler.py
class BaseHandler(ABC):
    @abstractmethod
    def handle(self, context: HandlerContext) -> HandlerResult: ...

# router.py
class ActionRouter:
    HANDLER_MAP = {
        ("fulltext", True): FulltextHandler,
        ("summarize", True): SummarizeHandler,
        ("extract", True): ExtractHandler,
        ("extract", False): ExtractHandler,
        ("discover", True): DiscoverHandler,
        ("discover", False): DiscoverHandler,
    }

    def route(self, intent: str, resolved: bool) -> BaseHandler: ...
```

## LangChain 컴포넌트

### SummarizeHandler
- `Chroma(collection_name="section_index")` — 전체 섹션 수집
- `ChatOpenAI(model="gpt-4o")` + `ChatPromptTemplate` (summarize prompt)

### ExtractHandler
- `Chroma(collection_name="chunk_index")` — MMR retrieval
- `ChatOpenAI(model="gpt-4o")` + `ChatPromptTemplate` (extract prompt)

### FulltextHandler
- LangChain 사용 안 함. `open(path).read()` 전용.

## 테스트 위치

`tests/test_action_router.py`
`tests/test_handlers.py`

## 관련 티켓

P0-TK-01, P0-TK-03, P1-TK-04, P2-TK-06
