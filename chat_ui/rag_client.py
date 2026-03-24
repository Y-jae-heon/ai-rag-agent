import httpx
from chat_ui.config import RAG_SERVER_URL

_TIMEOUT = 30.0


def query(question: str, domain: str, stack: str) -> dict:
    payload = {
        "question": question,
        "domain": None if domain == "auto" else domain,
        "stack": None if stack == "auto" else stack,
        "intent_hint": None,
    }
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(f"{RAG_SERVER_URL}/api/v1/query", json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        return {"error": "RAG 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."}
    except httpx.TimeoutException:
        return {"error": "서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."}
    except httpx.HTTPStatusError as e:
        return {"error": f"서버 오류가 발생했습니다. (HTTP {e.response.status_code})"}
    except Exception as e:
        return {"error": f"알 수 없는 오류가 발생했습니다: {str(e)}"}


def health() -> dict:
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(f"{RAG_SERVER_URL}/health")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return {"error": str(e)}
