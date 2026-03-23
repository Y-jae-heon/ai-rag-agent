"""DiscoverHandler 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.convention_qa.action_routing.base_handler import HandlerContext
from src.convention_qa.action_routing.discover_handler import DiscoverHandler


@pytest.fixture
def handler():
    return DiscoverHandler()


def make_candidate(title="테스트 문서", domain="frontend", stack="react"):
    candidate = MagicMock()
    candidate.title = title
    candidate.domain = domain
    candidate.stack = stack
    return candidate


@pytest.fixture
def resolved_resolution():
    candidate = make_candidate()
    resolution = MagicMock()
    resolution.resolved = True
    resolution.canonical_doc_id = "test_doc_id"
    resolution.title = "테스트 문서"
    resolution.path = "docs/test.md"
    resolution.candidates = [candidate]
    return resolution


@pytest.fixture
def unresolved_resolution():
    c1 = make_candidate(title="문서 A", domain="frontend")
    c2 = make_candidate(title="문서 B", domain="backend")
    resolution = MagicMock()
    resolution.resolved = False
    resolution.canonical_doc_id = None
    resolution.title = None
    resolution.path = None
    resolution.candidates = [c1, c2]
    return resolution


class TestHandleResolved:
    """resolution.resolved=True일 때의 동작 테스트."""

    def test_handle_resolved(self, handler, resolved_resolution):
        """resolved=True이고 섹션 헤딩이 있을 때 answer_type='discover'를 반환해야 한다."""
        headings = ["## 네이밍 규칙", "## 파일 구조", "## 컴포넌트 작성"]

        with patch.object(handler, "_get_section_headings", return_value=headings) as mock_headings:
            context = HandlerContext(
                question="React 컨벤션 문서가 뭐야?",
                intent="discover",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        mock_headings.assert_called_once_with("test_doc_id")

        assert result.answer_type == "discover"
        assert result.sources == [{"path": "docs/test.md", "title": "테스트 문서"}]
        assert result.resolved_document is not None
        assert result.resolved_document["canonical_doc_id"] == "test_doc_id"
        assert result.resolved_document["title"] == "테스트 문서"
        assert result.resolved_document["path"] == "docs/test.md"

    def test_handle_resolved_answer_contains_title(self, handler, resolved_resolution):
        """resolved 응답의 answer에 문서 제목이 포함되어야 한다."""
        with patch.object(handler, "_get_section_headings", return_value=["## 섹션1"]):
            context = HandlerContext(
                question="문서 찾아줘",
                intent="discover",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        assert "테스트 문서" in result.answer

    def test_handle_resolved_answer_contains_path(self, handler, resolved_resolution):
        """resolved 응답의 answer에 경로 정보가 포함되어야 한다."""
        with patch.object(handler, "_get_section_headings", return_value=[]):
            context = HandlerContext(
                question="문서 찾아줘",
                intent="discover",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        assert "docs/test.md" in result.answer

    def test_handle_resolved_answer_contains_headings(self, handler, resolved_resolution):
        """resolved 응답의 answer에 섹션 헤딩 정보가 포함되어야 한다."""
        headings = ["## 네이밍 규칙", "## 파일 구조"]

        with patch.object(handler, "_get_section_headings", return_value=headings):
            context = HandlerContext(
                question="문서 찾아줘",
                intent="discover",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        assert "네이밍 규칙" in result.answer
        assert "파일 구조" in result.answer

    def test_handle_resolved_uses_candidate_domain_and_stack(self, handler, resolved_resolution):
        """resolved 응답에 candidates[0]의 domain과 stack이 사용되어야 한다."""
        with patch.object(handler, "_get_section_headings", return_value=[]):
            context = HandlerContext(
                question="문서 찾아줘",
                intent="discover",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        # resolved_resolution의 candidates[0]는 domain="frontend", stack="react"
        assert "Frontend" in result.answer or "frontend" in result.answer
        assert "REACT" in result.answer or "React" in result.answer or "react" in result.answer


class TestHandleResolvedNoHeadings:
    """resolved=True이지만 섹션 헤딩이 없는 경우의 동작 테스트."""

    def test_handle_resolved_no_headings(self, handler, resolved_resolution):
        """헤딩이 없어도 answer_type='discover'로 정상 처리되어야 한다."""
        with patch.object(handler, "_get_section_headings", return_value=[]) as mock_headings:
            context = HandlerContext(
                question="문서 찾아줘",
                intent="discover",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        mock_headings.assert_called_once_with("test_doc_id")
        assert result.answer_type == "discover"
        assert result.answer is not None

    def test_handle_resolved_no_headings_answer_still_has_title_and_path(self, handler, resolved_resolution):
        """헤딩이 없어도 answer에는 제목과 경로가 포함되어야 한다."""
        with patch.object(handler, "_get_section_headings", return_value=[]):
            context = HandlerContext(
                question="문서 찾아줘",
                intent="discover",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        assert "테스트 문서" in result.answer
        assert "docs/test.md" in result.answer

    def test_handle_resolved_no_headings_sources_populated(self, handler, resolved_resolution):
        """헤딩이 없어도 sources에는 문서 정보가 들어있어야 한다."""
        with patch.object(handler, "_get_section_headings", return_value=[]):
            context = HandlerContext(
                question="문서 찾아줘",
                intent="discover",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        assert len(result.sources) == 1
        assert result.sources[0]["title"] == "테스트 문서"
        assert result.sources[0]["path"] == "docs/test.md"

    def test_handle_resolved_no_candidates(self, handler):
        """candidates가 빈 리스트일 때 domain/stack 없이 정상 처리되어야 한다."""
        resolution = MagicMock()
        resolution.resolved = True
        resolution.canonical_doc_id = "doc_no_candidate"
        resolution.title = "후보 없는 문서"
        resolution.path = "docs/no_candidate.md"
        resolution.candidates = []

        with patch.object(handler, "_get_section_headings", return_value=[]):
            context = HandlerContext(
                question="문서 찾아줘",
                intent="discover",
                resolution=resolution,
            )
            result = handler.handle(context)

        assert result.answer_type == "discover"
        assert "후보 없는 문서" in result.answer


class TestHandleUnresolved:
    """resolution.resolved=False일 때의 동작 테스트."""

    def test_handle_unresolved(self, handler, unresolved_resolution):
        """resolved=False이면 answer_type='clarify'를 반환해야 한다."""
        context = HandlerContext(
            question="컨벤션 문서 보여줘",
            intent="discover",
            resolution=unresolved_resolution,
        )
        result = handler.handle(context)

        assert result.answer_type == "clarify"
        assert result.sources == []
        assert result.resolved_document is None

    def test_handle_unresolved_answer_contains_candidate_titles(self, handler, unresolved_resolution):
        """unresolved 응답에 후보 문서들의 제목이 포함되어야 한다."""
        context = HandlerContext(
            question="컨벤션 문서 보여줘",
            intent="discover",
            resolution=unresolved_resolution,
        )
        result = handler.handle(context)

        assert "문서 A" in result.answer
        assert "문서 B" in result.answer

    def test_handle_unresolved_answer_contains_clarify_prompt(self, handler, unresolved_resolution):
        """unresolved 응답에 명확화 요청 메시지가 포함되어야 한다."""
        context = HandlerContext(
            question="컨벤션 문서 보여줘",
            intent="discover",
            resolution=unresolved_resolution,
        )
        result = handler.handle(context)

        assert "어떤 문서" in result.answer

    def test_handle_unresolved_no_candidates(self, handler):
        """후보가 없는 경우에도 answer_type='clarify'를 반환해야 한다."""
        resolution = MagicMock()
        resolution.resolved = False
        resolution.canonical_doc_id = None
        resolution.title = None
        resolution.path = None
        resolution.candidates = []

        context = HandlerContext(
            question="문서 찾아줘",
            intent="discover",
            resolution=resolution,
        )
        result = handler.handle(context)

        assert result.answer_type == "clarify"
        assert result.sources == []

    def test_handle_unresolved_get_section_headings_not_called(self, handler, unresolved_resolution):
        """resolved=False일 때 _get_section_headings가 호출되지 않아야 한다."""
        with patch.object(handler, "_get_section_headings") as mock_headings:
            context = HandlerContext(
                question="문서 찾아줘",
                intent="discover",
                resolution=unresolved_resolution,
            )
            handler.handle(context)

        mock_headings.assert_not_called()
