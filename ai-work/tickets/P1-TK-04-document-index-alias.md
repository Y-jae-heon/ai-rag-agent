# P1-TK-04: Document Index & Alias Schema 도입

우선순위: P1
작성일: 2026-03-23
선행: P0-TK-02 (document_index 초기 구현)
관련 플랜: ai-work/plans/architecture-v3.md §인덱스 구조

## 배경

P0-TK-02에서 구현한 document_index는 기본 메타데이터로 동작한다.
P1에서는 alias 체계를 공식화하고 모든 문서에 alias를 체계적으로 정의한다.

## 목표

- 전체 55개 문서에 alias 목록 정의 및 alias_registry.json 작성
- section_index 컬렉션 구축 (문서별 ## 섹션 단위 인덱싱)
- SummarizeHandler용 representative section assembly 구현

## 범위

### alias_registry.json 구조
```json
{
  "325e63c6fa9780149d90e16c61f7f0e2": {
    "title": "파일 네이밍 컨벤션",
    "aliases": [
      "파일명 컨벤션", "파일명 규칙", "file naming convention",
      "file naming", "파일 이름 규칙"
    ],
    "domain": "frontend",
    "stack": "react",
    "topic": "naming"
  }
}
```

### section_index 구조
각 문서의 ## 헤딩 단위로 분리하여 인덱싱.

```python
# section 파싱 기준
# ## 로 시작하는 라인을 섹션 경계로 사용
# 각 섹션: heading + content (다음 ## 전까지)
```

### SummarizeHandler 로직 (이 티켓에서 구현)
```
1. section_index에서 canonical_doc_id filter로 전체 섹션 수집
2. 섹션 목록을 구조화된 컨텍스트로 조합
3. LLMChain(summarize_prompt)에 전달
4. 3~6개 핵심 항목 요약 생성
```

## 완료 기준

- [ ] alias_registry.json 전체 55개 문서 커버리지
- [ ] section_index 구축 완료
- [ ] SummarizeHandler 구현 및 테스트 통과
- [ ] "파일 네이밍 컨벤션 내용 알려줘" → 3~6개 항목 요약 반환
