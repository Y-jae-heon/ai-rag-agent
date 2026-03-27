# vector store 검색 시 단어 하나의 차이로 맥락 변경으로 인한 문서 search 문제

### case 1

```
{
    "question: "frontend FSD 구조 규칙 알려줘",
  "candidates": [
    {
      "canonical_doc_id": "322e63c6fa978079af54d3d34b1fb0d2",
      "domain": "frontend",
      "path": "docs/fe_chunk_docs/Git PR 템플릿 322e63c6fa978079af54d3d34b1fb0d2.md",
      "score": 0.34675672649164546,
      "stack": "react",
      "title": "Git PR 템플릿"
    },
    {
      "canonical_doc_id": "325e63c6fa9780d397e9f7a3989944d5",
      "domain": "frontend",
      "path": "docs/fe_chunk_docs/폴더 네이밍 컨벤션 325e63c6fa9780d397e9f7a3989944d5.md",
      "score": 0.3425531352753643,
      "stack": "react",
      "title": "폴더 네이밍 컨벤션"
    },
    {
      "canonical_doc_id": "325e63c6fa978067a124e0c68833a066",
      "domain": "frontend",
      "path": "docs/fe_chunk_docs/FSD 레이어드 아키텍처 개요 325e63c6fa978067a124e0c68833a066.md",
      "score": 0.3424213179946668,
      "stack": "react",
      "title": "FSD 레이어드 아키텍처 개요"
    },
    {
      "canonical_doc_id": "322e63c6fa97804bb9edd3e783536dd7",
      "domain": "frontend",
      "path": "docs/fe_chunk_docs/FSD 레이어드 아키텍처 README 템플릿 322e63c6fa97804bb9edd3e783536dd7.md",
      "score": 0.3406834065416545,
      "stack": "react",
      "title": "FSD 레이어드 아키텍처 README 템플릿"
    },
    {
      "canonical_doc_id": "322e63c6fa9780119c4ed1a23c731d27",
      "domain": "frontend",
      "path": "docs/fe_chunk_docs/Git Branch 전략 322e63c6fa9780119c4ed1a23c731d27.md",
      "score": 0.339739092160469,
      "stack": "react",
      "title": "Git Branch 전략"
    }
  ],
  "confidence": 0.34675672649164546,
  "resolution_strategy": "semantic",
  "resolved": false
}
```

### case 2

```
{
    "question": "FSD 구조 규칙 알려줘",
  "candidates": [
    {
      "canonical_doc_id": "322e63c6fa978079af54d3d34b1fb0d2",
      "domain": "frontend",
      "path": "docs/fe_chunk_docs/Git PR 템플릿 322e63c6fa978079af54d3d34b1fb0d2.md",
      "score": 0.34648049164612155,
      "stack": "react",
      "title": "Git PR 템플릿"
    },
    {
      "canonical_doc_id": "325e63c6fa978067a124e0c68833a066",
      "domain": "frontend",
      "path": "docs/fe_chunk_docs/FSD 레이어드 아키텍처 개요 325e63c6fa978067a124e0c68833a066.md",
      "score": 0.3412961707131824,
      "stack": "react",
      "title": "FSD 레이어드 아키텍처 개요"
    },
    {
      "canonical_doc_id": "321e63c6fa9780348708f402e6f88dc4",
      "domain": "backend",
      "path": "docs/be_chunk_docs/Kotlin(Spring) 테스트 코드 컨벤션 321e63c6fa9780348708f402e6f88dc4.md",
      "score": 0.34112501610344725,
      "stack": "spring",
      "title": "Kotlin(Spring) 테스트 코드 컨벤션"
    },
    {
      "canonical_doc_id": "321e63c6fa9780aebfcccd454d31c824",
      "domain": "backend",
      "path": "docs/be_chunk_docs/Typescript(NestJS) 레이어드 아키텍처 - 서비스 코드 패턴 321e63c6fa9780aebfcccd454d31c824.md",
      "score": 0.33952209293642455,
      "stack": "nestjs",
      "title": "Typescript(NestJS) 레이어드 아키텍처 - 서비스 코드 패턴"
    },
    {
      "canonical_doc_id": "321e63c6fa978017a946c1074781b778",
      "domain": "backend",
      "path": "docs/be_chunk_docs/Typescript(NestJS) 레이어드 아키텍처 디렉토리 구조 321e63c6fa978017a946c1074781b778.md",
      "score": 0.3390974920327163,
      "stack": "nestjs",
      "title": "Typescript(NestJS) 레이어드 아키텍처 디렉토리 구조"
    }
  ],
  "canonical_doc_id": "325e63c6fa978067a124e0c68833a066",
  "confidence": 0.3412961707131824,
  "path": "docs/fe_chunk_docs/FSD 레이어드 아키텍처 개요 325e63c6fa978067a124e0c68833a066.md",
  "resolution_strategy": "keyword_tiebreak",
  "resolved": true,
  "title": "FSD 레이어드 아키텍처 개요"
}
```
