import re
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    file_path: str
    canonical_doc_id: str   # 파일명 UUID
    title: str              # 파일명에서 UUID 제거한 부분
    domain: str             # fe_chunk_docs → frontend, be_chunk_docs → backend
    stack: str | None       # 파일명에서 추출 (spring, nestjs, react 등)
    language: str | None    # java, kotlin, typescript 등
    raw_content: str        # 전체 파일 내용
    sections: list[dict] = field(default_factory=list)    # [{"heading": str, "content": str, "level": int}]
    section_headings: list[str] = field(default_factory=list)


_UUID_PATTERN = re.compile(r"([0-9a-f]{32})$", re.IGNORECASE)

_DOMAIN_MAP: dict[str, str] = {
    "fe_chunk_docs": "frontend",
    "be_chunk_docs": "backend",
}


def _extract_uuid(stem: str) -> tuple[str, str]:
    """파일명 stem에서 UUID와 제목을 분리한다."""
    m = _UUID_PATTERN.search(stem)
    if not m:
        return "", stem.strip()
    uuid = m.group(1)
    title = stem[: m.start()].strip()
    return uuid, title


def _detect_stack(title: str, domain: str) -> tuple[str | None, str | None]:
    """title 및 domain으로부터 stack과 language를 추출한다."""
    if "Java(Spring)" in title:
        return "spring", "java"
    if "Kotlin(Spring)" in title:
        return "spring", "kotlin"
    if "Typescript(NestJS)" in title:
        return "nestjs", "typescript"
    if domain == "frontend":
        return "react", None
    return None, None


def _parse_sections(content: str) -> list[dict]:
    """## 기준으로 섹션을 분리한다. # 제목 섹션은 제외한다."""
    sections: list[dict] = []
    # ## 이상의 heading 으로 분리 (# 단독은 제외)
    pattern = re.compile(r"^(#{2,6})\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(content))

    for i, match in enumerate(matches):
        level = len(match.group(1))
        heading = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section_content = content[start:end].strip()
        sections.append({
            "heading": heading,
            "content": section_content,
            "level": level,
        })

    return sections


def parse_file(file_path: Path) -> ParsedDocument:
    """마크다운 파일을 파싱하여 ParsedDocument를 반환한다."""
    stem = file_path.stem
    canonical_doc_id, title = _extract_uuid(stem)

    parent_name = file_path.parent.name
    domain = _DOMAIN_MAP.get(parent_name, parent_name)

    stack, language = _detect_stack(title, domain)

    raw_content = file_path.read_text(encoding="utf-8")
    sections = _parse_sections(raw_content)
    section_headings = [s["heading"] for s in sections]

    return ParsedDocument(
        file_path=str(file_path),
        canonical_doc_id=canonical_doc_id,
        title=title,
        domain=domain,
        stack=stack,
        language=language,
        raw_content=raw_content,
        sections=sections,
        section_headings=section_headings,
    )
