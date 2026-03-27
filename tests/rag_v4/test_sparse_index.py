from pathlib import Path

from src.rag_v4.models import SectionRecord
from src.rag_v4.retrieval.sparse_index import SparseSectionIndex


def test_sparse_index_scores_keyword_matches(tmp_path: Path):
    index = SparseSectionIndex(tmp_path / "section_sparse" / "index.json")
    records = [
        SectionRecord(
            section_id="doc-1::section-1",
            doc_id="doc-1",
            title="FSD 레이어드 아키텍처 개요",
            source_path="docs/fsd-overview.md",
            section_type="rule",
            heading="Rule",
            content="FSD 레이어 구조와 의존성 규칙을 설명한다.",
            index_text="FSD 레이어 구조와 의존성 규칙을 설명한다.",
        ),
        SectionRecord(
            section_id="doc-2::section-1",
            doc_id="doc-2",
            title="Git PR 템플릿",
            source_path="docs/git-pr.md",
            section_type="rule",
            heading="Rule",
            content="PR 작성 규칙을 설명한다.",
            index_text="PR 작성 규칙을 설명한다.",
        ),
    ]
    index.build(records)

    results = index.search("FSD 구조 규칙", limit=2)

    assert results
    assert results[0].doc_id == "doc-1"

