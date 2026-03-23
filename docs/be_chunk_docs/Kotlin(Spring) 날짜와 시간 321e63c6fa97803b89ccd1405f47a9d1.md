# Kotlin(Spring) 날짜와 시간

생성일: 2026년 3월 12일 오후 8:27
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 8:27
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 8:28
버전: r0
ID: BE-40
활성여부: Active

## Title

Kotlin(Spring) 날짜와 시간

## Rule

## TimezoneConfig

JVM의 기본 타임존은 KST로 설정합니다.

```kotlin
@Configuration
class TimeZoneConfig {

    @PostConstruct
    fun init() {
        TimeZone.setDefault(TimeZone.getTimeZone("Asia/Seoul"))
    }
}
```

## Controller로부터 입력

- Controller로부터 날짜 입력이 필요한 경우 `OffsetDateTime` 타입으로 받습니다.
    - 타임존 오프셋 정보를 포함해 받을 수 있음
    - 이후 하위 레이어로는 `LocalDateTime`으로 변환해 전달

## Rationale

## Exception

## Override