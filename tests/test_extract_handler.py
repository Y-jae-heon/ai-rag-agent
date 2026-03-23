"""ExtractHandler 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.convention_qa.action_routing.base_handler import HandlerContext
from src.convention_qa.action_routing.extract_handler import ExtractHandler


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
    return ExtractHandler()


class TestHandleWithChunks:
    """_mmr_search가 청크 목록을 반환할 때의 동작 테스트."""

    def test_handle_with_chunks(self, handler, resolved_resolution):
        chunks = [
            {"content": "camelCase를 사용한다.", "heading": "## 네이밍 규칙"},
            {"content": "컴포넌트별로 파일을 분리한다.", "heading": "## 파일 구조"},
        ]

        with patch.object(handler, "_mmr_search", return_value=chunks) as mock_search, \
             patch.object(handler, "_extract_answer", return_value="QA 답변") as mock_extract:

            context = HandlerContext(
                question="네이밍 규칙이 뭐야?",
                intent="extract",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        mock_search.assert_called_once_with("네이밍 규칙이 뭐야?", "test_doc_id")
        mock_extract.assert_called_once()

        assert result.answer_type == "extract"
        assert "QA 답변" in result.answer
        assert result.sources == [{"path": "docs/test.md", "title": "테스트 문서"}]
        assert result.resolved_document is not None
        assert result.resolved_document["canonical_doc_id"] == "test_doc_id"

    def test_handle_with_chunks_passes_question_and_chunks_text(self, handler, resolved_resolution):
        """_extract_answer에 question과 chunks_text가 올바르게 전달되는지 확인."""
        chunks = [
            {"content": "청크 내용1", "heading": "섹션1"},
            {"content": "청크 내용2", "heading": "섹션2"},
        ]

        captured_args = {}

        def capture_extract(question, chunks_text):
            captured_args["question"] = question
            captured_args["chunks_text"] = chunks_text
            return "QA 답변"

        with patch.object(handler, "_mmr_search", return_value=chunks), \
             patch.object(handler, "_extract_answer", side_effect=capture_extract):

            context = HandlerContext(
                question="규칙을 알려줘",
                intent="extract",
                resolution=resolved_resolution,
            )
            handler.handle(context)

        assert captured_args["question"] == "규칙을 알려줘"
        assert "청크 내용1" in captured_args["chunks_text"]
        assert "청크 내용2" in captured_args["chunks_text"]

    def test_handle_with_chunks_source_sections_in_answer(self, handler, resolved_resolution):
        """섹션 헤딩이 있는 청크의 경우 포맷된 응답에 출처 정보가 포함되는지 확인."""
        chunks = [
            {"content": "내용", "heading": "## 네이밍 규칙"},
        ]

        with patch.object(handler, "_mmr_search", return_value=chunks), \
             patch.object(handler, "_extract_answer", return_value="QA 답변"):

            context = HandlerContext(
                question="질문",
                intent="extract",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        assert "네이밍 규칙" in result.answer


class TestHandleEmptyChunks:
    """_mmr_search가 빈 리스트를 반환할 때의 동작 테스트."""

    def test_handle_empty_chunks(self, handler, resolved_resolution):
        """청크가 없으면 answer_type이 'not_found'여야 한다."""
        with patch.object(handler, "_mmr_search", return_value=[]) as mock_search, \
             patch.object(handler, "_extract_answer") as mock_extract:

            context = HandlerContext(
                question="없는 내용 질문",
                intent="extract",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        mock_search.assert_called_once_with("없는 내용 질문", "test_doc_id")
        mock_extract.assert_not_called()

        assert result.answer_type == "not_found"
        assert result.sources == []

    def test_handle_empty_chunks_answer_contains_not_found_message(self, handler, resolved_resolution):
        """청크가 없을 때 응답에 문서를 찾을 수 없다는 메시지가 포함되어야 한다."""
        with patch.object(handler, "_mmr_search", return_value=[]):
            context = HandlerContext(
                question="질문",
                intent="extract",
                resolution=resolved_resolution,
            )
            result = handler.handle(context)

        assert "찾을 수 없습니다" in result.answer


class TestHandleNoCanonicalDocId:
    """canonical_doc_id가 없을 때의 동작 테스트."""

    def test_handle_no_canonical_doc_id(self, handler):
        """canonical_doc_id가 None이면 _mmr_search가 빈 리스트를 반환하고
        format_not_found 결과가 반환되어야 한다."""
        resolution = MagicMock()
        resolution.resolved = True
        resolution.canonical_doc_id = None
        resolution.title = "알 수 없는 문서"
        resolution.path = ""
        resolution.candidates = []

        with patch.object(handler, "_extract_answer") as mock_extract:
            context = HandlerContext(
                question="질문",
                intent="extract",
                resolution=resolution,
            )
            result = handler.handle(context)

        mock_extract.assert_not_called()
        assert result.answer_type == "not_found"

    def test_handle_empty_canonical_doc_id_string(self, handler):
        """canonical_doc_id가 빈 문자열이면 _mmr_search가 빈 리스트를 반환해야 한다."""
        handler_instance = ExtractHandler()
        result = handler_instance._mmr_search("질문", "")
        assert result == []

    def test_handle_no_canonical_doc_id_resolved_document_is_none(self, handler):
        """not_found 응답의 resolved_document는 None이어야 한다."""
        resolution = MagicMock()
        resolution.resolved = True
        resolution.canonical_doc_id = None
        resolution.title = None
        resolution.path = None
        resolution.candidates = []

        context = HandlerContext(
            question="질문",
            intent="extract",
            resolution=resolution,
        )
        result = handler.handle(context)

        assert result.answer_type == "not_found"
        assert result.resolved_document is None
