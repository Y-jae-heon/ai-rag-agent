# Kotlin(Spring) QueryDSL

생성일: 2026년 3월 12일 오후 8:29
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 8:29
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 8:29
버전: r0
ID: BE-42
활성여부: Active

## Title

Kotlin(Spring) QueryDSL

## Rule

## 기본 설정

`JPAQueryFactory`를 Bean으로 등록하고 생성자 주입으로 사용합니다.

```kotlin
@Configuration
class QueryDslConfig(
    private val entityManager: EntityManager
) {

    @Bean
    fun jpaQueryFactory(): JPAQueryFactory {
        return JPAQueryFactory(entityManager)
    }
}
```

## 사용 기준

단순 조회는 Spring Data JPA 메서드로 처리하고, 아래 조건 중 하나라도 해당되면 QueryDSL을 사용합니다.

- 검색 조건이 2개 이상인 동적 쿼리
- JOIN이 2개 이상 필요한 복잡한 조회
- DTO로 직접 Projection이 필요한 경우
- 서브쿼리, groupBy, having 등 복잡한 집계

## 동적 쿼리

- `BooleanExpression?`을 리턴하는 private 함수로 조건을 분리합니다.
- 조건이 null이면 `null`을 리턴하여 `where` 절에서 자동으로 무시되도록 합니다.
- 코틀린의 `?.let`을 활용하면 더 간결하게 작성할 수 있습니다.

```kotlin
class OrderRepositoryImpl(
    private val queryFactory: JPAQueryFactory
) : OrderRepositoryCustom {

    override fun searchOrders(condition: SearchOrderQuery, pageable: Pageable): Page<Order> {
        val content = queryFactory
            .selectFrom(order)
            .leftJoin(order.member, member).fetchJoin()
            .where(
                memberIdEq(condition.memberId),
                statusEq(condition.status),
                createdAtBetween(condition.startDate, condition.endDate)
            )
            .offset(pageable.offset)
            .limit(pageable.pageSize.toLong())
            .orderBy(order.createdAt.desc())
            .fetch()

        val countQuery = queryFactory
            .select(order.count())
            .from(order)
            .where(
                memberIdEq(condition.memberId),
                statusEq(condition.status),
                createdAtBetween(condition.startDate, condition.endDate)
            )

        return PageableExecutionUtils.getPage(content, pageable) { countQuery.fetchOne() ?: 0L }
    }

    private fun memberIdEq(memberId: Long?): BooleanExpression? {
        return memberId?.let { order.member.id.eq(it) }
    }

    private fun statusEq(status: OrderStatus?): BooleanExpression? {
        return status?.let { order.status.eq(it) }
    }

    private fun createdAtBetween(start: LocalDateTime?, end: LocalDateTime?): BooleanExpression? {
        if (start == null || end == null) return null
        return order.createdAt.between(start, end)
    }
}
```

### 조건 메서드 작성 규칙

- 리턴 타입은 `BooleanExpression?`을 사용합니다. `Predicate`는 조합이 불편하므로 지양합니다.
- 메서드 네이밍은 `{필드명}{조건}` 형태로 작성합니다.
    - 예: `memberIdEq`, `statusIn`, `createdAtBetween`, `nameLike`
- 동일 도메인 내에서 자주 쓰이는 조건은 재사용합니다.

```kotlin
// 소프트 삭제 필터 - 여러 쿼리에서 재사용
private fun notDeleted(): BooleanExpression {
    return order.deletedAt.isNull
}
```

## Projection

단순 조회는 fetchJoin으로 엔티티를 가져오고, API 응답 전용 조회는 `@QueryProjection`을 사용합니다.

```kotlin
data class FindOrderSummaryQuery @QueryProjection constructor(
    val orderId: Long,
    val memberName: String,
    val totalAmount: Int,
    val status: OrderStatus
)
```

```kotlin
// Repository에서 사용
fun findOrderSummaries(memberId: Long): List<FindOrderSummaryQuery> {
    return queryFactory
        .select(
            QFindOrderSummaryQuery(
                order.id,
                order.member.name,
                order.totalAmount,
                order.status
            )
        )
        .from(order)
        .leftJoin(order.member, member)
        .where(
            memberIdEq(memberId),
            notDeleted()
        )
        .fetch()
}
```

`Projections.constructor()`나 `Projections.fields()`는 컴파일 타임에 타입 검증이 안 되므로 지양합니다.

## 페이지네이션

count 쿼리는 반드시 content 쿼리와 분리합니다. `PageableExecutionUtils.getPage()`를 사용하면 content 크기가 pageSize보다 작을 때 count 쿼리를 생략해 성능을 최적화합니다.

```kotlin
// Good - count 쿼리 분리, 필요시에만 실행
val countQuery = queryFactory
    .select(order.count())
    .from(order)
    .where(conditions)

return PageableExecutionUtils.getPage(content, pageable) { countQuery.fetchOne() ?: 0L }

// Bad - fetchResults() 사용 (deprecated)
val results = queryFactory
    .selectFrom(order)
    .fetchResults()
```

## 정렬

Pageable의 Sort를 QueryDSL `OrderSpecifier`로 변환하여 사용합니다. 정렬 대상이 고정적이라면 직접 명시합니다.

```kotlin
// 고정 정렬
.orderBy(order.createdAt.desc())

// 동적 정렬이 필요한 경우
private fun orderSort(sort: Sort): OrderSpecifier<*> {
    for (o in sort) {
        val pathBuilder = PathBuilder(Order::class.java, "order")
        return OrderSpecifier(
            if (o.isAscending) com.querydsl.core.types.Order.ASC
            else com.querydsl.core.types.Order.DESC,
            pathBuilder.get(o.property) as Expression<Comparable<*>>
        )
    }
    return order.createdAt.desc()
}
```

## fetchJoin 사용 기준

- 엔티티 그래프가 필요한 경우(서비스 레이어에서 연관 엔티티 접근) → `fetchJoin()` 사용
- DTO Projection으로 필요한 필드만 가져오는 경우 → 일반 `join` 사용
- 컬렉션(`@OneToMany`) fetchJoin은 페이징과 함께 사용하지 않습니다. `@BatchSize`로 대체합니다.

```kotlin
// Good - ToOne 관계 fetchJoin
queryFactory
    .selectFrom(order)
    .leftJoin(order.member, member).fetchJoin()
    .fetch()

// Bad - 컬렉션 fetchJoin + 페이징 (데이터 전체 메모리 로딩)
queryFactory
    .selectFrom(order)
    .leftJoin(order.orderItems, orderItem).fetchJoin()
    .offset(pageable.offset)
    .limit(pageable.pageSize.toLong())
    .fetch()
```

## 금지사항

- `fetchResults()`, `fetchCount()`는 deprecated이므로 사용하지 않습니다. count 쿼리를 직접 작성합니다.
- `JPAQueryFactory`를 직접 생성하지 않습니다. Bean 주입으로만 사용합니다.
- Repository 레이어에서 `@Transactional`을 선언하지 않습니다. 트랜잭션은 Service에서 관리합니다.

## Rationale

## Exception

## Override