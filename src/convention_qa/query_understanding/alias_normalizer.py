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

# NOTE: normalize_stack()은 first-match-wins 방식이다.
# "kotlin"이 "spring"보다 먼저 와야 한다.
# "Kotlin(Spring)으로 개발" 입력 시 "Kotlin" alias가 먼저 매칭되어 "kotlin"을 반환한다.
# 이 순서를 변경하면 test_kotlin_spring_maps_to_kotlin 이 실패한다.
_STACK_ALIASES: dict[str, list[str]] = {
    "kotlin": [
        "코틀린",
        "Kotlin",
        "kotlin",
        # "Kotlin(Spring)", "kotlin(spring)" 는 \b가 ) 뒤에서 미성립하여 영구 미매칭 → 제거 (P3-BUG-06)
    ],
    "spring": [
        "스프링",
        "Spring",
        "spring",
        "자바",
        "Java",
        "java",
        # "Java(Spring)", "java(spring)" 는 \b가 ) 뒤에서 미성립하여 영구 미매칭 → 제거 (P3-BUG-06)
    ],
    "nestjs": [
        "NestJS",
        "nestjs",
        "Nest",
        "nest",
        "네스트",
        "네스트JS",
        "네스트js",
        # "Typescript(NestJS)", "typescript(nestjs)" 는 \b가 ) 뒤에서 미성립하여 영구 미매칭 → 제거 (P3-BUG-06)
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

    Note:
        ASCII alias 매칭에 re.ASCII 플래그를 사용한다.
        기본 유니코드 모드에서는 한국어 글자도 \\w로 분류되어
        "Java에서" 같은 입력에서 'a'와 '에' 사이에 \\b가 성립하지 않는 문제가 있다.
        re.ASCII 적용 시 \\w = [a-zA-Z0-9_]로 제한되어 '에'가 \\W로 분류되고
        단어 경계가 올바르게 동작한다. (P1-BUG-02 참조)
    """
    if alias.isascii():
        # 영문/숫자 alias는 단어 경계 매칭 (대소문자 구분)
        pattern = r"\b" + re.escape(alias) + r"\b"
        return bool(re.search(pattern, text, re.ASCII))
    else:
        # 한국어 등 비ASCII alias는 단순 포함 검사
        return alias in text
