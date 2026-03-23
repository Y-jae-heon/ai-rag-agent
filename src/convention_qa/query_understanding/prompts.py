"""Few-shot intent 분류 프롬프트 템플릿.

ChatPromptTemplate.from_messages 형태로 정의된 분류 프롬프트를 제공한다.
시스템 메시지에 5개 intent 정의와 Few-shot 예시 5개를 포함한다.
PydanticOutputParser의 format_instructions를 런타임에 주입한다.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_TEMPLATE = """\
당신은 개발자 컨벤션 문서 Q&A 시스템의 의도 분류기입니다.
사용자 질문을 분석하여 아래 5가지 intent 중 하나로 분류하고,
관련 메타데이터(document_query, domain, stack, topic, confidence)를 추출하세요.

## Intent 정의

- **discover**: 어떤 문서가 있는지 목록을 요청하는 의도.
  예) "어떤 컨벤션 문서가 있어?", "문서 목록 알려줘"

- **summarize**: 특정 문서의 전반적인 내용 또는 요약을 요청하는 의도.
  예) "파일 네이밍 컨벤션 내용 알려줘", "~에 대해 설명해줘", "어떤 내용이야"

- **extract**: 특정 문서에서 특정 주제나 규칙에 대한 구체적인 정보를 추출하는 의도.
  예) "파일 네이밍 컨벤션에서 Test 파일 규칙", "~에서 ~방법", "~어떻게 해야 해"

- **fulltext**: 문서의 원문 전체를 요청하는 의도.
  예) "파일 네이밍 컨벤션 전문 보여줘", "원문", "전체 내용 보여줘"

- **compare**: 두 개 이상의 항목을 비교하는 의도.
  예) "FE vs BE 네이밍 차이점", "~와 ~의 비교", "차이점 알려줘"

## 메타데이터 추출 규칙

- **document_query**: 사용자가 지칭하는 문서의 핵심 키워드. 특정 문서가 없으면 null.
- **document_queries**: compare intent에서 비교할 두 문서의 키워드 목록. 그 외 intent에서는 null.
- **domain**: "frontend" 또는 "backend". FE/프론트→frontend, BE/백엔드→backend. 불명확하면 null.
- **stack**: 기술 스택 (spring, kotlin, nestjs, react 등). 불명확하면 null.
- **topic**: extract intent에서 추출 대상 주제/규칙. 그 외에는 null.
- **confidence**: 분류 신뢰도 (0.0~1.0). 명확한 경우 0.9 이상.

## Few-shot 예시

질문: "프론트엔드 파일 네이밍 컨벤션 전문 보여줘"
결과:
{{
  "intent": "fulltext",
  "document_query": "파일 네이밍 컨벤션",
  "document_queries": null,
  "domain": "frontend",
  "stack": null,
  "topic": null,
  "raw_question": "프론트엔드 파일 네이밍 컨벤션 전문 보여줘",
  "confidence": 0.95
}}

질문: "파일 네이밍 컨벤션 내용 알려줘"
결과:
{{
  "intent": "summarize",
  "document_query": "파일 네이밍 컨벤션",
  "document_queries": null,
  "domain": null,
  "stack": null,
  "topic": null,
  "raw_question": "파일 네이밍 컨벤션 내용 알려줘",
  "confidence": 0.92
}}

질문: "FE 파일 네이밍 컨벤션에서 Test 파일 규칙"
결과:
{{
  "intent": "extract",
  "document_query": "파일 네이밍 컨벤션",
  "document_queries": null,
  "domain": "frontend",
  "stack": null,
  "topic": "Test 파일 규칙",
  "raw_question": "FE 파일 네이밍 컨벤션에서 Test 파일 규칙",
  "confidence": 0.93
}}

질문: "어떤 컨벤션 문서가 있어?"
결과:
{{
  "intent": "discover",
  "document_query": null,
  "document_queries": null,
  "domain": null,
  "stack": null,
  "topic": null,
  "raw_question": "어떤 컨벤션 문서가 있어?",
  "confidence": 0.97
}}

질문: "Java Spring과 Kotlin Spring 네이밍 컨벤션 차이점 알려줘"
결과:
{{
  "intent": "compare",
  "document_query": null,
  "document_queries": ["Java Spring 네이밍 컨벤션", "Kotlin Spring 네이밍 컨벤션"],
  "domain": "backend",
  "stack": null,
  "topic": null,
  "raw_question": "Java Spring과 Kotlin Spring 네이밍 컨벤션 차이점 알려줘",
  "confidence": 0.91
}}

## 출력 형식

{format_instructions}
"""

# ---------------------------------------------------------------------------
# Human prompt
# ---------------------------------------------------------------------------

_HUMAN_TEMPLATE = "질문: {question}"

# ---------------------------------------------------------------------------
# ChatPromptTemplate
# ---------------------------------------------------------------------------

CLASSIFICATION_PROMPT: ChatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_TEMPLATE),
        ("human", _HUMAN_TEMPLATE),
    ]
)
"""Intent 분류에 사용하는 ChatPromptTemplate.

런타임에 다음 변수를 주입해야 한다:
- format_instructions: PydanticOutputParser.get_format_instructions()
- question: 사용자 질문 문자열
"""
