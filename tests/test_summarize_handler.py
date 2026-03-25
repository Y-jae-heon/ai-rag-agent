"""SummarizeHandler 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.convention_qa.action_routing.base_handler import HandlerContext
from src.convention_qa.action_routing.summarize_handler import SummarizeHandler


@pytest.fixture
def resolved_resolution():
    resolution = MagicMock()
    resolution.resolved = True
    resolution.canonical_doc_id = "test_doc_id"
    resolution.title = "테스트 문서"
    resolution.path = "docs/test.md"
    resolution.candidates = []
    return resolution


@pytest.fixture
def handler():
    return SummarizeHandler()


class TestHandleWithSections:
    """_get_sections가 섹션 목록을 반환할 때의 동작 테스트."""

    def test_handle_with_sections(self, handler, resolved_resolution):
        sections = [
            {"heading": "## 네이밍 규칙", "content": "camelCase를 사용한다."},
            {"heading": "## 파일 구조", "content": "컴포넌트별로 분리한다."},
        ]

        with patch.object(handler, "_get_sections", return_value=sections) as mock_get_sections, \
             patch.object(handler, "_summarize", return_value="요약 텍스트") as mock_summarize:

            context = HandlerContext(
                question="이 문서를 요약해줘",
                intent="summarize",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        mock_get_sections.assert_called_once_with("test_doc_id")
        mock_summarize.assert_called_once()

        assert result.answer_type == "summary"
        assert "테스트 문서" in result.answer
        assert "요약" in result.answer
        assert result.sources == [{"path": "docs/test.md", "title": "테스트 문서"}]
        assert result.resolved_document is not None
        assert result.resolved_document["canonical_doc_id"] == "test_doc_id"

    def test_handle_sections_text_includes_heading_and_content(self, handler, resolved_resolution):
        """섹션 텍스트가 heading과 content를 포함해 _summarize에 전달되는지 확인."""
        sections = [
            {"heading": "## 규칙1", "content": "내용1"},
        ]

        captured_args = {}

        def capture_summarize(title, sections_text):
            captured_args["title"] = title
            captured_args["sections_text"] = sections_text
            return "요약 텍스트"

        with patch.object(handler, "_get_sections", return_value=sections), \
             patch.object(handler, "_summarize", side_effect=capture_summarize):

            context = HandlerContext(
                question="요약",
                intent="summarize",
                resolution=resolved_resolution,
            )
            handler.handle(context)

        assert "## 규칙1" in captured_args["sections_text"]
        assert "내용1" in captured_args["sections_text"]
        assert captured_args["title"] == "테스트 문서"


class TestHandleEmptySections:
    """_get_sections가 빈 리스트를 반환할 때의 동작 테스트."""

    def test_handle_empty_sections(self, handler, resolved_resolution):
        """빈 섹션 반환 시 sections_text가 '(섹션 데이터 없음)'으로 _summarize에 전달되어야 한다."""
        captured_args = {}

        def capture_summarize(title, sections_text):
            captured_args["sections_text"] = sections_text
            return "요약 텍스트"

        with patch.object(handler, "_get_sections", return_value=[]), \
             patch.object(handler, "_summarize", side_effect=capture_summarize):

            context = HandlerContext(
                question="요약해줘",
                intent="summarize",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        assert captured_args["sections_text"] == "(섹션 데이터 없음)"
        assert result.answer_type == "summary"

    def test_handle_empty_sections_still_returns_summarize_type(self, handler, resolved_resolution):
        """빈 섹션이어도 answer_type은 'summary'여야 한다."""
        with patch.object(handler, "_get_sections", return_value=[]), \
             patch.object(handler, "_summarize", return_value="요약 텍스트"):

            context = HandlerContext(
                question="요약해줘",
                intent="summarize",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        assert result.answer_type == "summary"
        assert result.answer is not None


class TestHandleNoCanonicalDocId:
    """canonical_doc_id가 없을 때의 동작 테스트."""

    def test_handle_no_canonical_doc_id(self, handler):
        """canonical_doc_id가 None이면 _get_sections가 빈 리스트를 반환하고
        sections_text가 '(섹션 데이터 없음)'으로 처리되어야 한다."""
        resolution = MagicMock()
        resolution.resolved = True
        resolution.canonical_doc_id = None
        resolution.title = "제목 없음"
        resolution.path = ""
        resolution.candidates = []

        captured_args = {}

        def capture_summarize(title, sections_text):
            captured_args["sections_text"] = sections_text
            return "요약 텍스트"

        with patch.object(handler, "_summarize", side_effect=capture_summarize):
            context = HandlerContext(
                question="요약해줘",
                intent="summarize",
                resolution=resolution,
            )
            result = handler.handle(context)

        assert captured_args["sections_text"] == "(섹션 데이터 없음)"
        assert result.answer_type == "summary"

    def test_handle_empty_canonical_doc_id_string(self, handler):
        """canonical_doc_id가 빈 문자열이면 _get_sections가 빈 리스트를 반환해야 한다."""
        resolution = MagicMock()
        resolution.resolved = True
        resolution.canonical_doc_id = ""
        resolution.title = "테스트"
        resolution.path = "docs/test.md"
        resolution.candidates = []

        handler_instance = SummarizeHandler()
        # _get_sections를 직접 호출하여 빈 canonical_doc_id 처리 확인
        result = handler_instance._get_sections("")
        assert result == []
