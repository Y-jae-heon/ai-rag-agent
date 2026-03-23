# Java(Spring) 예외 처리

생성일: 2026년 3월 12일 오후 7:53
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 7:53
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:56
버전: r0
ID: BE-28
활성여부: Active

## Title

Java(Spring) AoP

## Rule

### 예외 처리

- 제어 가능한 비즈니스 로직에서의 예외는 커스텀 예외를 사용합니다.
- 예외는 `@RestControllerAdvice` 에서 일괄 처리합니다.
- 예외 발생 지점에서 에러 로깅을 남겨 추후 유지보수성을 높힙니다.
- 에러코드는 ENUM으로 관리하며 외부 메세지, 코드, 상태값 등을 포함합니다.
- 예외의 기본 구조는 다음과 같습니다.

```java
public enum ErrorCode {

    USER_NOT_FOUND(404, "USER_NOT_FOUND"),
    INVALID_PASSWORD(400, "INVALID_PASSWORD");

    private final int status;
    private final String code;
}
```

```java
class CustomException extends RuntimeException {

    private final ErrorCode errorCode;

    public CustomException(ErrorCode errorCode) {
        this.errorCode = errorCode;
    }
}
```

## Rationale

## Exception

## Override