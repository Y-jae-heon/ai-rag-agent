"""CompareHandler 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.convention_qa.action_routing.base_handler import HandlerContext
from src.convention_qa.action_routing.compare_handler import CompareHandler


def make_context(document_queries, question="비교해줘"):
    resolution = MagicMock()
    resolution.resolved = False
    resolution.canonical_doc_id = None
    resolution.title = None
    resolution.path = None

    understanding = MagicMock()
    understanding.document_queries = document_queries
    understanding.domain = None
    understanding.stack = None

    return HandlerContext(
        question=question,
        intent="compare",
        resolution=resolution,
        understanding=understanding,
    )


@pytest.fixture
def handler():
    return CompareHandler()


class TestHandleNotFound:
    """document_queries가 없거나 부족한 경우 not_found 반환 테스트."""

    def test_handle_no_document_queries_returns_not_found(self, handler):
        """document_queries가 None이면 answer_type='not_found'를 반환해야 한다."""
        context = make_context(document_queries=None)
        result = handler.handle(context)

        assert result.answer_type == "not_found"
        assert result.sources == []
        assert "찾을 수 없습니다" in result.answer

    def test_handle_single_document_query_returns_not_found(self, handler):
        """document_queries가 1개(len < 2)이면 answer_type='not_found'를 반환해야 한다."""
        context = make_context(document_queries=["문서A"])
        result = handler.handle(context)

        assert result.answer_type == "not_found"
        assert result.sources == []
        assert "찾을 수 없습니다" in result.answer

    def test_handle_empty_document_queries_returns_not_found(self, handler):
        """document_queries가 빈 리스트이면 answer_type='not_found'를 반환해야 한다."""
        context = make_context(document_queries=[])
        result = handler.handle(context)

        assert result.answer_type == "not_found"
        assert result.sources == []


class TestHandleNormalCase:
    """두 문서 모두 resolution 성공한 정상 케이스 테스트."""

    def test_handle_two_documents_returns_compare_type(self, handler):
        """두 document_queries가 모두 resolve되면 answer_type='compare'를 반환해야 한다."""
        resolution_a = MagicMock()
        resolution_a.title = "Java 네이밍"
        resolution_a.path = "docs/java-naming.md"
        resolution_a.canonical_doc_id = "id_java"

        resolution_b = MagicMock()
        resolution_b.title = "Kotlin 네이밍"
        resolution_b.path = "docs/kotlin-naming.md"
        resolution_b.canonical_doc_id = "id_kotlin"

        sections_a = [{"heading": "## 클래스 네이밍", "content": "PascalCase를 사용한다."}]
        sections_b = [{"heading": "## 클래스 네이밍", "content": "PascalCase를 사용한다."}]

        context = make_context(document_queries=["Java 네이밍", "Kotlin 네이밍"])

        with patch.object(handler, "_resolve", side_effect=[resolution_a, resolution_b]) as mock_resolve, \
             patch.object(handler, "_get_sections", side_effect=[sections_a, sections_b]) as mock_get_sections, \
             patch.object(handler, "_compare", return_value="비교 결과 텍스트") as mock_compare:

            result = handler.handle(context)

        assert result.answer_type == "compare"
        assert mock_resolve.call_count == 2
        assert mock_get_sections.call_count == 2
        mock_compare.assert_called_once()

    def test_handle_sources_contain_both_documents(self, handler):
        """결과 sources에 두 문서 정보가 모두 포함되어야 한다."""
        resolution_a = MagicMock()
        resolution_a.title = "Java 네이밍"
        resolution_a.path = "docs/java-naming.md"
        resolution_a.canonical_doc_id = "id_java"

        resolution_b = MagicMock()
        resolution_b.title = "Kotlin 네이밍"
        resolution_b.path = "docs/kotlin-naming.md"
        resolution_b.canonical_doc_id = "id_kotlin"

        context = make_context(document_queries=["Java 네이밍", "Kotlin 네이밍"])

        with patch.object(handler, "_resolve", side_effect=[resolution_a, resolution_b]), \
             patch.object(handler, "_get_sections", return_value=[]), \
             patch.object(handler, "_compare", return_value="비교 결과"):

            result = handler.handle(context)

        assert len(result.sources) == 2
        paths = [s["path"] for s in result.sources]
        titles = [s["title"] for s in result.sources]
        assert "docs/java-naming.md" in paths
        assert "docs/kotlin-naming.md" in paths
        assert "Java 네이밍" in titles
        assert "Kotlin 네이밍" in titles

    def test_handle_compare_called_with_correct_args(self, handler):
        """_compare가 올바른 title과 sections 인자로 호출되어야 한다."""
        resolution_a = MagicMock()
        resolution_a.title = "Java 네이밍"
        resolution_a.path = "docs/java-naming.md"
        resolution_a.canonical_doc_id = "id_java"

        resolution_b = MagicMock()
        resolution_b.title = "Kotlin 네이밍"
        resolution_b.path = "docs/kotlin-naming.md"
        resolution_b.canonical_doc_id = "id_kotlin"

        sections_a = [{"heading": "## 규칙A", "content": "내용A"}]
        sections_b = [{"heading": "## 규칙B", "content": "내용B"}]

        captured_args = {}

        def capture_compare(title_a, title_b, sections_a, sections_b, question):
            captured_args.update({
                "title_a": title_a,
                "title_b": title_b,
                "sections_a": sections_a,
                "sections_b": sections_b,
                "question": question,
            })
            return "비교 결과"

        context = make_context(document_queries=["Java 네이밍", "Kotlin 네이밍"], question="차이를 설명해줘")

        with patch.object(handler, "_resolve", side_effect=[resolution_a, resolution_b]), \
             patch.object(handler, "_get_sections", side_effect=[sections_a, sections_b]), \
             patch.object(handler, "_compare", side_effect=capture_compare):

            handler.handle(context)

        assert captured_args["title_a"] == "Java 네이밍"
        assert captured_args["title_b"] == "Kotlin 네이밍"
        assert "## 규칙A" in captured_args["sections_a"]
        assert "내용A" in captured_args["sections_a"]
        assert "## 규칙B" in captured_args["sections_b"]
        assert "내용B" in captured_args["sections_b"]
        assert captured_args["question"] == "차이를 설명해줘"

    def test_handle_answer_contains_titles(self, handler):
        """최종 answer에 두 문서 제목이 포함되어야 한다."""
        resolution_a = MagicMock()
        resolution_a.title = "Java 네이밍"
        resolution_a.path = "docs/java-naming.md"
        resolution_a.canonical_doc_id = "id_java"

        resolution_b = MagicMock()
        resolution_b.title = "Kotlin 네이밍"
        resolution_b.path = "docs/kotlin-naming.md"
        resolution_b.canonical_doc_id = "id_kotlin"

        context = make_context(document_queries=["Java 네이밍", "Kotlin 네이밍"])

        with patch.object(handler, "_resolve", side_effect=[resolution_a, resolution_b]), \
             patch.object(handler, "_get_sections", return_value=[]), \
             patch.object(handler, "_compare", return_value="비교 결과"):

            result = handler.handle(context)

        assert "Java 네이밍" in result.answer
        assert "Kotlin 네이밍" in result.answer


class TestHandleResolutionFailure:
    """한 문서 resolution 실패(None 반환) 시 graceful 처리 테스트."""

    def test_handle_second_resolution_none_still_returns_compare(self, handler):
        """두 번째 _resolve가 None을 반환해도 answer_type='compare'를 반환해야 한다."""
        resolution_a = MagicMock()
        resolution_a.title = "문서A"
        resolution_a.path = "docs/a.md"
        resolution_a.canonical_doc_id = "id_a"

        context = make_context(document_queries=["문서A", "문서B"])

        with patch.object(handler, "_resolve", side_effect=[resolution_a, None]), \
             patch.object(handler, "_get_sections", return_value=[]), \
             patch.object(handler, "_compare", return_value="비교 결과"):

            result = handler.handle(context)

        assert result.answer_type == "compare"

    def test_handle_second_resolution_none_uses_query_as_title(self, handler):
        """두 번째 _resolve가 None이면 query 문자열 자체를 title로 사용해야 한다."""
        resolution_a = MagicMock()
        resolution_a.title = "문서A"
        resolution_a.path = "docs/a.md"
        resolution_a.canonical_doc_id = "id_a"

        captured_args = {}

        def capture_compare(title_a, title_b, sections_a, sections_b, question):
            captured_args["title_b"] = title_b
            return "비교 결과"

        context = make_context(document_queries=["문서A", "문서B"])

        with patch.object(handler, "_resolve", side_effect=[resolution_a, None]), \
             patch.object(handler, "_get_sections", return_value=[]), \
             patch.object(handler, "_compare", side_effect=capture_compare):

            handler.handle(context)

        assert captured_args["title_b"] == "문서B"

    def test_handle_second_resolution_none_get_sections_called_with_empty_string(self, handler):
        """두 번째 _resolve가 None이면 _get_sections는 빈 문자열("")로 호출되어야 한다."""
        resolution_a = MagicMock()
        resolution_a.title = "문서A"
        resolution_a.path = "docs/a.md"
        resolution_a.canonical_doc_id = "id_a"

        context = make_context(document_queries=["문서A", "문서B"])

        with patch.object(handler, "_resolve", side_effect=[resolution_a, None]), \
             patch.object(handler, "_get_sections", return_value=[]) as mock_get_sections, \
             patch.object(handler, "_compare", return_value="비교 결과"):

            handler.handle(context)

        call_args_list = mock_get_sections.call_args_list
        assert call_args_list[0][0][0] == "id_a"
        assert call_args_list[1][0][0] == ""

    def test_handle_compare_called_with_empty_sections_when_resolution_fails(self, handler):
        """resolution이 None이면 해당 문서의 sections는 '(섹션 데이터 없음)'으로 _compare에 전달되어야 한다."""
        resolution_a = MagicMock()
        resolution_a.title = "문서A"
        resolution_a.path = "docs/a.md"
        resolution_a.canonical_doc_id = "id_a"

        captured_args = {}

        def capture_compare(title_a, title_b, sections_a, sections_b, question):
            captured_args["sections_b"] = sections_b
            return "비교 결과"

        context = make_context(document_queries=["문서A", "문서B"])

        with patch.object(handler, "_resolve", side_effect=[resolution_a, None]), \
             patch.object(handler, "_get_sections", return_value=[]), \
             patch.object(handler, "_compare", side_effect=capture_compare):

            handler.handle(context)

        assert captured_args["sections_b"] == "(섹션 데이터 없음)"


class TestFormatSections:
    """_format_sections 메서드 직접 테스트."""

    def test_format_sections_empty_returns_placeholder(self, handler):
        """빈 섹션 리스트를 전달하면 '(섹션 데이터 없음)'을 반환해야 한다."""
        result = handler._format_sections([])
        assert result == "(섹션 데이터 없음)"

    def test_format_sections_with_heading_and_content(self, handler):
        """heading과 content가 있는 섹션을 올바르게 포맷팅해야 한다."""
        sections = [
            {"heading": "## 네이밍 규칙", "content": "camelCase를 사용한다."},
        ]
        result = handler._format_sections(sections)
        assert "## 네이밍 규칙" in result
        assert "camelCase를 사용한다." in result

    def test_format_sections_multiple_sections_joined_by_double_newline(self, handler):
        """여러 섹션은 두 줄 개행으로 구분되어야 한다."""
        sections = [
            {"heading": "## 섹션1", "content": "내용1"},
            {"heading": "## 섹션2", "content": "내용2"},
        ]
        result = handler._format_sections(sections)
        assert "## 섹션1" in result
        assert "내용1" in result
        assert "## 섹션2" in result
        assert "내용2" in result
        assert "\n\n" in result

    def test_format_sections_empty_content_only_heading(self, handler):
        """content가 빈 문자열인 섹션은 heading만 포함되어야 한다."""
        sections = [
            {"heading": "## 제목만 있는 섹션", "content": ""},
        ]
        result = handler._format_sections(sections)
        assert "## 제목만 있는 섹션" in result

    def test_get_sections_empty_canonical_doc_id_returns_empty_list(self, handler):
        """canonical_doc_id가 빈 문자열이면 _get_sections는 빈 리스트를 반환해야 한다."""
        result = handler._get_sections("")
        assert result == []
