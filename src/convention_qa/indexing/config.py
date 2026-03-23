import os
from pathlib import Path

CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", ".chroma"))
CORPUS_DIRS = [
    Path("docs/fe_chunk_docs"),
    Path("docs/be_chunk_docs"),
]
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
SIMILARITY_THRESHOLD = 0.75
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
