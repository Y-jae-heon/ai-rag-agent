# Module Plan: indexing

## 역할

docs/ 마크다운 파일을 파싱하여 3개의 ChromaDB 컬렉션을 구축하고 유지한다.

**이 모듈은 서버 기동과 완전히 분리된다.**
인덱싱은 문서 변경 시 수동으로 실행하며, 서버는 기존 인덱스를 읽기만 한다.

| 컬렉션 | 단위 | 용도 |
|--------|------|------|
| document_index | 문서 1개 = 벡터 1개 | 문서 식별 |
| section_index | 섹션(##) 1개 = 벡터 1개 | 요약/섹션 탐색 |
| chunk_index | chunk 1개 = 벡터 1개 | 세부 규칙 추출 |

---

## 실행 모델

| 구분 | 실행 방법 | 시점 |
|------|-----------|------|
| 최초 인덱스 빌드 | `python scripts/ingest.py` | 프로젝트 최초 구성 시 |
| 문서 변경 후 재빌드 | `python scripts/ingest.py --rebuild` | docs/ 파일 추가/수정 시 |
| 특정 컬렉션만 재빌드 | `python scripts/ingest.py --collections document_index` | 부분 업데이트 시 |
| 서버 기동 | `uvicorn src.api.main:app` | 인덱스 빌드 완료 후에만 실행 |

**서버는 인덱싱 코드를 절대 호출하지 않는다.**
`.chroma/` 인덱스가 없으면 서버가 즉시 에러로 종료된다.

---

## 구현할 파일

| 파일 | 역할 |
|------|------|
| `__init__.py` | 모듈 export |
| `config.py` | CHROMA_PERSIST_DIR, CORPUS_DIRS, CHUNK_SIZE 등 설정값 |
| `document_indexer.py` | 문서 단위 인덱싱 (document_index 구축) |
| `section_indexer.py` | 섹션 단위 인덱싱 (section_index 구축) |
| `chunk_indexer.py` | chunk 단위 인덱싱 (chunk_index 구축, v2 방식 개선) |
| `markdown_parser.py` | 마크다운 파일 파싱 유틸 (제목, 섹션, 메타데이터 추출) |
| `manifest.py` | alias_registry.json 로딩 및 메타데이터 조합 |
| `build_index.py` | 빌드 오케스트레이터 — `run(force_rebuild, collections)` 함수 제공 |

별도 위치:
| 파일 | 역할 |
|------|------|
| `scripts/ingest.py` | CLI 진입점 — argparse로 `--rebuild`, `--collections` 옵션 처리 |

---

## build_index.py 핵심 로직

```
run(force_rebuild=False, collections=None):
  1. docs/fe_chunk_docs/, docs/be_chunk_docs/ 파일 목록 수집
  2. markdown_parser.parse_file() 로 각 파일 파싱
  3. document_indexer → document_index upsert
  4. section_indexer  → section_index upsert
  5. chunk_indexer    → chunk_index upsert
  6. .chroma/ingest_manifest.json 기록 (빌드 날짜, 문서 수)
```

`force_rebuild=True` 이면 `.chroma/` 삭제 후 재생성.

---

## 각 파일별 핵심 로직

### markdown_parser.py
```
파일 경로 → title(파일명에서 추출) + canonical_doc_id(파일명 UUID) + sections(## 기준 분리)
domain/stack은 경로로 판단: fe_chunk_docs → frontend, be_chunk_docs → backend
```

### document_indexer.py
```
각 문서 1개 → embedding(title + aliases + section_headings) → document_index upsert
```

### section_indexer.py
```
각 섹션 → embedding(heading + content) → section_index upsert
metadata: canonical_doc_id, section_heading, rule_type, content_span
```

### chunk_indexer.py
```
RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
각 chunk → chunk_index upsert
metadata: canonical_doc_id, section_heading(상위 섹션), domain, stack
```

---

## 인덱스 저장 위치

```
.chroma/
  document_index/
  section_index/
  chunk_index/
  ingest_manifest.json   ← 빌드 날짜, 문서 수 기록
```

## alias_registry.json 위치

`src/convention_qa/indexing/alias_registry.json`

---

## LangChain 컴포넌트

- `OpenAIEmbeddings()` — 모든 임베딩 생성
- `Chroma.from_documents()` — 초기 빌드
- `Chroma.add_documents()` — 증분 업데이트
- `RecursiveCharacterTextSplitter` (chunk_indexer)

---

## 테스트 위치

`tests/test_indexing.py`

---

## 관련 문서

- `ai-work/plans/ingest-separation.md` — 서버-ingest 분리 실행 구조 상세
- 관련 티켓: P0-TK-02, P1-TK-04
