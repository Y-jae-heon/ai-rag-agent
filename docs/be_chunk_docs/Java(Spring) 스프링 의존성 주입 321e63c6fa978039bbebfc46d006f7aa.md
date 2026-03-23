# Java(Spring) 스프링 의존성 주입

생성일: 2026년 3월 12일 오후 7:44
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 7:44
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:45
버전: r0
ID: BE-23
활성여부: Active

## Title

Java(Spring) 의존성 주입

## Rule

### 주입

- 주입은 생성자 주입을 사용합니다. 이 외에는 사용하지 않습니다.
- lombok (`@RequiredArgsConstructor`) 사용을 권장합니다.
- 주입된 필드는 `private final` 로 사용합니다.

```java
@RequiredArgsConstructor
public class SensorRepository {
  private final JPAQueryFactory queryFactory;
}
```

## Rationale

## Exception

## Override