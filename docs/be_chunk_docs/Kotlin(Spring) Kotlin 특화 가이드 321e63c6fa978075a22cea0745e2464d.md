# Kotlin(Spring) Kotlin 특화 가이드

생성일: 2026년 3월 12일 오후 8:29
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 8:29
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 8:30
버전: r0
ID: BE-43
활성여부: Active

## Title

Kotlin(Spring) 코틀린 특화 가이드

## Rule

## Gradle 플러그인 설정

```kotlin
// build.gradle.kts
plugins {
    kotlin("plugin.spring")    // open 자동 처리 (@Service, @Controller 등)
    kotlin("plugin.jpa")       // no-arg 생성자 자동 생성 (@Entity, @Embeddable 등)
    kotlin("kapt")             // QueryDSL annotation processing
}

// QueryDSL kapt 설정
dependencies {
    kapt("com.querydsl:querydsl-apt:${querydslVersion}:jpa")
}
```

## Null Safety 활용

- 엔티티 ID는 `Long? = null`로 선언하고, 저장 후에는 `!!` 또는 `requireNotNull`로 접근합니다.
- Repository의 단일 조회는 nullable 타입으로 리턴합니다.
- Service에서 null 처리 시 `?: throw` 패턴을 적극 활용합니다.

```kotlin
// Repository
fun findByEmail(email: String): User?

// Service
fun getByEmail(email: String): User {
    return userRepository.findByEmail(email)
        ?: throw CustomException(ErrorCode.USER_NOT_FOUND)
}
```

## 확장 함수 활용

- 유틸리티성 변환은 확장 함수로 작성합니다.

```kotlin
// Entity → DTO 변환을 확장 함수로도 가능 (선택적)
fun User.toSummaryRes(): UserSummaryRes {
    return UserSummaryRes(
        id = this.id!!,
        name = this.name,
        email = this.email
    )
}
```

## Scope Functions

- `apply` : 객체 초기화에 사용
- `let` : null 체크 + 변환에 사용
- `also` : 부수 효과(로깅 등)에 사용
- `run`/`with` : 객체의 여러 메서드를 호출할 때 사용

```kotlin
// apply - 객체 설정
val config = LocalContainerEntityManagerFactoryBean().apply {
    dataSource = businessDataSource()
    setPackagesToScan("com.example.entity")
}

// let - null safe 변환
val result = findByEmail(email)?.let { UserRes.from(it) }

// also - 부수 효과
return orderRepository.save(order).also {
    logger.info { "[Order] 주문 저장 완료 id=${it.id}" }
}
```

## Rationale

## Exception

## Override