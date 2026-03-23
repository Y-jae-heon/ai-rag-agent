# P0-TK-02: Document Resolution 단계 도입

우선순위: P0
작성일: 2026-03-23
블로킹: P0-TK-01 완료 후 진행
관련 플랜: ai-work/plans/architecture-v3.md §[2], §인덱스 구조

## 배경

v2에서 문서명을 명시한 질문도 chunk 검색으로 처리해 원하는 문서를 안정적으로 식별하지 못했다.
v3에서는 document_index를 별도로 구축하고 exact → alias → semantic 순서로 문서를 확정한다.

## 목표

- `document_index` ChromaDB 컬렉션 구축 및 인덱싱 파이프라인 구현
- exact match → alias match → semantic search 3단계 resolution 구현
- 현재 docs/fe_chunk_docs/, docs/be_chunk_docs/ 문서 전체 인덱싱

## 범위

### 구현 대상

**`src/convention_qa/indexing/`**
- `document_indexer.py`: 마크다운 파일을 파싱해 document_index에 적재
- `manifest.py`: 문서 메타데이터 manifest (title, aliases, domain, stack, section_headings)
- `alias_registry.py`: 문서별 alias 목록 관리

**`src/convention_qa/document_resolution/`**
- `resolver.py`: `DocumentResolver` 클래스 — 3단계 resolution 로직
- `models.py`: `DocumentResolutionResult`, `DocumentCandidate` Pydantic 모델

### document_index 메타데이터 필드
```python
{
    "canonical_doc_id": "325e63c6fa9780149d90e16c61f7f0e2",
    "title": "파일 네이밍 컨벤션",
    "aliases": '["파일명 컨벤션", "file naming", "파일 이름"]',  # JSON string
    "path": "docs/fe_chunk_docs/파일 네이밍 컨벤션 325e63c6fa9780149d90e16c61f7f0e2.md",
    "domain": "frontend",
    "stack": "react",
    "topic": "naming",
    "doc_type": "convention",
    "section_headings": '["개요", "컴포넌트 파일", "훅 파일", "테스트 파일"]',
    "language": "ko"
}
```

## 현재 문서 목록 및 alias 계획

### Frontend (docs/fe_chunk_docs/)
| 파일명 | aliases 계획 |
|--------|-------------|
| 파일 네이밍 컨벤션 | file naming, 파일명 규칙 |
| 폴더 네이밍 컨벤션 | folder naming, 폴더명 규칙 |
| 네이밍 컨벤션 개요 | naming convention overview |
| FSD 레이어드 아키텍처 개요 | FSD, feature sliced design |
| Git Branch 전략 | 브랜치 전략, git flow |
| Git Message 컨벤션 | 커밋 메시지, commit convention |

### Backend (docs/be_chunk_docs/)
| 파일명 | aliases 계획 |
|--------|-------------|
| Java(Spring) 네이밍 컨벤션 | 자바 네이밍, spring naming |
| Kotlin(Spring) 네이밍 컨벤션 | 코틀린 네이밍, kotlin naming |
| Typescript(NestJS) 네이밍 컨벤션 | 네스트 네이밍, nestjs naming |
| Java(Spring) 테스트 코드 컨벤션 | 자바 테스트, spring test |

## 테스트 케이스

| document_query | domain | 기대 결과 |
|----------------|--------|-----------|
| "파일 네이밍 컨벤션" | frontend | exact match, confidence > 0.95 |
| "파일명 규칙" | frontend | alias match |
| "FSD" | frontend | alias match (FSD 레이어드 아키텍처) |
| "네이밍 컨벤션" | backend, stack=spring | semantic match → Java 네이밍 |
| "존재하지않는문서" | null | unresolved |

## 완료 기준

- [ ] document_index 구축 스크립트 구현 완료
- [ ] 현재 fe/be 문서 전체 (약 55개) 인덱싱 완료
- [ ] exact match 테스트 통과
- [ ] alias match 테스트 통과
- [ ] semantic match 테스트 통과 (threshold 0.75)
- [ ] unresolved 케이스 처리 확인
