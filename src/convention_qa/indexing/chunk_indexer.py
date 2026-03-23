from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .markdown_parser import ParsedDocument
from .config import OPENAI_EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP


def build_chunk_index(
    parsed_docs: list[ParsedDocument],
    persist_dir: Path,
) -> int:
    """청크 단위 인덱스를 빌드한다.

    각 섹션을 RecursiveCharacterTextSplitter로 분할하여 chunk_index에 저장한다.

    Args:
        parsed_docs: 파싱된 문서 목록
        persist_dir: Chroma persist 디렉토리 (루트)

    Returns:
        인덱싱된 청크 수
    """
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    collection_dir = str(persist_dir / "chunk_index")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    documents: list[Document] = []
    for doc in parsed_docs:
        if doc.sections:
            for section in doc.sections:
                heading = section["heading"]
                content = section["content"]
                section_text = f"{heading}\n{content}" if content else heading

                chunks = splitter.split_text(section_text)
                for chunk in chunks:
                    metadata = {
                        "canonical_doc_id": doc.canonical_doc_id,
                        "section_heading": heading,
                        "domain": doc.domain,
                        "stack": doc.stack or "",
                        "title": doc.title,
                        "path": doc.file_path,
                    }
                    documents.append(
                        Document(
                            page_content=chunk,
                            metadata=metadata,
                        )
                    )
        else:
            # 섹션이 없는 경우 전체 내용을 청크로 분할
            chunks = splitter.split_text(doc.raw_content)
            for chunk in chunks:
                metadata = {
                    "canonical_doc_id": doc.canonical_doc_id,
                    "section_heading": "",
                    "domain": doc.domain,
                    "stack": doc.stack or "",
                    "title": doc.title,
                    "path": doc.file_path,
                }
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata=metadata,
                    )
                )

    if not documents:
        return 0

    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name="chunk_index",
        persist_directory=collection_dir,
    )

    return len(documents)
