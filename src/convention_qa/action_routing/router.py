"""ActionRouter — intent + resolved 기반 handler dispatch.

(intent, resolved) 키 조합으로 적절한 BaseHandler를 선택하여 반환한다.
P0 단계에서는 fulltext와 clarify만 실제 구현되어 있으며,
나머지 intent(summarize, extract, discover)는 ClarifyHandler로 fallback한다.
"""

from __future__ import annotations

from src.convention_qa.action_routing.base_handler import (
    BaseHandler,
    HandlerContext,
    HandlerResult,
)
from src.convention_qa.action_routing.clarify_handler import ClarifyHandler
from src.convention_qa.action_routing.fulltext_handler import FulltextHandler
from langsmith import traceable


class ActionRouter:
    """intent + resolved 조합으로 handler를 선택하는 라우터.

    HANDLER_MAP에 등록된 (intent, resolved) 키에 해당하는 handler 클래스를
    인스턴스화하여 반환한다.

    P1 단계 구현 상태:
    - fulltext + resolved=True: FulltextHandler
    - summarize + resolved=True: SummarizeHandler
    - extract + resolved=True/False: ExtractHandler
    - discover + resolved=True/False: DiscoverHandler
    - 매핑에 없는 경우: ClarifyHandler fallback

    Example:
        router = ActionRouter()
        handler = router.route("fulltext", resolved=True)
        result = handler.handle(context)
    """

    # handler 문자열 이름 매핑
    HANDLER_MAP: dict[tuple[str, bool], str] = {
        ("fulltext", True): "FulltextHandler",
        ("summarize", True): "SummarizeHandler",
        ("extract", True): "ExtractHandler",
        ("extract", False): "ExtractHandler",
        ("discover", True): "DiscoverHandler",
        ("discover", False): "DiscoverHandler",
        ("compare", True): "CompareHandler",
        ("compare", False): "CompareHandler",
    }

    def route(self, intent: str, resolved: bool) -> BaseHandler:
        """(intent, resolved) 조합에 맞는 BaseHandler 인스턴스를 반환한다.

        P0 단계에서는 fulltext(resolved=True) 외 모든 경우
        ClarifyHandler로 fallback한다.
        resolved=False이거나 매핑에 없는 intent는 항상 ClarifyHandler를 반환한다.

        Args:
            intent: 분류된 intent 문자열.
                    (discover/summarize/extract/fulltext/compare)
            resolved: DocumentResolutionResult.resolved 값.

        Returns:
            선택된 BaseHandler 인스턴스.
        """
        # resolved=False이면 문서 미해결이므로 항상 ClarifyHandler
        if not resolved:
            # discover는 resolved 여부와 무관하게 동작 가능하나, P0에서는 stub
            if intent not in ("discover", "extract", "compare"):
                return ClarifyHandler()

        handler_name = self.HANDLER_MAP.get((intent, resolved))

        if handler_name is None:
            # 매핑에 없는 (intent, resolved) 조합 → ClarifyHandler fallback
            return ClarifyHandler()

        return self._instantiate(handler_name)

    def _instantiate(self, handler_name: str) -> BaseHandler:
        """handler_name에 해당하는 BaseHandler 인스턴스를 생성한다.

        P0 단계에서는 FulltextHandler를 제외한 모든 handler가
        ClarifyHandler로 fallback한다.

        Args:
            handler_name: HANDLER_MAP에 등록된 handler 클래스명 문자열.

        Returns:
            BaseHandler 인스턴스.
        """
        if handler_name == "FulltextHandler":
            return FulltextHandler()

        if handler_name == "SummarizeHandler":
            from src.convention_qa.action_routing.summarize_handler import SummarizeHandler  # noqa: PLC0415
            return SummarizeHandler()

        if handler_name == "ExtractHandler":
            from src.convention_qa.action_routing.extract_handler import ExtractHandler  # noqa: PLC0415
            return ExtractHandler()

        if handler_name == "DiscoverHandler":
            from src.convention_qa.action_routing.discover_handler import DiscoverHandler  # noqa: PLC0415
            return DiscoverHandler()

        if handler_name == "CompareHandler":
            from src.convention_qa.action_routing.compare_handler import CompareHandler  # noqa: PLC0415
            return CompareHandler()

        return ClarifyHandler()

    @traceable
    def route_and_execute(
        self,
        understanding: "QueryUnderstandingResult",
        resolution: "DocumentResolutionResult",
        question: str,
    ) -> HandlerResult:
        """handler 선택 + execute를 한 번에 처리하는 편의 메서드.

        Args:
            understanding: 질문 분류 결과. intent 필드를 참조한다.
            resolution: 문서 해결 결과. resolved 필드를 참조한다.
            question: 사용자 원본 질문.

        Returns:
            선택된 handler가 처리한 HandlerResult.
        """
        from src.convention_qa.document_resolution.models import DocumentResolutionResult  # noqa: PLC0415
        from src.convention_qa.query_understanding.models import QueryUnderstandingResult  # noqa: PLC0415

        handler = self.route(understanding.intent, resolution.resolved)
        context = HandlerContext(
            question=question,
            intent=understanding.intent,
            resolution=resolution,
            understanding=understanding,
        )
        return handler.handle(context)
