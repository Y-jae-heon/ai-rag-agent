#!/usr/bin/env python3
"""Build the greenfield RAG v4 indices."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from src.rag_v4.ingest.index_builder import build_indices


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the RAG v4 indices.")
    parser.add_argument("--rebuild", action="store_true", default=False)
    parser.add_argument(
        "--collections",
        nargs="+",
        choices=["document_dense", "section_dense", "section_sparse"],
        default=None,
    )
    args = parser.parse_args()

    counts = build_indices(force_rebuild=args.rebuild, collections=args.collections)
    print(counts)


if __name__ == "__main__":
    main()

