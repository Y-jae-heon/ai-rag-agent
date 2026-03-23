"""LangChain LCEL 기반 Intent 분류기.

ChatOpenAI + PydanticOutputParser + ChatPromptTemplate을 LCEL chain으로 조합하여
사용자 질문을 QueryUnderstandingResult로 분류한다.
alias_normalizer를 사용해 domain/stack 전처리를 수행한다.
"""

from __future__ import annotations

from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from src.convention_qa.query_understanding.alias_normalizer import (
    normalize_domain,
    normalize_stack,
)
from src.convention_qa.query_understanding.models import QueryUnderstandingResult
from src.convention_qa.query_understanding.prompts import CLASSIFICATION_PROMPT


class IntentClassifier:
    """사용자 질문을 분류하여 QueryUnderstandingResult를 반환하는 분류기.

    LangChain LCEL chain (prompt | llm | parser) 을 사용한다.
    .env 파일에서 OPENAI_API_KEY를 자동으로 로드한다.

    Example:
        classifier = IntentClassifier()
        result = classifier.classify("파일 네이밍 컨벤션 전문 보여줘")
        print(result.intent)  # "fulltext"
    """

    def __init__(self) -> None:
        load_dotenv()

        self._parser: PydanticOutputParser[QueryUnderstandingResult] = (
            PydanticOutputParser(pydantic_object=QueryUnderstandingResult)
        )

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # LCEL chain: prompt → LLM → parser
        self._chain = CLASSIFICATION_PROMPT | llm | self._parser

    def classify(
        self,
        question: str,
        metadata: dict | None = None,  # noqa: ARG002 — reserved for future use
    ) -> QueryUnderstandingResult:
        """사용자 질문을 분류하여 QueryUnderstandingResult를 반환한다.

        alias_normalizer를 통해 domain/stack을 사전 추출한 뒤,
        LLM chain에 전달하여 최종 분류 결과를 생성한다.

        Args:
            question: 사용자가 입력한 자연어 질문.
            metadata: 추가 컨텍스트 (현재 미사용, 확장을 위한 reserved 파라미터).

        Returns:
            분류 결과를 담은 QueryUnderstandingResult 인스턴스.

        Raises:
            ValidationError: LLM 응답이 파싱 불가능한 경우.
            openai.AuthenticationError: OPENAI_API_KEY가 없거나 유효하지 않은 경우.
        """
        # alias_normalizer로 domain/stack 사전 추출 (LLM 프롬프트 힌트로 활용 가능)
        pre_domain = normalize_domain(question)
        pre_stack = normalize_stack(question)

        format_instructions = self._parser.get_format_instructions()

        result: QueryUnderstandingResult = self._chain.invoke(
            {
                "question": question,
                "format_instructions": format_instructions,
            }
        )

        # alias_normalizer 결과가 있으면 LLM 결과를 보강한다
        # (LLM이 이미 잘 추출한 경우에는 덮어쓰지 않고 병합)
        if pre_domain is not None and result.domain is None:
            result = result.model_copy(update={"domain": pre_domain})

        if pre_stack is not None and result.stack is None:
            result = result.model_copy(update={"stack": pre_stack})

        # raw_question은 항상 원본 질문으로 보장
        if result.raw_question != question:
            result = result.model_copy(update={"raw_question": question})

        return result
