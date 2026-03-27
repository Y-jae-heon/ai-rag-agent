#!/usr/bin/env python3
"""Run the retrieval benchmark for RAG v4."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from src.rag_v4.service import RagV4Service

CASES_PATH = Path("ai-work/benchmarks/rag_v4_queries.json")


def main() -> None:
    service = RagV4Service()
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    results: list[dict] = []
    for case in cases:
        outcome = service.query(case["question"], debug=True)
        results.append(
            {
                "question": case["question"],
                "expected_docs": case["expected_docs"],
                "top_documents": [doc.model_dump() for doc in outcome.top_documents],
                "trace_id": outcome.trace_id,
            }
        )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

