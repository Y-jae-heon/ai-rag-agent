import json
from pathlib import Path


def load_alias_registry(registry_path: Path) -> dict[str, dict]:
    """alias_registry.json을 로딩한다.

    Returns:
        {canonical_doc_id: {title, aliases, domain, stack, topic}} 형태의 딕셔너리
    """
    if not registry_path.exists():
        return {}
    with registry_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data


def get_aliases(canonical_doc_id: str, alias_registry: dict[str, dict]) -> list[str]:
    """canonical_doc_id에 해당하는 alias 목록을 반환한다."""
    entry = alias_registry.get(canonical_doc_id, {})
    if isinstance(entry, list):
        return entry
    return entry.get("aliases", [])
