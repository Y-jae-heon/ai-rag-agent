# Kotlin(Spring) 레이어드 아키텍처 패키지 구조

생성일: 2026년 3월 12일 오후 8:22
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 8:22
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 8:25
버전: r0
ID: BE-36
활성여부: Active

## Title

Kotlin(Spring) 레이어드 아키텍처 패키지 구조

## Rule

```
src/
├── domain/              # 기능 도메인 (비즈니스 로직)
│   ├── [domain-name]/
│   │   ├── controllers/ # 요청 핸들러
│   │   ├── services/    # 비즈니스 로직
│   │   ├── repositories/# 데이터 접근 계층
│   │   ├── entities/    # 데이터베이스 엔티티
│   │   ├── enums/       # ENUM 타입
│   │   └── dtos/        # 데이터 전송 객체 (DTO)
└── global/              # 공통 유틸리티, 상수, 데코레이터
    ├── annotation/      # 어노테이션, AoP, Resolver
    ├── config/          # 설정 파일
    ├── dto/             # 공통 DTO (응답 래퍼 등)
    ├── exception/       # 예외 필터
    └── utils/           # 유틸리티 파일
```

## Rationale

## Exception

## Override