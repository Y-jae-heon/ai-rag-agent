# Module Plan: indexing

## 역할

docs/ 마크다운 파일을 파싱하여 3개의 ChromaDB 컬렉션을 구축하고 유지한다.

| 컬렉션 | 단위 | 용도 |
|--------|------|------|
| document_index | 문서 1개 = 벡터 1개 | 문서 식별 |
| section_index | 섹션(##) 1개 = 벡터 1개 | 요약/섹션 탐색 |
| chunk_index | chunk 1개 = 벡터 1개 | 세부 규칙 추출 |

## 구현할 파일

| 파일 | 역할 |
|------|------|
| `__init__.py` | 모듈 export |
| `document_indexer.py` | 문서 단위 인덱싱 (document_index 구축) |
| `section_indexer.py` | 섹션 단위 인덱싱 (section_index 구축) |
| `chunk_indexer.py` | chunk 단위 인덱싱 (chunk_index 구축, v2 방식 개선) |
| `markdown_parser.py` | 마크다운 파일 파싱 유틸 (제목, 섹션, 메타데이터 추출) |
| `manifest.py` | alias_registry.json 로딩 및 메타데이터 조합 |
| `build_index.py` | 전체 인덱스 빌드 스크립트 진입점 |

## 핵심 로직

### markdown_parser.py
```
파일 경로 → title(파일명에서 추출) + canonical_doc_id(파일명 UUID) + sections(## 기준 분리)
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

## 인덱스 저장 위치

```
.chroma/
  document_index/
  section_index/
  chunk_index/
```

## alias_registry.json 위치

`src/convention_qa/indexing/alias_registry.json`

## LangChain 컴포넌트

- `OpenAIEmbeddings()` — 모든 임베딩 생성
- `Chroma.from_documents()` — 초기 빌드
- `Chroma.add_documents()` — 증분 업데이트
- `RecursiveCharacterTextSplitter` (chunk_indexer)

## 테스트 위치

`tests/test_indexing.py`

## 관련 티켓

P0-TK-02, P1-TK-04
