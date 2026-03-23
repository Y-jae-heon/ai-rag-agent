#!/usr/bin/env python3
"""
인덱스 빌드 CLI.

사용법:
  python scripts/ingest.py                                        # 전체 빌드
  python scripts/ingest.py --rebuild                             # 강제 재빌드
  python scripts/ingest.py --collections document_index section_index
"""
import argparse
import sys
import time
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.convention_qa.indexing.build_index import run

_ALL_COLLECTIONS = ["document_index", "section_index", "chunk_index"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ChromaDB 인덱스를 빌드합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python scripts/ingest.py
  python scripts/ingest.py --rebuild
  python scripts/ingest.py --collections document_index section_index
""",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        default=False,
        help="기존 .chroma/ 를 삭제하고 전체 재빌드합니다.",
    )
    parser.add_argument(
        "--collections",
        nargs="+",
        choices=_ALL_COLLECTIONS,
        metavar="COLLECTION",
        default=None,
        help=(
            f"빌드할 컬렉션을 지정합니다. "
            f"선택 가능: {', '.join(_ALL_COLLECTIONS)}. "
            f"미지정 시 전체 빌드."
        ),
    )

    args = parser.parse_args()

    print("=" * 60)
    print("  developer-chat-bot-v3 / Index Builder")
    print("=" * 60)

    if args.rebuild:
        print("[INFO] Mode: FORCE REBUILD (기존 인덱스 삭제 후 재빌드)")
    else:
        print("[INFO] Mode: BUILD (기존 인덱스가 없으면 신규 생성)")

    if args.collections:
        print(f"[INFO] Target collections: {args.collections}")
    else:
        print(f"[INFO] Target collections: ALL ({', '.join(_ALL_COLLECTIONS)})")

    print("-" * 60)

    start = time.time()
    try:
        run(
            force_rebuild=args.rebuild,
            collections=args.collections,
        )
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Build failed: {e}")
        raise
    finally:
        elapsed = time.time() - start
        print("-" * 60)
        print(f"[INFO] Elapsed: {elapsed:.1f}s")
        print("=" * 60)


if __name__ == "__main__":
    main()
