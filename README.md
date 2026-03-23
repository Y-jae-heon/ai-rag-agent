# developer-chat-bot-v3

개발 컨벤션 문서(FE/BE)에 대해 자연어로 질문하면 의도에 맞는 답변을 반환하는 QA API 서버.

## 개요

v3는 단순한 chunk 검색이 아닌 **intent 기반 실행 시스템**이다. 사용자의 질문 의도를 5가지로 분류하고, 각 의도에 최적화된 방식으로 문서를 찾아 응답을 생성한다.

| Intent | 설명 | 예시 질문 |
|--------|------|-----------|
| `fulltext` | 문서 원문 그대로 반환 (LLM 없음) | "파일 네이밍 컨벤션 전문 보여줘" |
| `summarize` | 문서 내용 요약 (LLM) | "파일 네이밍 컨벤션 내용 알려줘" |
| `extract` | 특정 규칙/정보 추출 (LLM + MMR) | "테스트 파일 네이밍 규칙 알려줘" |
| `discover` | 문서 존재 여부 및 구조 확인 (LLM 없음) | "파일 네이밍 컨벤션 문서 있어?" |
| `compare` | 두 문서/스택 규칙 비교 (LLM) | "Java Spring vs Kotlin Spring 네이밍 차이점" |

---

## 빠른 시작

### 사전 요구사항

- Python 3.11+
- OpenAI API Key

### 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에 OPENAI_API_KEY=sk-... 입력
```

### 인덱스 빌드 (최초 1회 필요)

```bash
# 전체 인덱스 빌드 (document_index / section_index / chunk_index)
python scripts/ingest.py

# 특정 컬렉션만 재빌드
python scripts/ingest.py --collections document_index
python scripts/ingest.py --collections section_index chunk_index

# 전체 강제 재빌드
python scripts/ingest.py --rebuild
```

### 서버 실행

```bash
# 프로덕션 모드 (인덱스 빌드 완료 후)
uvicorn src.api.main:app --reload

# 개발 모드 (인덱스 없이 실행)
SKIP_INDEX_CHECK=true uvicorn src.api.main:app --reload
```

기본 포트: `http://localhost:8000`

---

## API 사용법

### POST /api/v1/query

사용자의 자연어 질문을 처리하고 답변을 반환한다.

**요청**

```json
{
  "question": "파일 네이밍 컨벤션 전문 보여줘",
  "domain": "frontend",
  "stack": null,
  "intent_hint": null
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `question` | string | 필수 | 자연어 질문 |
| `domain` | `"frontend"` \| `"backend"` \| null | 선택 | 도메인 힌트 (없으면 자동 감지) |
| `stack` | string \| null | 선택 | 기술 스택 힌트 (예: `"react"`, `"spring"`, `"nestjs"`) |
| `intent_hint` | string \| null | 선택 | 클라이언트가 제공하는 intent 힌트 |

**응답**

```json
{
  "answer": "## 파일 네이밍 컨벤션\n> 경로: docs/fe_chunk_docs/...\n\n---\n\n# 파일 네이밍 컨벤션\n...",
  "answer_type": "fulltext",
  "intent": "fulltext",
  "resolved_document": {
    "canonical_doc_id": "325e63c6fa9780149d90e16c61f7f0e2",
    "title": "파일 네이밍 컨벤션",
    "path": "docs/fe_chunk_docs/파일 네이밍 컨벤션 325e63c6fa9780149d90e16c61f7f0e2.md"
  },
  "sources": [
    {
      "title": "파일 네이밍 컨벤션",
      "path": "docs/fe_chunk_docs/...",
      "domain": "frontend"
    }
  ]
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `answer` | string | 마크다운 형식의 답변 텍스트 |
| `answer_type` | `"fulltext"` \| `"summary"` \| `"extract"` \| `"discover"` \| `"clarify"` | 응답 유형 |
| `intent` | string | 분류된 사용자 의도 |
| `resolved_document` | object \| null | 특정된 문서 정보 |
| `sources` | array | 참조 문서 목록 |

### GET /health

서버 및 인덱스 상태를 확인한다.

```json
{
  "status": "ok",
  "index_exists": true,
  "ingest_manifest": { ... }
}
```

인덱스가 없으면 `status: "degraded"`를 반환한다.

---

## 요청 예시 모음

### curl

```bash
# 문서 원문 조회
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "파일 네이밍 컨벤션 전문 보여줘"}'

# 백엔드 Java Spring 요약
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Java Spring 네이밍 컨벤션 요약해줘", "domain": "backend", "stack": "spring"}'

# 두 스택 비교
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Java Spring과 Kotlin Spring 네이밍 컨벤션 차이점 알려줘"}'
```

### Python

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

response = client.post("/api/v1/query", json={
    "question": "파일 네이밍 컨벤션 전문 보여줘",
    "domain": "frontend"
})

data = response.json()
print(data["answer"])
print(data["answer_type"])  # "fulltext"
```

---

## Slack 연동 가이드

Slack Bolt 앱에서 이 API를 호출하는 기본 패턴이다.

```python
from slack_bolt import App
import httpx

app = App(token="xoxb-...")
CHATBOT_API = "http://localhost:8000"

@app.message("")
def handle_message(message, say):
    question = message.get("text", "")
    if not question:
        return

    with httpx.Client() as client:
        res = client.post(f"{CHATBOT_API}/api/v1/query", json={
            "question": question
        })

    if res.status_code != 200:
        say("오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        return

    data = res.json()
    answer_type = data["answer_type"]
    answer = data["answer"]

    # answer_type에 따른 Slack 메시지 포맷
    if answer_type == "clarify":
        say(f":question: {answer}")
    elif answer_type == "fulltext":
        # 긴 원문은 파일로 업로드하거나 스레드로 이어 붙이는 것을 권장
        say(f":page_facing_up: {answer[:2900]}...")
    else:
        say(answer)
```

**권장 사항:**
- `answer_type == "fulltext"` 응답은 길 수 있으므로 Slack 파일 업로드(`files.upload`) 또는 스레드 분할을 사용할 것
- `answer_type == "clarify"` 시 후보 문서 목록을 버튼 액션으로 안내하면 UX가 개선된다
- `domain` / `stack` 힌트를 채널 ID나 사용자 프로필에서 추론하면 정확도가 높아진다

---

## 웹 애플리케이션 연동 가이드

### Next.js / React (fetch)

```typescript
interface QueryRequest {
  question: string;
  domain?: "frontend" | "backend";
  stack?: string;
}

interface QueryResponse {
  answer: string;
  answer_type: "fulltext" | "summary" | "extract" | "discover" | "clarify";
  intent: string;
  resolved_document: {
    canonical_doc_id: string;
    title: string;
    path: string;
  } | null;
  sources: Array<{ title: string; path: string; domain: string }>;
}

async function askConventionBot(req: QueryRequest): Promise<QueryResponse> {
  const res = await fetch("/api/v1/query", {   // 프록시 설정 권장
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error("API 호출 실패");
  return res.json();
}
```

**answer_type별 렌더링 전략:**

| answer_type | 권장 렌더링 |
|-------------|------------|
| `fulltext` | 마크다운 렌더러 (예: `react-markdown`) |
| `summary` | 마크다운 렌더러, 축약 카드 UI |
| `extract` | 마크다운 렌더러, 출처 하이라이트 |
| `discover` | 구조화 카드 (제목/경로/섹션 목록) |
| `clarify` | 후보 문서 선택 버튼 목록 |

### CORS 설정

웹 앱에서 직접 호출하려면 FastAPI에 CORS 미들웨어를 추가해야 한다.

```python
# src/api/main.py에 추가
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app.example.com"],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)
```

---

## 테스트 실행

```bash
# 단위 테스트 전체 실행 (41개)
python -m pytest tests/ -v

# 특정 핸들러 테스트
python -m pytest tests/test_compare_handler.py -v
```

---

## 프로젝트 구조

```
developer-chat-bot-v3/
├── docs/
│   ├── fe_chunk_docs/       # FE 컨벤션 문서 (16개 마크다운)
│   └── be_chunk_docs/       # BE 컨벤션 문서 (38개 마크다운, Java/Kotlin/NestJS)
├── src/
│   ├── convention_qa/       # 핵심 QA 파이프라인
│   │   ├── query_understanding/    # Intent 분류
│   │   ├── document_resolution/   # 문서 식별
│   │   ├── action_routing/        # 핸들러 라우팅 및 실행
│   │   ├── indexing/              # ChromaDB 인덱스 빌더
│   │   └── response/              # 응답 포맷터
│   └── api/                 # FastAPI 레이어
│       └── routes/
├── scripts/
│   └── ingest.py            # 인덱스 빌드 CLI
├── tests/                   # 단위 테스트
├── .chroma/                 # ChromaDB 영속 스토리지 (gitignore)
├── requirements.txt
└── .env                     # OPENAI_API_KEY
```
