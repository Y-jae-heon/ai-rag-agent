"""convention_qa response 패키지.

QueryResponse, SourceRef 모델과 응답 포맷팅 함수를 제공한다.
"""

from .formatters import format_clarify, format_fulltext, format_not_found
from .models import QueryResponse, SourceRef

__all__ = [
    "QueryResponse",
    "SourceRef",
    "format_fulltext",
    "format_clarify",
    "format_not_found",
]
