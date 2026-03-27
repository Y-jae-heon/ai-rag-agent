"""FastAPI 애플리케이션 진입점."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

from src.api.dependencies_v4 import check_v4_indices
from src.api.routes import health
from src.api.routes import query_v4


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI 애플리케이션 lifespan 컨텍스트 매니저.

    서버 기동 시 RAG v4 인덱스 존재 여부를 확인한다.
    SKIP_INDEX_CHECK=true 환경변수가 설정된 경우 확인을 건너뛴다.

    Raises:
        RuntimeError: 필수 RAG v4 인덱스가 존재하지 않는 경우.
    """
    if not os.getenv("SKIP_INDEX_CHECK"):
        check_v4_indices()
    yield


app = FastAPI(
    title="Developer Convention Q&A v4",
    description="개발 컨벤션 문서 검색 중심 RAG v4 API",
    version="4.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(query_v4.router)
