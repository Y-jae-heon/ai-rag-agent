"""FastAPI 애플리케이션 진입점.

lifespan에서 ChromaDB 인덱스 존재 여부를 확인하고,
health 및 query 라우터를 등록한다.
SKIP_INDEX_CHECK=true 환경변수로 인덱스 확인을 건너뛸 수 있다 (개발/테스트 용도).
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.api.dependencies import get_chroma_client
from src.api.routes import health, query


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI 애플리케이션 lifespan 컨텍스트 매니저.

    서버 기동 시 ChromaDB 인덱스 존재 여부를 확인한다.
    SKIP_INDEX_CHECK=true 환경변수가 설정된 경우 확인을 건너뛴다.

    Raises:
        RuntimeError: 필수 ChromaDB 인덱스가 존재하지 않는 경우.
    """
    if not os.getenv("SKIP_INDEX_CHECK"):
        get_chroma_client()
    yield


app = FastAPI(
    title="Developer Convention Q&A",
    description="개발 컨벤션 문서 QA API",
    version="3.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(query.router)
