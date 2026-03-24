# Ingest 분리 실행 구조

작성일: 2026-03-23
관련 문서: ai-work/plans/architecture-v3.md, ai-work/plans/langchain-integration.md

## 배경

ChromaDB 인덱스 빌드(ingest)는 서버 기동과 분리되어야 한다.

- 인덱스는 docs/ 파일이 변경될 때만 재빌드가 필요하다
- 서버 매 기동마다 ingest를 실행하면 OpenAI Embedding 비용이 낭비된다
- 인덱스 빌드는 수 분이 걸릴 수 있어 서버 응답 가용성에 영향을 준다

---

## 실행 모델

| 구분               | 명령                                                    | 시점                         |
| ------------------ | ------------------------------------------------------- | ---------------------------- |
| 인덱스 최초 빌드   | `python scripts/ingest.py`                              | 프로젝트 최초 구성 시        |
| 인덱스 전체 재빌드 | `python scripts/ingest.py --rebuild`                    | docs/ 파일 대거 변경 시      |
| 특정 컬렉션 재빌드 | `python scripts/ingest.py --collections document_index` | 부분 업데이트 시             |
| 서버 기동          | `uvicorn src.api.main:app`                              | 인덱스 빌드 완료 후에만 실행 |

**핵심 원칙**: 서버 기동 시 인덱싱 코드를 절대 호출하지 않는다.

---

## 구현 파일 구조

```
scripts/
  ingest.py                    # CLI 진입점

src/
  convention_qa/
    indexing/
      config.py                # 설정값 (CHROMA_PERSIST_DIR, CORPUS_DIRS 등)
      build_index.py           # 빌드 오케스트레이터 — run() 함수
      markdown_parser.py       # 파일 파싱 유틸
      document_indexer.py      # document_index 구축
      section_indexer.py       # section_index 구축
      chunk_indexer.py         # chunk_index 구축
      manifest.py              # alias_registry 로딩
  api/
    main.py                    # FastAPI lifespan — 인덱스 검증
    dependencies.py            # get_chroma_client() — 인덱스 없으면 RuntimeError
```

---

## scripts/ingest.py 설계

```
argparse 옵션:
  --rebuild              기존 .chroma/ 삭제 후 전체 재빌드
  --collections [...]    지정된 컬렉션만 빌드 (기본: 전체 3개)

실행 흐름:
  1. python-dotenv로 .env 로딩 (OPENAI_API_KEY)
  2. build_index.run(force_rebuild, collections) 호출
  3. 진행 상황 stdout 출력 (문서 수, 소요 시간)
  4. 완료 후 .chroma/ingest_manifest.json 확인 출력
```

---

## build_index.run() 설계

```
run(force_rebuild: bool = False, collections: list[str] | None = None):
  1. force_rebuild=True이면 .chroma/ 디렉토리 삭제
  2. docs/fe_chunk_docs/, docs/be_chunk_docs/ 파일 목록 수집
  3. 각 .md 파일 → markdown_parser.parse_file() 파싱
  4. document_indexer → document_index upsert
  5. section_indexer  → section_index upsert
  6. chunk_indexer    → chunk_index upsert
  7. .chroma/ingest_manifest.json 기록 (빌드 날짜, 문서 수)
```

---

## 서버 측 인덱스 검증 설계

### dependencies.py

```python
def get_chroma_client() -> chromadb.ClientAPI:
    required_collections = ["document_index", "section_index", "chunk_index"]
    for name in required_collections:
        collection_path = CHROMA_PERSIST_DIR / name
        if not collection_path.exists():
            raise RuntimeError(
                f"Index '{name}' not found. "
                f"Run: python scripts/ingest.py"
            )
    return chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
```

### main.py (lifespan)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 기동 전 인덱스 존재 확인 — 없으면 즉시 종료
    get_chroma_client()
    yield

app = FastAPI(lifespan=lifespan)
```

---

## config.py 설계

```python
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", ".chroma"))
CORPUS_DIRS = [
    Path("docs/fe_chunk_docs"),
    Path("docs/be_chunk_docs"),
]
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
SIMILARITY_THRESHOLD = 0.75
```

`.env`에서 `CHROMA_PERSIST_DIR` 오버라이드 가능.

---

## ingest_manifest.json 구조

```json
{
  "built_at": "2026-03-23T10:00:00+09:00",
  "document_count": 57,
  "collections": {
    "document_index": { "count": 57 },
    "section_index": { "count": 312 },
    "chunk_index": { "count": 890 }
  }
}
```

서버 `/health` 엔드포인트에서 이 파일을 읽어 인덱스 상태를 반환한다.

---

## 검증 시나리오

| 시나리오                 | 명령                                                    | 기대 결과                                                   |
| ------------------------ | ------------------------------------------------------- | ----------------------------------------------------------- |
| 인덱스 없이 서버 기동    | `uvicorn src.api.main:app`                              | RuntimeError + "Run: python scripts/ingest.py" 출력 후 종료 |
| 인덱스 빌드 후 서버 기동 | `python scripts/ingest.py && uvicorn src.api.main:app`  | 정상 기동                                                   |
| 전체 재빌드              | `python scripts/ingest.py --rebuild`                    | .chroma/ 삭제 후 재생성                                     |
| 특정 컬렉션 재빌드       | `python scripts/ingest.py --collections document_index` | document_index만 갱신                                       |
