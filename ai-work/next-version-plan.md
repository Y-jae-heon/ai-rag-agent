# RAG v4 구현 기준 문서

## 구현 방향

- v4는 v3 코드를 이관하지 않는 greenfield rewrite로 구현한다.
- 1차 범위는 검색 중심 MVP다.
- 메타데이터는 `doc_id`, `title`, `source_path`, `section_id`, `section_type`만 유지한다.
- `domain`, `framework`, `language`는 retrieval metadata에서 제거한다.
- `/api/v4/query`와 `/health`를 기준으로 FastAPI를 구성한다.
- Gradio UI는 API만 호출하는 단순 채팅 + debug 보기 형태로 구성한다.

## 구현 메모

- H1 중심 문서를 위해 `# Title / # Rule / # Rationale / # Exception / # Override`를 semantic section으로 직접 파싱한다.
- dense retrieval은 `document_dense`, `section_dense` 2개 Chroma 컬렉션으로 구성한다.
- sparse retrieval은 local Chroma `search()`가 미구현이므로, Chroma BM25 tokenizer/config를 사용한 Python-side sparse index로 구현한다.
- fusion은 weighted RRF를 Python 레이어에서 수행한다.
- embedding baseline은 `text-embedding-3-small` 유지, A/B benchmark는 별도 스크립트로 지원한다.

