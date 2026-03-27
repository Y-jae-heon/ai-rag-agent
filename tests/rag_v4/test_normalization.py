from src.rag_v4.normalization import expand_terms, normalize_query


def test_normalize_query_keeps_frontend_as_lexical_signal_not_filter():
    normalized = normalize_query("프론트엔드 FSD 구조 규칙 알려줘")

    assert "frontend" in normalized.expansions
    assert "feature sliced design" in normalized.expansions
    assert "프론트엔드 fsd 구조 규칙 알려줘" in normalized.retrieval_text


def test_expand_terms_does_not_overmatch_short_tokens():
    expansions = expand_terms("feature")
    assert "backend" not in expansions
    assert "pull request" not in expansions

