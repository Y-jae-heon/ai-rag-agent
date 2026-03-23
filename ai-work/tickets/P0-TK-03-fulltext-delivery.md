# P0-TK-03: Fulltext Delivery 경로 도입

우선순위: P0
작성일: 2026-03-23
블로킹: P0-TK-02 완료 후 진행
관련 플랜: ai-work/plans/architecture-v3.md §[5] 원칙4

## 배경

v2에서 "전문 보여줘" 요청이 chunk 기반 QA로 처리되어 원문 반환이 불가능했다.
rag-init-document.md 원인C: fulltext requirement를 RAG로 해결하려 시도한 것이 구조적으로 잘못된 접근이었다.

핵심 결정: **fulltext는 prompt completion이 아니라 controlled file read다.**

## 목표

- FulltextHandler 구현: resolved document 경로에서 파일을 읽어 원문 그대로 반환
- 안전 정책 구현: corpus 허용 경로 외 접근 차단
- fulltext-delivery sub-agent 정의 파일 작성

## 범위

### 구현 대상

**`src/convention_qa/action_routing/`**
- `fulltext_handler.py`: FulltextHandler 구현

**`src/convention_qa/response/`**
- `fulltext_formatter.py`: 원문에 메타데이터 헤더 추가 (title, path)

### 안전 정책
```python
ALLOWED_CORPUS_DIRS = [
    "docs/fe_chunk_docs/",
    "docs/be_chunk_docs/",
]

def is_safe_path(path: str) -> bool:
    abs_path = os.path.abspath(path)
    for allowed in ALLOWED_CORPUS_DIRS:
        if abs_path.startswith(os.path.abspath(allowed)):
            return True
    return False
```

### 응답 형식
```
## [문서 제목]
> 경로: docs/fe_chunk_docs/파일 네이밍 컨벤션 325e63c6...md

---

[원문 내용 그대로]
```

### LLM 사용 정책
FulltextHandler는 LLM을 사용하지 않는다.
원문 이외 어떤 텍스트도 추가하거나 변형하지 않는다.

## 테스트 케이스

| 입력 | 기대 동작 |
|------|-----------|
| resolved path = docs/fe_chunk_docs/파일 네이밍 컨벤션.md | 원문 전체 반환 |
| resolved path = /etc/passwd | 거부 + 에러 응답 |
| resolved path = docs/fe_chunk_docs/존재안함.md | FileNotFoundError 처리 |
| 파일 크기 > 500KB | 경고 + 부분 반환 |

## 완료 기준

- [ ] FulltextHandler 구현 완료
- [ ] 안전 정책 path traversal 테스트 통과
- [ ] "프론트엔드 파일 네이밍 컨벤션 전문 보여줘" → 원문 전체 반환 E2E 테스트 통과
- [ ] LLM 호출 없음 확인 (mock 없이 file read만)
- [ ] fulltext-delivery 에이전트 파일 작성 완료
