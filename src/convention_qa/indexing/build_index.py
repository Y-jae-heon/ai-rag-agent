import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .config import CHROMA_PERSIST_DIR, CORPUS_DIRS
from .markdown_parser import parse_file, ParsedDocument
from .manifest import load_alias_registry
from .document_indexer import build_document_index
from .section_indexer import build_section_index
from .chunk_indexer import build_chunk_index

_REGISTRY_PATH = Path(__file__).parent / "alias_registry.json"
_ALL_COLLECTIONS = ["document_index", "section_index", "chunk_index"]


def _collect_md_files(corpus_dirs: list[Path]) -> list[Path]:
    """CORPUS_DIRS에서 .md 파일을 수집한다."""
    files: list[Path] = []
    for corpus_dir in corpus_dirs:
        if not corpus_dir.exists():
            print(f"[WARNING] corpus dir not found: {corpus_dir}")
            continue
        files.extend(sorted(corpus_dir.glob("*.md")))
    return files


def run(
    force_rebuild: bool = False,
    collections: list[str] | None = None,
) -> None:
    """인덱스를 빌드한다.

    Args:
        force_rebuild: True이면 .chroma/ 삭제 후 재빌드
        collections: 빌드할 컬렉션 목록. None이면 전체 빌드.
                     예: ["document_index", "section_index", "chunk_index"]
    """
    persist_dir = CHROMA_PERSIST_DIR

    if force_rebuild and persist_dir.exists():
        print(f"[INFO] Removing existing index: {persist_dir}")
        shutil.rmtree(persist_dir)

    persist_dir.mkdir(parents=True, exist_ok=True)

    target_collections = set(collections) if collections else set(_ALL_COLLECTIONS)
    invalid = target_collections - set(_ALL_COLLECTIONS)
    if invalid:
        raise ValueError(f"Unknown collections: {invalid}. Valid: {_ALL_COLLECTIONS}")

    # 문서 수집 및 파싱
    print("[INFO] Collecting markdown files...")
    md_files = _collect_md_files(CORPUS_DIRS)
    if not md_files:
        print("[WARNING] No markdown files found.")
        return

    print(f"[INFO] Found {len(md_files)} files. Parsing...")
    parsed_docs: list[ParsedDocument] = []
    for f in md_files:
        try:
            doc = parse_file(f)
            parsed_docs.append(doc)
        except Exception as e:
            print(f"[WARNING] Failed to parse {f}: {e}")

    print(f"[INFO] Parsed {len(parsed_docs)} documents.")

    # alias_registry 로딩
    alias_registry = load_alias_registry(_REGISTRY_PATH)
    print(f"[INFO] Loaded alias registry with {len(alias_registry)} entries.")

    # 컬렉션별 빌드
    counts: dict[str, int] = {}

    if "document_index" in target_collections:
        print("[INFO] Building document_index...")
        count = build_document_index(parsed_docs, persist_dir, alias_registry)
        counts["document_index"] = count
        print(f"[INFO] document_index: {count} documents.")

    if "section_index" in target_collections:
        print("[INFO] Building section_index...")
        count = build_section_index(parsed_docs, persist_dir)
        counts["section_index"] = count
        print(f"[INFO] section_index: {count} sections.")

    if "chunk_index" in target_collections:
        print("[INFO] Building chunk_index...")
        count = build_chunk_index(parsed_docs, persist_dir)
        counts["chunk_index"] = count
        print(f"[INFO] chunk_index: {count} chunks.")

    # ingest_manifest.json 저장
    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "document_count": len(parsed_docs),
        "collections": {
            col: {"count": counts.get(col, 0)} for col in _ALL_COLLECTIONS
        },
    }
    manifest_path = persist_dir / "ingest_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[INFO] Manifest saved to {manifest_path}")
    print("[INFO] Done.")
