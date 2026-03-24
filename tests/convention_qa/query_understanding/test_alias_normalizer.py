"""alias_normalizer 단위 테스트.

P2-BUG-05: 회귀 방지 및 핵심 동작 검증.
"""

from __future__ import annotations

import pytest

from src.convention_qa.query_understanding.alias_normalizer import (
    _matches_alias,
    normalize_domain,
    normalize_stack,
)


class TestMatchesAlias:
    """_matches_alias() 핵심 동작 및 회귀 테스트."""

    def test_ascii_alias_followed_by_korean_matches(self):
        """핵심 버그 회귀: re.ASCII 플래그로 한국어 앞 ASCII alias가 단어 경계에서 매칭되어야 한다."""
        assert _matches_alias("Java에서 트랜잭션", "Java") is True

    def test_ascii_alias_partial_match_prevented_ascii_suffix(self):
        """부분 일치 방지: 'Java'가 'JavaScript' 안에서 매칭되지 않아야 한다."""
        assert _matches_alias("JavaScript", "Java") is False

    def test_ascii_alias_partial_match_prevented_mixed_suffix(self):
        """부분 일치 방지: 'JavaEE에서 트랜잭션'에서 'Java'가 매칭되지 않아야 한다."""
        assert _matches_alias("JavaEE에서 트랜잭션", "Java") is False

    def test_non_ascii_alias_korean_matches(self):
        """비ASCII alias(한국어)는 단순 포함 검사로 매칭되어야 한다."""
        assert _matches_alias("스프링으로 개발", "스프링") is True


class TestNormalizeStack:
    """normalize_stack() 동작 테스트."""

    def test_java_maps_to_spring(self):
        assert normalize_stack("Java에서 트랜잭션 관리하는 법") == "spring"

    def test_kotlin_maps_to_kotlin(self):
        assert normalize_stack("Kotlin으로 테스트 작성") == "kotlin"

    def test_react_maps_to_react(self):
        assert normalize_stack("React 컴포넌트 구조") == "react"

    def test_unknown_stack_returns_none(self):
        assert normalize_stack("파이썬으로 API 만들기") is None

    def test_kotlin_spring_maps_to_kotlin(self):
        """P3-BUG-06 회귀: Kotlin(Spring) 조합은 kotlin을 반환해야 한다.

        _STACK_ALIASES에서 "kotlin" 키가 "spring" 키보다 먼저 순회되므로
        "Kotlin" alias가 먼저 매칭되어 "kotlin"을 반환한다.
        dict 순서가 바뀌면 이 테스트가 깨진다.
        """
        assert normalize_stack("Kotlin(Spring)으로 개발") == "kotlin"

    def test_java_spring_maps_to_spring(self):
        """P3-BUG-06 회귀: Java(Spring) 조합은 spring을 반환해야 한다.

        "kotlin" 키에 "Java" alias가 없으므로 "spring" 키의 "Java" alias가 매칭된다.
        """
        assert normalize_stack("Java(Spring) 프로젝트") == "spring"


class TestNormalizeDomain:
    """normalize_domain() 동작 테스트."""

    def test_fe_alias_maps_to_frontend(self):
        assert normalize_domain("FE에서 처리") == "frontend"

    def test_be_alias_maps_to_backend(self):
        assert normalize_domain("BE에서 API") == "backend"
