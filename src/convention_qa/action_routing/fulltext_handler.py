"""FulltextHandler — LLM 없이 파일을 직접 읽어 원문 반환."""

from __future__ import annotations

import os
from pathlib import Path

from src.convention_qa.action_routing.base_handler import (
    BaseHandler,
    HandlerContext,
    HandlerResult,
)

# 허용된 corpus 디렉토리 목록 (프로젝트 루트 기준 상대 경로)
ALLOWED_CORPUS_DIRS: list[str] = [
    "docs/fe_chunk_docs",
    "docs/be_chunk_docs",
]

# 이 파일의 위치로부터 프로젝트 루트 계산
# src/convention_qa/action_routing/fulltext_handler.py → 3단계 상위가 프로젝트 루트
_DEFAULT_PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]


def is_safe_path(path: str, project_root: Path | None = None) -> bool:
    """path가 ALLOWED_CORPUS_DIRS 중 하나의 하위 경로인지 확인한다.

    Path traversal 방지를 위해 os.path.abspath로 정규화한 후 비교한다.

    Args:
        path: 검증할 경로 문자열 (프로젝트 루트 기준 상대 경로 또는 절대 경로).
        project_root: 프로젝트 루트 Path. None이면 이 파일 위치 기준으로 계산.

    Returns:
        path가 허용된 corpus 디렉토리 하위에 있으면 True, 아니면 False.
    """
    root: Path = project_root if project_root is not None else _DEFAULT_PROJECT_ROOT

    # 입력 경로가 절대 경로면 그대로 사용, 상대 경로면 프로젝트 루트 기준으로 절대 경로 변환
    if os.path.isabs(path):
        candidate = os.path.abspath(path)
    else:
        candidate = os.path.abspath(root / path)

    for allowed_dir in ALLOWED_CORPUS_DIRS:
        allowed_abs = os.path.abspath(root / allowed_dir)
        # 후행 구분자 추가로 정확한 디렉토리 하위 경로 확인 (prefix 오탐 방지)
        if candidate.startswith(allowed_abs + os.sep) or candidate == allowed_abs:
            return True

    return False


class FulltextHandler(BaseHandler):
    """파일 원문을 LLM 없이 직접 읽어 반환하는 핸들러.

    DocumentResolutionResult에서 path를 꺼내 해당 파일을 읽고
    메타데이터 헤더를 붙여 원문 그대로 반환한다.

    LLM 호출 없음. 규칙 기반으로 동작한다.
    """

    MAX_FILE_SIZE_BYTES: int = 500 * 1024  # 500KB

    def handle(self, context: HandlerContext) -> HandlerResult:
        """resolution에서 path를 꺼내 파일을 읽고 원문을 반환한다.

        동작 순서:
        1. context.resolution.path 확인
        2. is_safe_path() 검증 → 실패 시 에러 HandlerResult 반환
        3. 파일 존재 확인 → 없으면 에러 HandlerResult 반환
        4. 파일 크기 확인 → 500KB 초과 시 경고 메시지와 함께 앞부분만 반환
        5. 파일 읽기 (UTF-8)
        6. format_fulltext()로 포맷팅
        7. HandlerResult 반환

        Args:
            context: HandlerContext. resolution.path가 파일 경로를 담아야 한다.

        Returns:
            answer_type="fulltext"인 HandlerResult.
        """
        from src.convention_qa.response.formatters import format_fulltext, format_not_found

        resolution = context.resolution
        file_path: str | None = getattr(resolution, "path", None)
        title: str | None = getattr(resolution, "title", None)
        canonical_doc_id: str | None = getattr(resolution, "canonical_doc_id", None)

        # 1. path 확인
        if not file_path:
            return HandlerResult(
                answer=format_not_found(getattr(resolution, "canonical_doc_id", None)),
                answer_type="fulltext",
                sources=[],
                resolved_document=None,
            )

        # 2. 경로 안전성 검증 (Path traversal 방지)
        if not is_safe_path(file_path):
            return HandlerResult(
                answer=(
                    "요청한 파일 경로가 허용된 corpus 디렉토리 범위를 벗어납니다. "
                    "접근이 거부되었습니다."
                ),
                answer_type="fulltext",
                sources=[],
                resolved_document=None,
            )

        # 절대 경로 계산
        if os.path.isabs(file_path):
            abs_path = Path(file_path)
        else:
            abs_path = _DEFAULT_PROJECT_ROOT / file_path

        # 3. 파일 존재 확인
        if not abs_path.exists():
            return HandlerResult(
                answer=(
                    f"파일을 찾을 수 없습니다: `{file_path}`\n"
                    "문서가 인덱싱되지 않았거나 경로가 올바르지 않을 수 있습니다."
                ),
                answer_type="fulltext",
                sources=[],
                resolved_document=None,
            )

        # 4. 파일 크기 확인
        file_size = abs_path.stat().st_size
        truncated = False
        if file_size > self.MAX_FILE_SIZE_BYTES:
            truncated = True

        # 5. 파일 읽기 (UTF-8)
        if truncated:
            with abs_path.open("r", encoding="utf-8", errors="replace") as f:
                content = f.read(self.MAX_FILE_SIZE_BYTES)
            content += (
                f"\n\n---\n> ⚠️ 파일이 너무 큽니다 ({file_size // 1024}KB). "
                f"앞부분 {self.MAX_FILE_SIZE_BYTES // 1024}KB만 표시합니다."
            )
        else:
            content = abs_path.read_text(encoding="utf-8", errors="replace")

        # 6. 포맷팅
        display_title = title or abs_path.stem
        answer = format_fulltext(
            title=display_title,
            path=file_path,
            content=content,
        )

        # sources 구성
        sources: list[dict] = []
        if canonical_doc_id or display_title:
            sources = [
                {
                    "canonical_doc_id": canonical_doc_id or "",
                    "title": display_title,
                    "path": file_path,
                }
            ]

        # resolved_document 구성
        resolved_document: dict | None = None
        if resolution is not None:
            try:
                resolved_document = resolution.model_dump()
            except AttributeError:
                resolved_document = {
                    "path": file_path,
                    "title": display_title,
                    "canonical_doc_id": canonical_doc_id,
                }

        # 7. HandlerResult 반환
        return HandlerResult(
            answer=answer,
            answer_type="fulltext",
            sources=sources,
            resolved_document=resolved_document,
        )
