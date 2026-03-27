# developer-chat-bot-v3

사내 개발 컨벤션 문서를 대상으로 동작하는 RAG 프로젝트다. 현재 기본 실행 경로는 v4 greenfield 파이프라인 기준이다.

## 현재 기준

- 서버 엔트리포인트: `src.api.main:app`
- 질의 API: `POST /api/v4/query`
- 인덱스 빌드 스크립트: `python scripts/ingest_v4.py`
- 벤치마크 스크립트: `python scripts/benchmark_v4.py`
- Gradio UI: `python chat_ui/app.py`

참고:

- 저장소 안에 v3 코드도 남아 있지만, 현재 FastAPI 기본 엔트리포인트는 v4를 바라본다.
- v4 계획 문서는 [ai-docs/rag-v4-greenfield-plan.md](/Users/yeomjaeheon/Documents/dev/ai-tf/developer-chat-bot-v3/ai-docs/rag-v4-greenfield-plan.md)에 있다.

## 사전 요구사항

- Python 3.11+
- OpenAI API Key
- 인터넷 연결

선택:

- LangSmith trace를 보려면 `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` 설정

## 설치

```bash
pip install -r requirements.txt
```

`.env` 예시:

```bash
OPENAI_API_KEY=sk-...
RAG_SERVER_URL=http://localhost:8000
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=developer-chat-bot-v4
LANGCHAIN_API_KEY=...
```

## 실행 순서

### 1. v4 인덱스 빌드

최초 1회는 전체 인덱스를 빌드해야 한다.

```bash
python scripts/ingest_v4.py --rebuild
```

특정 인덱스만 다시 만들 때:

```bash
python scripts/ingest_v4.py --collections document_dense
python scripts/ingest_v4.py --collections section_dense
python scripts/ingest_v4.py --collections section_sparse
```

빌드 결과는 `.chroma_v4/` 아래에 저장된다.

생성 항목:

- `.chroma_v4/document_dense/`
- `.chroma_v4/section_dense/`
- `.chroma_v4/section_sparse/index.json`
- `.chroma_v4/ingest_manifest.json`

### 2. API 서버 실행

```bash
uvicorn src.api.main:app --reload
```

기본 주소:

- `http://localhost:8000`

인덱스 체크를 잠시 건너뛰고 서버만 띄우고 싶을 때:

```bash
SKIP_INDEX_CHECK=true uvicorn src.api.main:app --reload
```

### 3. Gradio UI 실행

별도 터미널에서 실행한다.

```bash
python chat_ui/app.py
```

기본 주소:

- `http://localhost:7860`

현재 UI는 다음만 제공한다.

- 질문 입력
- 답변 확인
- debug 출력 보기

domain/framework dropdown은 제거되어 있다.

### 4. 벤치마크 실행

v4 retrieval benchmark는 아래 스크립트로 실행한다.

```bash
python scripts/benchmark_v4.py
```

기본 benchmark 케이스 파일:

- `ai-work/benchmarks/rag_v4_queries.json`

## API 사용법

### POST /api/v4/query

질문을 보내면 answer, citation, top document를 반환한다.

요청 예시:

```json
{
  "question": "FSD 구조 규칙 알려줘",
  "debug": true
}
```

요청 필드:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `question` | string | 필수 | 자연어 질문 |
| `debug` | boolean | 선택 | retrieval/debug payload 포함 여부 |

응답 예시:

```json
{
  "answer": "FSD 구조는 ...",
  "citations": [
    {
      "title": "FSD 레이어드 아키텍처 개요",
      "source_path": "docs/fe_chunk_docs/FSD 레이어드 아키텍처 개요 325e63c6fa978067a124e0c68833a066.md",
      "section_id": "325e63...::section::1",
      "section_type": "rule",
      "excerpt": "프론트엔드 아키텍처는 Feature-Sliced Design ..."
    }
  ],
  "top_documents": [
    {
      "doc_id": "325e63c6fa978067a124e0c68833a066",
      "title": "FSD 레이어드 아키텍처 개요",
      "source_path": "docs/fe_chunk_docs/FSD 레이어드 아키텍처 개요 325e63c6fa978067a124e0c68833a066.md",
      "score": 0.031,
      "matched_by": ["section_dense", "section_sparse"]
    }
  ],
  "confidence": 0.031,
  "needs_clarification": false,
  "trace_id": "..."
}
```

응답 필드:

| 필드 | 타입 | 설명 |
|------|------|------|
| `answer` | string | 최종 답변 |
| `citations` | array | 답변 근거 섹션 목록 |
| `top_documents` | array | fusion 이후 상위 문서 후보 |
| `confidence` | float | 상위 문서 점수 |
| `needs_clarification` | boolean | 근거 부족 여부 |
| `trace_id` | string \| null | LangSmith trace id |
| `debug` | object \| null | debug=true일 때 retrieval 상세 |

### GET /health

v4 인덱스 상태를 반환한다.

응답 예시:

```json
{
  "status": "ok",
  "indices": ["document_dense", "section_dense", "section_sparse"],
  "manifest": {
    "built_at": "...",
    "document_count": 54,
    "section_count": 521,
    "collections": {
      "document_dense": 54,
      "section_dense": 521,
      "section_sparse": 521
    }
  },
  "version": "v4"
}
```

## curl 예시

```bash
curl -X POST http://localhost:8000/api/v4/query \
  -H "Content-Type: application/json" \
  -d '{"question": "FSD 구조 규칙 알려줘"}'
```

```bash
curl -X POST http://localhost:8000/api/v4/query \
  -H "Content-Type: application/json" \
  -d '{"question": "프론트엔드 FSD 구조 규칙 알려줘", "debug": true}'
```

```bash
curl http://localhost:8000/health
```

## 테스트 실행

전체 테스트:

```bash
pytest -q
```

v4 테스트만:

```bash
pytest -q tests/rag_v4 tests/api/test_query_v4.py
```

## 프로젝트 구조

```text
developer-chat-bot-v3/
├── ai-docs/
│   └── rag-v4-greenfield-plan.md
├── ai-work/
│   ├── benchmarks/
│   │   └── rag_v4_queries.json
│   └── next-version-plan.md
├── chat_ui/
│   ├── app.py
│   ├── config.py
│   └── rag_client.py
├── docs/
│   ├── fe_chunk_docs/
│   └── be_chunk_docs/
├── scripts/
│   ├── benchmark_v4.py
│   ├── ingest.py
│   └── ingest_v4.py
├── src/
│   ├── api/
│   │   ├── dependencies_v4.py
│   │   ├── models_v4.py
│   │   ├── main.py
│   │   └── routes/
│   │       ├── health.py
│   │       └── query_v4.py
│   ├── convention_qa/      # 기존 v3 코드
│   └── rag_v4/
│       ├── answering/
│       ├── ingest/
│       ├── retrieval/
│       ├── config.py
│       ├── models.py
│       ├── normalization.py
│       └── service.py
├── tests/
│   ├── api/
│   └── rag_v4/
├── .chroma/                # 기존 v3 인덱스
├── .chroma_v4/             # 현재 v4 인덱스
├── requirements.txt
└── .env
```

## 운영 메모

- v4는 metadata filter 기반 retrieval이 아니라 dense+sparse hybrid retrieval 기준이다.
- `domain`, `framework`는 API 입력과 retrieval metadata에서 제거되어 있다.
- baseline embedding model은 `text-embedding-3-small`이다.
- BM25 경로는 [Chroma BM25 문서](https://docs.trychroma.com/integrations/embedding-models/chroma-bm25)를 기준으로 설계했다.
