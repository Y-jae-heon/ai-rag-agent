# Plan: Gradio Chat UI (별도 서버 연동)

작성일: 2026-03-23

---

## 개요

기존 RAG 서버(FastAPI, `src/api/`)는 `POST /api/v1/query`와 `GET /health` API를 제공한다.
Gradio UI는 이 서버와 **별도 프로세스**로 구동되며, HTTP 클라이언트로 연동한다.
같은 레포 내 `chat_ui/` 디렉토리에 배치하되, 기존 `src/` 코드는 전혀 import하지 않는다.

---

## 연동 구조

```
[ 사용자 브라우저 ]
        |
        | HTTP (localhost:7860)
        v
[ Gradio App (chat_ui/app.py) ]
        |
        | HTTP (localhost:8000)
        v
[ RAG FastAPI Server (src/api/main.py) ]
        |
        v
[ ChromaDB + LLM Pipeline ]
```

---

## 목표 파일 구조

```
chat_ui/
├── app.py          # Gradio 앱 진입점
├── rag_client.py   # RAG 서버 HTTP 클라이언트 (httpx 사용)
└── config.py       # RAG_SERVER_URL 등 환경변수 로딩
```

변경 대상 기존 파일:
- `.env` — `RAG_SERVER_URL` 항목 추가
- `requirements.txt` — `gradio>=4.0.0` 추가

---

## UI 레이아웃

```
┌──────────────┬──────────────────────────────────────┐
│   Settings   │     Developer Convention Q&A Bot      │
│              ├──────────────────────────────────────┤
│ Domain:      │                                      │
│ [auto  ▼]    │  [Bot] 안녕하세요! 개발 컨벤션...    │
│              │  [You] 파일 네이밍 컨벤션 알려줘      │
│ Stack:       │  [Bot] ...                           │
│ [auto  ▼]    │                                      │
│              ├──────────────────────────────────────┤
│ [초기화]     │  질문 입력...              [전송]     │
└──────────────┴──────────────────────────────────────┘
```

- **Domain dropdown**: `auto` / `frontend` / `backend`
- **Stack dropdown**: `auto` / `react` / `spring` / `nestjs` / `kotlin`
- **채팅 히스토리**: `gr.Chatbot` (type="messages")
- **응답 메시지 하단**: `answer_type` + `resolved_document.title` 메타정보 표시

---

## 파일별 구현 상세

### `chat_ui/config.py`

```python
from dotenv import load_dotenv
import os

load_dotenv()

RAG_SERVER_URL = os.getenv("RAG_SERVER_URL", "http://localhost:8000")
```

### `chat_ui/rag_client.py`

- `httpx.Client` (동기) 사용 — Gradio 기본 이벤트 루프가 동기
- `query(question, domain, stack) -> dict`
  - `POST {RAG_SERVER_URL}/api/v1/query`
  - payload: `{"question": ..., "domain": ..., "stack": ...}`
  - `domain="auto"` → `domain=None` 변환 후 전송
- `health() -> dict`
  - `GET {RAG_SERVER_URL}/health`
- 타임아웃 30초
- 서버 미기동 / 네트워크 오류 시 사용자 친화적 에러 메시지 반환

### `chat_ui/app.py`

- `gr.Blocks` 기반 레이아웃
- 좌측 컬럼 (사이드바):
  - `gr.Dropdown` — domain 선택
  - `gr.Dropdown` — stack 선택
  - `gr.Button` — 대화 초기화
- 우측 컬럼 (메인):
  - `gr.Chatbot(type="messages")` — 채팅 히스토리
  - `gr.Textbox` + `gr.Button` — 입력 + 전송
- 전송 로직:
  1. rag_client.query() 호출
  2. `answer` 텍스트 + `[answer_type | resolved_document]` 메타 footer 조합
  3. Chatbot에 메시지 추가
- 초기화 버튼: 채팅 히스토리 비우기

---

## API 요청/응답 명세 (참조)

### Request — POST /api/v1/query
```json
{
  "question": "파일 네이밍 컨벤션 알려줘",
  "domain": "frontend",
  "stack": "react",
  "intent_hint": null
}
```

### Response
```json
{
  "answer": "...",
  "answer_type": "summary",
  "intent": "summarize",
  "resolved_document": {
    "canonical_doc_id": "325e63c6...",
    "title": "파일 네이밍 컨벤션",
    "path": "docs/fe_chunk_docs/..."
  },
  "sources": []
}
```

---

## 실행 방법

```bash
# 터미널 1: RAG 서버 기동
uvicorn src.api.main:app --port 8000

# 터미널 2: Gradio UI 기동
python chat_ui/app.py
# → http://localhost:7860 에서 접속
```

---

## 변경 파일 요약

| 파일 | 작업 |
|------|------|
| `chat_ui/config.py` | 신규 생성 |
| `chat_ui/rag_client.py` | 신규 생성 |
| `chat_ui/app.py` | 신규 생성 |
| `requirements.txt` | `gradio>=4.0.0` 추가 |
| `.env` | `RAG_SERVER_URL=http://localhost:8000` 추가 |

---

## 검증 시나리오

| # | 시나리오 | 기대 결과 |
|---|----------|-----------|
| 1 | 서버 기동 후 UI 접속 | 채팅 초기 메시지 표시 |
| 2 | domain=frontend, stack=react 선택 후 질문 | 필터 반영된 API 호출 및 응답 표시 |
| 3 | domain=auto 선택 후 질문 | domain=null 로 API 호출 |
| 4 | 초기화 버튼 클릭 | 채팅 히스토리 비워짐 |
| 5 | RAG 서버 미기동 상태에서 질문 | 에러 메시지 표시 (앱 크래시 없음) |
