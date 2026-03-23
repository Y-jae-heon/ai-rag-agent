"""응답 포맷팅 함수 모음.

각 answer_type에 맞는 텍스트 포맷을 생성한다.
LLM 호출 없이 규칙 기반으로 동작한다.
"""

from __future__ import annotations


def format_fulltext(title: str, path: str, content: str) -> str:
    """원문에 메타데이터 헤더를 추가하여 포맷팅한다.

    형식:
        ## {title}
        > 경로: {path}

        ---

        {content}

    Args:
        title: 문서 제목.
        path: 문서 파일 경로.
        content: 문서 원문 내용.

    Returns:
        헤더가 포함된 원문 문자열.
    """
    return f"## {title}\n> 경로: {path}\n\n---\n\n{content}"


def format_clarify(candidates: list[dict], question: str) -> str:
    """후보 문서 목록을 clarify 메시지로 포맷팅한다.

    형식:
        여러 문서가 검색되었습니다. 어떤 문서를 원하시나요?

        1. {title} ({domain})
        2. ...

    Args:
        candidates: 후보 문서 dict 목록. 각 dict에 "title", "domain" 키를 포함할 수 있다.
        question: 사용자 원본 질문 (현재는 미사용, 추후 확장을 위해 유지).

    Returns:
        후보 목록이 포함된 명확화 요청 메시지 문자열.
    """
    lines: list[str] = ["여러 문서가 검색되었습니다. 어떤 문서를 원하시나요?", ""]

    for idx, candidate in enumerate(candidates, start=1):
        if isinstance(candidate, dict):
            title = candidate.get("title") or candidate.get("name") or str(candidate)
            domain = candidate.get("domain")
        else:
            title = (
                getattr(candidate, "title", None)
                or getattr(candidate, "name", None)
                or str(candidate)
            )
            domain = getattr(candidate, "domain", None)

        if domain:
            lines.append(f"{idx}. {title} ({domain})")
        else:
            lines.append(f"{idx}. {title}")

    return "\n".join(lines)


def format_not_found(document_query: str | None) -> str:
    """문서를 찾지 못한 경우 안내 메시지를 반환한다.

    Args:
        document_query: 검색하려 했던 문서명 또는 쿼리 (없으면 None).

    Returns:
        문서 미발견 안내 메시지 문자열.
    """
    if document_query:
        return (
            f"`{document_query}` 문서를 찾을 수 없습니다. "
            "문서명을 다시 확인하거나 더 구체적인 키워드로 질문해 주세요."
        )
    return (
        "요청하신 문서를 찾을 수 없습니다. "
        "문서명을 다시 확인하거나 더 구체적인 키워드로 질문해 주세요."
    )
