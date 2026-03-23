from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from .markdown_parser import ParsedDocument
from .config import OPENAI_EMBEDDING_MODEL


def build_section_index(
    parsed_docs: list[ParsedDocument],
    persist_dir: Path,
) -> int:
    """섹션 단위 인덱스를 빌드한다.

    각 섹션(##) → Document 1개 (heading + content 임베딩)

    Args:
        parsed_docs: 파싱된 문서 목록
        persist_dir: Chroma persist 디렉토리 (루트)

    Returns:
        인덱싱된 섹션 수
    """
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    collection_dir = str(persist_dir / "section_index")

    documents: list[Document] = []
    for doc in parsed_docs:
        for section in doc.sections:
            heading = section["heading"]
            content = section["content"]
            page_content = f"{heading}\n{content}" if content else heading

            metadata = {
                "canonical_doc_id": doc.canonical_doc_id,
                "section_heading": heading,
                "domain": doc.domain,
                "stack": doc.stack or "",
                "path": doc.file_path,
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
        collection_name="section_index",
        persist_directory=collection_dir,
    )

    return len(documents)
