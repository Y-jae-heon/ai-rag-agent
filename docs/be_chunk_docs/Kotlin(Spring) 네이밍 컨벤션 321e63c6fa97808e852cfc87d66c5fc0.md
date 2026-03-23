# Kotlin(Spring) 네이밍 컨벤션

생성일: 2026년 3월 12일 오후 8:25
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 8:25
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 8:28
버전: r0
ID: BE-37
활성여부: Active

## Title

Kotlin(Spring) 네이밍 컨벤션

## Rule

## 파일 & 디렉토리

- 파일 : 파스칼 케이스 (ex: `GlobalException.kt`)
- 디렉토리 : 소문자, 복합어가 필요하다면 스네이크 케이스 (ex: `golf_course`)

## 클래스 & 인터페이스

- 클래스 : 파스칼 케이스 (ex: `SensorService`)
- 인터페이스 : 파스칼 케이스 (ex: `Runnable`)

## 변수 & 함수

- 프로퍼티 : 카멜케이스
- 함수 : 카멜케이스
- 불리언값 : `is`, `has`, `can` 등의 접두사 사용

## 데이터베이스

- 테이블 : 스네이크 케이스
- 컬럼 : DB에서는 스네이크 케이스, 엔티티는 카멜 케이스 사용
    - JPA의 자동 변환기능 사용

```kotlin
@Comment("코스 정보 초기화 유무")
var isInit: Boolean = false  // DB의 is_init 필드와 매핑
```

## DTO

- DTO는 레이어별로 분리를 지향합니다.
    - Controller, Service, Repository에서 사용하는 DTO를 각각 만들어 서비스 레이어의 재사용성을 높이고 변경에 대한 사이드이펙트를 줄입니다.
    - 불필요한 분리라면 굳이 분리가 없어도 됩니다.
    - Controller : `Req` `Res`
    - Service : `Command`
    - Repository : `Query`
    - 라는 용어를 붙여 레이어를 구분합니다.
    - ex) 유저를 찾는 API에서
        - Controller DTO : `FindUserReq`
        - Service DTO : `FindUserCommand`
        - Repository DTO : `FindUserQuery`
- DTO 컨벤션은 `{동작}{도메인}{추가옵션}` 를 사용합니다.
    - ex)
        - `FindUserListReq`
        - `FindUserListRes` → `FindUserListItemRes`
        - `FindUserWithAccountReq`
        - `FindUserRes`
        - `UpdateUserReq`
- DTO는 **data class**로 선언합니다. 불변성을 위해 `val` 프로퍼티를 기본으로 합니다.
- DTO → 다른 DTO 또는 엔티티로의 변환은 DTO의 **companion object**에서 책임집니다.
    - `from` (다른 DTO 또는 엔티티로부터 생성) : companion object의 팩토리 함수
    - `to` (현재 DTO를 다른 DTO 또는 엔티티로 변환) : 멤버 함수
    - 코틀린은 메서드 오버로딩 대신 **이름 있는 인자(named arguments)** 와 **기본값**을 적극 활용합니다.

```kotlin
data class FindLatestVersionRes(
    val id: Long,
    val platform: AppPlatform,
    val version: String,
    val minSupportedVersion: String,
    val releaseNotes: String?,
    val releasedAt: LocalDateTime
) {
    companion object {
        fun from(appVersion: AppVersion): FindLatestVersionRes {
            return FindLatestVersionRes(
                id = appVersion.id!!,
                platform = appVersion.platform,
                version = appVersion.version,
                minSupportedVersion = appVersion.minSupportedVersion,
                releaseNotes = appVersion.releaseNotes,
                releasedAt = appVersion.releasedAt
            )
        }
    }

    fun toEntity(): AppVersion {
        return AppVersion(
            id = id,
            platform = platform,
            version = version,
            minSupportedVersion = minSupportedVersion,
            releaseNotes = releaseNotes,
            releasedAt = releasedAt
        )
    }
}
```

## Rationale

## Exception

## Override