import json
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from .markdown_parser import ParsedDocument
from .manifest import get_aliases
from .config import OPENAI_EMBEDDING_MODEL


def build_document_index(
    parsed_docs: list[ParsedDocument],
    persist_dir: Path,
    alias_registry: dict[str, list[str]],
) -> int:
    """문서 단위 인덱스를 빌드한다.

    각 ParsedDocument → Document 1개 (title + aliases + section_headings 임베딩)

    Args:
        parsed_docs: 파싱된 문서 목록
        persist_dir: Chroma persist 디렉토리 (루트)
        alias_registry: {canonical_doc_id: [alias, ...]}

    Returns:
        인덱싱된 문서 수
    """
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    collection_dir = str(persist_dir / "document_index")

    documents: list[Document] = []
    for doc in parsed_docs:
        aliases = get_aliases(doc.canonical_doc_id, alias_registry)
        alias_str = " ".join(aliases) if aliases else ""
        headings_str = " ".join(doc.section_headings)

        page_content_parts = [doc.title]
        if alias_str:
            page_content_parts.append(alias_str)
        if headings_str:
            page_content_parts.append(headings_str)
        page_content = "\n".join(page_content_parts)

        metadata = {
            "canonical_doc_id": doc.canonical_doc_id,
            "title": doc.title,
            "aliases": json.dumps(aliases, ensure_ascii=False),
            "path": doc.file_path,
            "domain": doc.domain,
            "stack": doc.stack or "",
            "section_headings": json.dumps(doc.section_headings, ensure_ascii=False),
        }

        documents.append(
            Document(
                page_content=page_content,
                metadata=metadata,
            )
        )

    if not documents:
        return 0

    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name="document_index",
        persist_directory=collection_dir,
    )

    return len(documents)
