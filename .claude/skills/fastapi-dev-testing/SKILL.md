---
name: fastapi-dev-testing
description: "Use this skill for any developer testing operations in the FastAPI developer chatbot project. Triggers when the user wants to start or stop the local API server, send a question/query to the API endpoint to verify its response, or run the pytest test suite. Use this skill whenever you see requests like '서버 시작', '서버 꺼줘', 'API 테스트', '쿼리 날려줘', '테스트 실행', 'run tests', 'start server', 'stop server', or any check that involves the local FastAPI dev server at localhost."
---

# FastAPI Dev Testing

이 프로젝트의 FastAPI 서버(`src.api.main:app`)를 대상으로 하는 4가지 테스팅 작업을 다룹니다.

---

## 1. 서버 시작 (Start Server)

사용자가 서버를 기동하거나 특정 포트로 띄워달라고 하면 아래 명령을 사용합니다.

```bash
SKIP_INDEX_CHECK=true uvicorn src.api.main:app --host 0.0.0.0 --port {PORT} &
sleep 3
echo "서버 기동 확인 중..."
curl -s http://localhost:{PORT}/health
```

**변수:**
- `{PORT}`: 기본값 `8000`. 사용자가 다른 포트를 명시하면 그 값을 사용합니다.

**주의사항:**
- `SKIP_INDEX_CHECK=true`는 ChromaDB 인덱스 체크를 건너뜁니다. 실제 인덱스가 필요한 테스트라면 이 환경변수를 제거합니다.
- 백그라운드 실행(`&`) 후 반드시 `sleep 3`으로 startup을 기다립니다.
- `/health` 엔드포인트로 기동 여부를 확인합니다.

---

## 2. API 쿼리 (Query Endpoint)

사용자가 특정 질문으로 API를 테스트하고 싶을 때 사용합니다.

```bash
curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X POST http://localhost:{PORT}/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "{QUESTION}"}' \
| python3 -c "
import sys
raw = sys.stdin.read()
parts = raw.rsplit('\nHTTP_STATUS:', 1)
body, status = parts[0], parts[1]
print('HTTP Status:', status)
import json
try:
    print(json.dumps(json.loads(body), indent=2, ensure_ascii=False))
except Exception:
    print(body)
"
```

**변수:**
- `{PORT}`: 기본값 `8000`.
- `{QUESTION}`: 사용자가 테스트하려는 질문 문자열. 예: `"FSD 구조 규칙 알려줘"`.

**결과 읽기:**
- `HTTP Status: 200` + `answer` 필드 → 정상
- `HTTP Status: 500` → 서버 오류 (로그 확인 필요)
- `HTTP Status: 422` → 요청 형식 오류 (`question` 필드명 확인)

---

## 3. 서버 종료 (Stop Server)

사용자가 서버를 종료하거나 포트를 해제하고 싶을 때 사용합니다.

```bash
kill $(lsof -ti:{PORT}) 2>/dev/null && echo "포트 {PORT} 서버 종료 완료" || echo "실행 중인 서버 없음"
```

**변수:**
- `{PORT}`: 기본값 `8000`.

---

## 4. 테스트 실행 (Run Tests)

사용자가 pytest를 실행하거나 회귀 테스트를 확인하고 싶을 때 사용합니다.

```bash
pytest {TEST_PATH} -v --tb=short
```

**변수:**
- `{TEST_PATH}`: 기본값 `tests/`. 특정 파일이나 디렉토리를 지정할 수 있습니다.
  - 전체 테스트: `tests/`
  - 특정 파일: `tests/test_compare_handler.py`
  - 특정 테스트 함수: `tests/test_compare_handler.py::TestHandleNormalCase::test_handle_answer_contains_titles`

**pytest가 없는 경우:**
```bash
which pytest || python3 -m pytest {TEST_PATH} -v --tb=short
```

---

## 사용 패턴 예시

사용자가 "FSD 구조 규칙 테스트해줘"처럼 말하면 일반적으로 다음 순서로 진행합니다:

1. 서버가 이미 떠 있는지 확인: `lsof -ti:8000`
2. 없으면 서버 시작 (작업 1)
3. API 쿼리 실행 (작업 2)
4. 필요하면 서버 종료 (작업 3)

사용자가 단순히 "테스트 돌려줘"라고 하면 작업 4만 실행합니다.
