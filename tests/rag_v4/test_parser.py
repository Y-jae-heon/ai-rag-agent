from pathlib import Path

from src.rag_v4.ingest.parser import parse_markdown_file


def test_parser_extracts_h1_semantic_sections_from_fsd_overview():
    doc = parse_markdown_file(
        Path("docs/fe_chunk_docs/FSD 레이어드 아키텍처 개요 325e63c6fa978067a124e0c68833a066.md")
    )

    section_types = [section.section_type for section in doc.sections]

    assert "title" in section_types
    assert "rule" in section_types
    assert "rationale" in section_types
    assert "exception" in section_types
    assert "override" in section_types
    assert len(doc.sections) >= 5

