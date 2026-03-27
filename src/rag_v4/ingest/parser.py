"""Markdown parsing for the greenfield RAG v4 index."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from src.rag_v4.models import ParsedDocument, ParsedSection

_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_UUID_SUFFIX = re.compile(r"([0-9a-f]{32})$", re.IGNORECASE)
_SEMANTIC_HEADINGS = {
    "title": "title",
    "rule": "rule",
    "rationale": "rationale",
    "exception": "exception",
    "override": "override",
}


def parse_markdown_file(file_path: Path) -> ParsedDocument:
    """Parse a markdown file into semantic sections, preserving H1 blocks."""
    raw_text = file_path.read_text(encoding="utf-8")
    doc_id, title = _derive_doc_identity(file_path)
    sections = _extract_sections(raw_text, doc_id, title)
    return ParsedDocument(
        doc_id=doc_id,
        title=title,
        source_path=str(file_path),
        sections=sections,
    )


def _derive_doc_identity(file_path: Path) -> tuple[str, str]:
    stem = file_path.stem
    matched = _UUID_SUFFIX.search(stem)
    if matched:
        return matched.group(1), stem[: matched.start()].strip()
    digest = hashlib.sha1(str(file_path).encode("utf-8")).hexdigest()[:16]
    return digest, stem.strip()


def _extract_sections(raw_text: str, doc_id: str, title: str) -> list[ParsedSection]:
    matches = list(_HEADING_PATTERN.finditer(raw_text))
    if not matches:
        return [_fallback_body_section(doc_id, title, raw_text)]

    sections: list[ParsedSection] = []
    for index, match in enumerate(matches):
        heading = match.group(2).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw_text)
        content = raw_text[start:end].strip()

        if _is_metadata_title_block(index, heading, title, content):
            continue

        section_type = _classify_heading(heading)
        section_id = f"{doc_id}::section::{len(sections)}"
        sections.append(
            ParsedSection(
                section_id=section_id,
                section_type=section_type,
                heading=heading,
                content=content,
            )
        )

    if sections:
        return sections
    return [_fallback_body_section(doc_id, title, raw_text)]


def _is_metadata_title_block(index: int, heading: str, title: str, content: str) -> bool:
    if index != 0:
        return False
    if heading.strip() != title.strip():
        return False
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return True
    metadata_like = sum(1 for line in lines if ":" in line)
    return metadata_like >= max(3, len(lines) // 2)


def _classify_heading(heading: str) -> str:
    normalized = heading.strip().lower()
    return _SEMANTIC_HEADINGS.get(normalized, "body")


def _fallback_body_section(doc_id: str, title: str, raw_text: str) -> ParsedSection:
    cleaned = _strip_header_metadata(raw_text)
    return ParsedSection(
        section_id=f"{doc_id}::section::0",
        section_type="body",
        heading=title,
        content=cleaned,
    )


def _strip_header_metadata(raw_text: str) -> str:
    lines = raw_text.splitlines()
    kept_lines: list[str] = []
    for line in lines:
        if kept_lines or not re.match(r"^[^#\n][^:]{0,40}:\s*", line.strip()):
            kept_lines.append(line)
    return "\n".join(kept_lines).strip()

