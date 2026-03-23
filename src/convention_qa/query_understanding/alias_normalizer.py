"""한국어/영어 FE/BE alias 정규화 유틸리티.

사용자 입력에 포함된 도메인(frontend/backend) 및 기술 스택 관련 별칭을
표준 형태로 정규화한다.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Domain alias mapping
# ---------------------------------------------------------------------------

_FRONTEND_ALIASES: list[str] = [
    "FE",
    "fe",
    "프론트엔드",
    "프론트",
    "frontend",
    "front-end",
    "front",
]

_BACKEND_ALIASES: list[str] = [
    "BE",
    "be",
    "백엔드",
    "백",
    "backend",
    "back-end",
    "back",
]

# ---------------------------------------------------------------------------
# Stack alias mapping
# ---------------------------------------------------------------------------

_STACK_ALIASES: dict[str, list[str]] = {
    "spring": [
        "스프링",
        "Spring",
        "spring",
        "자바",
        "Java",
        "java",
        "Java(Spring)",
        "java(spring)",
    ],
    "kotlin": [
        "코틀린",
        "Kotlin",
        "kotlin",
        "Kotlin(Spring)",
        "kotlin(spring)",
    ],
    "nestjs": [
        "NestJS",
        "nestjs",
        "Nest",
        "nest",
        "네스트",
        "네스트JS",
        "네스트js",
        "Typescript(NestJS)",
        "typescript(nestjs)",
    ],
    "react": [
        "React",
        "react",
        "리액트",
    ],
}


def normalize_domain(text: str) -> str | None:
    """텍스트에서 도메인 alias를 감지하여 "frontend" 또는 "backend"로 정규화한다.

    Args:
        text: 사용자 입력 문자열 (단어 또는 문장).

    Returns:
        "frontend", "backend", 또는 None (감지 불가).
    """
    # 정확한 단어 경계 매칭을 위해 공백/구두점으로 분리된 토큰을 사용한다.
    # 단어 경계가 없는 언어(한국어)를 위해 포함(in) 검사도 병행한다.
    for alias in _FRONTEND_ALIASES:
        if _matches_alias(text, alias):
            return "frontend"

    for alias in _BACKEND_ALIASES:
        if _matches_alias(text, alias):
            return "backend"

    return None


def normalize_stack(text: str) -> str | None:
    """텍스트에서 기술 스택 alias를 감지하여 표준 스택명으로 정규화한다.

    Args:
        text: 사용자 입력 문자열 (단어 또는 문장).

    Returns:
        "spring", "kotlin", "nestjs", "react", 또는 None (감지 불가).
    """
    for canonical, aliases in _STACK_ALIASES.items():
        for alias in aliases:
            if _matches_alias(text, alias):
                return canonical

    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _matches_alias(text: str, alias: str) -> bool:
    """텍스트 내에서 alias가 단어 단위로 존재하는지 확인한다.

    ASCII alias는 단어 경계(\b) 매칭을, 한국어/비ASCII alias는
    단순 포함(in) 검사를 사용한다.

    Args:
        text: 검색 대상 문자열.
        alias: 감지할 alias 문자열.

    Returns:
        alias가 텍스트에 포함되어 있으면 True.
    """
    if alias.isascii():
        # 영문/숫자 alias는 단어 경계 매칭 (대소문자 구분)
        pattern = r"\b" + re.escape(alias) + r"\b"
        return bool(re.search(pattern, text))
    else:
        # 한국어 등 비ASCII alias는 단순 포함 검사
        return alias in text
