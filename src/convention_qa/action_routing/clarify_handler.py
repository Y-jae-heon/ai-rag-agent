"""ClarifyHandler — 문서 미해결 또는 다중 후보 상황에서 명확화 응답을 생성.

DocumentResolutionResult가 unresolved이거나 후보 문서가 여러 개일 때,
사용자에게 명확화를 요청하는 응답을 반환한다.
"""

from __future__ import annotations

from src.convention_qa.action_routing.base_handler import (
    BaseHandler,
    HandlerContext,
    HandlerResult,
)


class ClarifyHandler(BaseHandler):
    """문서 미해결 또는 다중 후보 상황 처리 핸들러.

    resolution.resolved가 False이거나 candidates가 여러 개인 경우
    사용자에게 명확화를 요청하는 텍스트 응답을 생성한다.

    LLM을 사용하지 않으며 규칙 기반으로 응답을 구성한다.
    """

    def handle(self, context: HandlerContext) -> HandlerResult:
        """HandlerContext를 분석하여 명확화 응답을 생성한다.

        Args:
            context: handler 실행 컨텍스트. resolution 필드를 참조한다.

        Returns:
            answer_type="clarify"인 HandlerResult.
        """
        resolution = context.resolution

        # resolution 객체의 resolved 속성 확인
        resolved: bool = getattr(resolution, "resolved", False)

        if not resolved:
            # 후보 목록이 있으면 나열
            candidates: list = getattr(resolution, "candidates", [])

            if candidates:
                answer = self._build_candidates_message(candidates)
            else:
                answer = (
                    "요청하신 문서를 찾을 수 없습니다. "
                    "문서명을 다시 확인하거나 더 구체적인 키워드로 질문해 주세요."
                )
        else:
            # resolved=True인데 ClarifyHandler로 라우팅된 경우 (예외적 상황)
            candidates = getattr(resolution, "candidates", [])
            if len(candidates) > 1:
                answer = self._build_candidates_message(candidates)
            else:
                answer = (
                    "요청을 처리하는 중 문제가 발생했습니다. "
                    "질문을 더 구체적으로 입력해 주세요."
                )

        return HandlerResult(
            answer=answer,
            answer_type="clarify",
            sources=[],
            resolved_document=None,
        )

    @staticmethod
    def _build_candidates_message(candidates: list) -> str:
        """후보 문서 목록을 나열하는 명확화 메시지를 생성한다.

        Args:
            candidates: 후보 문서 목록. 각 항목은 dict 또는 속성을 가진 객체.

        Returns:
            후보 목록이 포함된 안내 메시지 문자열.
        """
        lines: list[str] = [
            "여러 문서가 검색되었습니다. 아래 중 어떤 문서를 원하시나요?\n"
        ]

        for idx, candidate in enumerate(candidates, start=1):
            if isinstance(candidate, dict):
                name = candidate.get("name") or candidate.get("title") or str(candidate)
            else:
                name = (
                    getattr(candidate, "name", None)
                    or getattr(candidate, "title", None)
                    or str(candidate)
                )
            lines.append(f"  {idx}. {name}")

        lines.append("\n원하시는 문서 번호나 이름을 알려주세요.")
        return "\n".join(lines)
