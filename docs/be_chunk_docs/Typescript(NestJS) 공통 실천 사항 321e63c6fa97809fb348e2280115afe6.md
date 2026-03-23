# Typescript(NestJS) 공통 실천 사항

생성일: 2026년 3월 12일 오후 4:17
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 4:17
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:13
버전: r0
ID: BE-12
활성여부: Active

## Title

NestJS 코드 아키텍처 - DTO 패턴

## Rule

### 응답 포맷

- 일관된 API 응답을 위해 `ObjectResponse<T>` 및 `ListResponse<T>` 래퍼를 사용합니다.
- **Raw Entity 반환 금지**: 변환이 필요한 경우 날것의 Entity를 그대로 반환하지 않습니다. DTO나 Entity가 반환되면 Interceptor/Controller 로직(또는 수동 래핑)에 의해 표준 포맷으로 감싸집니다.

### 에러 처리

- 표준 NestJS 예외(`BadRequestException`, `NotFoundException` 등)를 발생시킵니다.
- 글로벌 `HttpExceptionFilter`가 응답 포맷팅을 처리합니다.

### 로깅

- `Winston` 로거를 사용합니다.
- `HttpLoggerInterceptor`가 HTTP 요청을 자동으로 로깅합니다.

### 설정 (Configuration)

- 환경 변수 접근 시 `ConfigService`를 사용합니다.
- 값을 하드코딩하지 않고 상수(`src/shared/constants`)나 환경 변수를 사용합니다.

### Swagger

- 데코레이터를 사용하여 문서를 최신 상태로 유지합니다.
- `swaggerConstants`를 사용하여 태그 이름을 일관되게 관리합니다.

## Rationale

## Exception

## Override