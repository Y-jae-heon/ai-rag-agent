# Typescript(NestJS) 네이밍 컨벤션

생성일: 2026년 3월 12일 오후 12:31
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 12:31
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:11
버전: r0
ID: BE-3
활성여부: Active

## Title

NestJS 네이밍 컨벤션

## Rule

### 파일 & 디렉토리

- **파일**: 케밥 케이스 (예: `attachment-board.controller.ts`, `user-profile.service.ts`)
- **디렉토리**: 케밥 케이스 (예: `car-info`, `push-token`)

### 클래스 & 인터페이스

- **클래스**: 파스칼 케이스 (예: `AttachmentService`, `AttachmentBoardController`)
- **인터페이스**: 파스칼 케이스. `I` 접두사를 **사용하지 않습니다** (예: `IUser`가 아닌 `User`).

### 변수 & 함수

- **변수/속성**: 카멜 케이스 (camelCase)
- **함수/메서드**: 카멜 케이스 (camelCase)
- **불리언(Boolean)**: `is`, `has`, `can` 등의 접두사 사용 (예: `isThumbnail`. 단, DB 매핑 필드인 `delYn` 등은 예외)

### 데이터베이스

- **테이블**: 스네이크 케이스 (snake_case, 엔티티 매핑으로 처리됨)
- **컬럼**: DB에서는 스네이크 케이스, 엔티티에서는 카멜 케이스 사용.

### 메소드

- 함수는 `camelCase`를 사용합니다.
- **컨트롤러 레이어 메서드 접두어**:
    - URL에 맞춰 `get`, `generate`, `remove`, `modify` 등의 동사를 사용합니다.
        - GET 메서드는 get 을 사용합니다.
    - 예: `getUser`, `generateUser`, `deleteUser`
- **서비스 레이어**:
    - 동작에 따라 `get`, `generate`, `remove`, `modify` 등의 동사를 사용합니다.
    - 예: `getNotice`, `generateNotice`, `sendEmail`, `uploadImages`
- **레포지토리 레이어**:
    - 데이터베이스 작업에 맞춰 `find`, `create`, `delete`, `update` 등의 동사를 사용합니다.
    - 예: `findNoticeList`, `updateNotice`, `createNotice`

### **DTO**

- DTO는 레이어별로 분리를 지향합니다.
    - Controller, Service, Repository 에서 사용하는 DTO를 각각 만들어 서비스 레이어의 재사용성을 높이고 변경에 대한 사이드이펙트를 줄입니다.
- 동작에 따라 `get`, `generate`, `remove`, `modify` 등의 동사를 사용합니다.
- 예: `getNoticeDto`, `generateNoticeDto`, `sendEmaiLDto`

## Rationale

## Exception

## Override