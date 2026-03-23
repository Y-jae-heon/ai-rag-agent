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


def format_summarize(title: str, summary: str, path: str) -> str:
    """LLM 요약 결과에 메타데이터 헤더와 출처를 추가하여 포맷팅한다.

    형식:
        ## {title} 요약

        {summary}

        > 출처: {title} ({path})

    Args:
        title: 문서 제목.
        summary: LLM이 생성한 요약 텍스트.
        path: 문서 파일 경로.

    Returns:
        헤더와 출처가 포함된 요약 문자열.
    """
    header = f"## {title} 요약\n\n" if title else "## 요약\n\n"
    footer = f"\n\n> 출처: {title} (`{path}`)" if path else ""
    return f"{header}{summary}{footer}"


def format_discover(
    title: str,
    path: str,
    domain: str | None,
    stack: str | None,
    section_headings: list[str],
) -> str:
    """문서 발견 결과를 구조화된 포맷으로 반환한다.

    형식:
        ## 문서 발견 결과

        **제목**: {title}
        **경로**: {path}
        **도메인**: {domain} / {stack}
        **주요 섹션**: {headings}

    Args:
        title: 문서 제목.
        path: 문서 파일 경로.
        domain: 도메인 (frontend/backend).
        stack: 기술 스택 (react/java/kotlin/nestjs).
        section_headings: 문서의 섹션 헤딩 목록.

    Returns:
        구조화된 문서 발견 결과 문자열.
    """
    lines: list[str] = ["## 문서 발견 결과", ""]
    if title:
        lines.append(f"**제목**: {title}")
    if path:
        lines.append(f"**경로**: `{path}`")
    if domain or stack:
        domain_str = domain.capitalize() if domain else ""
        stack_str = stack.upper() if stack and len(stack) <= 4 else (stack.capitalize() if stack else "")
        lines.append(f"**도메인**: {domain_str} / {stack_str}".rstrip(" /"))
    if section_headings:
        headings_str = ", ".join(h.lstrip("#").strip() for h in section_headings[:6])
        lines.append(f"**주요 섹션**: {headings_str}")
    return "\n".join(lines)


def format_extract(
    title: str,
    answer_text: str,
    source_sections: list[str],
    path: str,
) -> str:
    """QA 추출 답변에 출처 정보를 추가하여 포맷팅한다.

    형식:
        {answer_text}

        > 근거: {title} §{section1}, §{section2} ...

    Args:
        title: 문서 제목.
        answer_text: LLM이 생성한 QA 답변 텍스트.
        source_sections: 참조한 섹션 헤딩 목록.
        path: 문서 파일 경로.

    Returns:
        출처가 포함된 QA 답변 문자열.
    """
    if source_sections:
        sections_str = ", ".join(
            f"§{s.lstrip('#').strip()}" for s in source_sections[:3] if s
        )
        footer = f"\n\n> 근거: {title} {sections_str}" if sections_str else f"\n\n> 근거: {title}"
    else:
        footer = f"\n\n> 근거: {title}" if title else ""
    return f"{answer_text}{footer}"


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
