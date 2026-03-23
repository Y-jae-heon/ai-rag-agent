"""action_routing 패키지.

intent와 DocumentResolutionResult를 기반으로 올바른 handler를 선택하고
실행하는 ActionRouter와 BaseHandler를 제공한다.
"""

from src.convention_qa.action_routing.base_handler import (
    BaseHandler,
    HandlerContext,
    HandlerResult,
)
from src.convention_qa.action_routing.clarify_handler import ClarifyHandler
from src.convention_qa.action_routing.discover_handler import DiscoverHandler
from src.convention_qa.action_routing.extract_handler import ExtractHandler
from src.convention_qa.action_routing.router import ActionRouter
from src.convention_qa.action_routing.summarize_handler import SummarizeHandler

__all__ = [
    "ActionRouter",
    "BaseHandler",
    "HandlerContext",
    "HandlerResult",
    "ClarifyHandler",
    "SummarizeHandler",
    "ExtractHandler",
    "DiscoverHandler",
]
