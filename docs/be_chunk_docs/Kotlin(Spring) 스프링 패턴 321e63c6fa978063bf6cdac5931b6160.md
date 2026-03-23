# Kotlin(Spring) 스프링 패턴

생성일: 2026년 3월 12일 오후 8:26
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 8:26
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 8:28
버전: r0
ID: BE-39
활성여부: Active

## Title

Kotlin(Spring) 스프링 패턴

## Rule

## 주입

- 주입은 **생성자 주입**을 사용합니다. 이 외에는 사용하지 않습니다.
- 코틀린에서는 primary constructor 파라미터에 `private val`로 선언하면 자동으로 생성자 주입이 됩니다.
- `@RequiredArgsConstructor` 없이도 동작합니다 (코틀린 기본 문법).

```kotlin
@Service
class SensorService(
    private val sensorRepository: SensorRepository
) {
    // ...
}
```

## 트랜잭션 관리

- 트랜잭션 경계는 `Service` 레이어에서만 선언합니다.
- 클래스 레벨에서 `@Transactional(readOnly = true)`를 선언하고, 쓰기 메서드에서만 `@Transactional`을 오버라이딩합니다.
    - 더티체킹 스킵, 읽기전용 DB로 전환 가능

```kotlin
@Service
@Transactional(readOnly = true)
class UserService(
    private val userRepository: UserRepository
) {

    fun getUser(id: Long): User {
        return userRepository.findById(id)
            .orElseThrow { CustomException(ErrorCode.USER_NOT_FOUND) }
    }

    @Transactional
    fun updateUser(id: Long, command: UpdateUserCommand): User {
        val user = getUser(id)
        user.updateInfo(command.name, command.nickname)
        return user
    }
}
```

## 데이터소스 관리

- 데이터 소스가 1개인 경우 Spring의 Auto Config를 사용합니다.
- 데이터소스가 2개 이상인 경우 데이터소스와 트랜잭션 매니저를 직접 선언합니다.

```kotlin
@Configuration
class BatchConfig {

    @Primary
    @Bean
    @ConfigurationProperties(prefix = "spring.datasource.batch")
    fun batchDataSource(): DataSource {
        return DataSourceBuilder.create().build()
    }

    @Primary
    @Bean
    fun batchDataSourceTransactionManager(): PlatformTransactionManager {
        return DataSourceTransactionManager(batchDataSource())
    }
}
```

```kotlin
@Configuration
class JpaConfig {

    @Bean
    @ConfigurationProperties(prefix = "spring.datasource.business")
    fun businessDataSource(): DataSource {
        return DataSourceBuilder.create().build()
    }

    @Bean
    fun dataEntityManagerFactory(): LocalContainerEntityManagerFactoryBean {
        return LocalContainerEntityManagerFactoryBean().apply {
            dataSource = businessDataSource()
            setPackagesToScan("batch.adapter.out.persistence", "core.entity")
            jpaVendorAdapter = HibernateJpaVendorAdapter()
            setJpaPropertyMap(
                mapOf(
                    "hibernate.hbm2ddl.auto" to "none",
                    "hibernate.show_sql" to "true",
                    "hibernate.physical_naming_strategy" to
                        "org.hibernate.boot.model.naming.CamelCaseToUnderscoresNamingStrategy",
                    "hibernate.format_sql" to "true",
                    "hibernate.dialect" to "org.hibernate.dialect.MySQL8Dialect"
                )
            )
        }
    }

    @Bean
    fun dataTransactionManager(): PlatformTransactionManager {
        return JpaTransactionManager().apply {
            entityManagerFactory = dataEntityManagerFactory().`object`
        }
    }
}
```

## AoP

- AoP는 도메인 로직이 아니기 때문에 `global` 패키지에 선언합니다.
- AoP에 비즈니스 로직은 포함되지 않습니다.

## 예외 처리

- 제어 가능한 비즈니스 로직에서의 예외는 커스텀 예외를 사용합니다.
- 예외는 `@RestControllerAdvice`에서 일괄 처리합니다.
- 예외 발생 지점에서 에러 로깅을 남겨 추후 유지보수성을 높힙니다.
- 에러코드는 enum class로 관리하며 외부 메세지, 코드, 상태값 등을 포함합니다.

```kotlin
enum class ErrorCode(
    val status: Int,
    val code: String
) {
    USER_NOT_FOUND(404, "USER_NOT_FOUND"),
    INVALID_PASSWORD(400, "INVALID_PASSWORD")
}
```

```kotlin
class CustomException(
    val errorCode: ErrorCode
) : RuntimeException(errorCode.code)
```

## Rationale

## Exception

## Override