# Java(Spring) QueryDSL

생성일: 2026년 3월 12일 오후 7:55
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 7:55
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:58
버전: r0
ID: BE-32
활성여부: Active

## Title

Java(Spring) QueryDSL

## Rule

### 기본 설정

`JPAQueryFactory`를 Bean으로 등록하고 생성자 주입으로 사용합니다.

```java
@Configuration
public class QueryDslConfig {

    @Bean
    public JPAQueryFactory jpaQueryFactory(EntityManager entityManager) {
        return new JPAQueryFactory(entityManager);
    }
}
```

### 사용 기준

단순 조회는 Spring Data JPA 메서드로 처리하고, 아래 조건 중 하나라도 해당되면 QueryDSL을 사용합니다.

- 검색 조건이 2개 이상인 동적 쿼리
- JOIN이 2개 이상 필요한 복잡한 조회
- DTO로 직접 Projection이 필요한 경우
- 서브쿼리, groupBy, having 등 복잡한 집계

### 동적 쿼리

- `BooleanExpression`을 리턴하는 private 메서드로 조건을 분리합니다.
- 조건이 null이면 `null`을 리턴하여 `where` 절에서 자동으로 무시되도록 합니다.

```java
@RequiredArgsConstructor
public class OrderRepositoryImpl implements OrderRepositoryCustom {

    private final JPAQueryFactory queryFactory;

    @Override
    public Page<Order> searchOrders(SearchOrderQuery condition, Pageable pageable) {
        List<Order> content = queryFactory
            .selectFrom(order)
            .leftJoin(order.member, member).fetchJoin()
            .where(
                memberIdEq(condition.getMemberId()),
                statusEq(condition.getStatus()),
                createdAtBetween(condition.getStartDate(), condition.getEndDate())
            )
            .offset(pageable.getOffset())
            .limit(pageable.getPageSize())
            .orderBy(order.createdAt.desc())
            .fetch();

        JPAQuery<Long> countQuery = queryFactory
            .select(order.count())
            .from(order)
            .where(
                memberIdEq(condition.getMemberId()),
                statusEq(condition.getStatus()),
                createdAtBetween(condition.getStartDate(), condition.getEndDate())
            );

        return PageableExecutionUtils.getPage(content, pageable, countQuery::fetchOne);
    }

    private BooleanExpression memberIdEq(Long memberId) {
        return memberId != null ? order.member.id.eq(memberId) : null;
    }

    private BooleanExpression statusEq(OrderStatus status) {
        return status != null ? order.status.eq(status) : null;
    }

    private BooleanExpression createdAtBetween(LocalDateTime start, LocalDateTime end) {
        if (start == null || end == null) return null;
        return order.createdAt.between(start, end);
    }
}
```

### 조건 메서드 작성 규칙

- 리턴 타입은 `BooleanExpression`을 사용합니다. `Predicate`는 조합이 불편하므로 지양합니다.
- 메서드 네이밍은 `{필드명}{조건}` 형태로 작성합니다.
    - 예: `memberIdEq`, `statusIn`, `createdAtBetween`, `nameLike`
- 동일 도메인 내에서 자주 쓰이는 조건은 재사용합니다.

```java
// 소프트 삭제 필터 - 여러 쿼리에서 재사용
private BooleanExpression notDeleted() {
    return order.deletedAt.isNull();
}
```

### Projection

단순 조회는 fetchJoin으로 엔티티를 가져오고, API 응답 전용 조회는 `@QueryProjection`을 사용합니다.

```java
// DTO 생성자에 @QueryProjection 선언
@Getter
public class FindOrderSummaryQuery {

    private final Long orderId;
    private final String memberName;
    private final Integer totalAmount;
    private final OrderStatus status;

    @QueryProjection
    public FindOrderSummaryQuery(Long orderId, String memberName,
                                  Integer totalAmount, OrderStatus status) {
        this.orderId = orderId;
        this.memberName = memberName;
        this.totalAmount = totalAmount;
        this.status = status;
    }
}
```

```java
// Repository에서 사용
public List<FindOrderSummaryQuery> findOrderSummaries(Long memberId) {
    return queryFactory
        .select(new QFindOrderSummaryQuery(
            order.id,
            order.member.name,
            order.totalAmount,
            order.status
        ))
        .from(order)
        .leftJoin(order.member, member)
        .where(
            memberIdEq(memberId),
            notDeleted()
        )
        .fetch();
}
```

`Projections.constructor()`나 `Projections.fields()`는 컴파일 타임에 타입 검증이 안 되므로 지양합니다.

### 페이지네이션

count 쿼리는 반드시 content 쿼리와 분리합니다. `PageableExecutionUtils.getPage()`를 사용하면 content 크기가 pageSize보다 작을 때 count 쿼리를 생략해 성능을 최적화합니다.

```java
// Good - count 쿼리 분리, 필요시에만 실행
JPAQuery<Long> countQuery = queryFactory
    .select(order.count())
    .from(order)
    .where(conditions);

return PageableExecutionUtils.getPage(content, pageable, countQuery::fetchOne);

// Bad - fetchResults() 사용 (deprecated)
QueryResults<Order> results = queryFactory
    .selectFrom(order)
    .fetchResults();
```

### 정렬

Pageable의 Sort를 QueryDSL `OrderSpecifier`로 변환하여 사용합니다. 정렬 대상이 고정적이라면 직접 명시합니다.

```java
// 고정 정렬
.orderBy(order.createdAt.desc())

// 동적 정렬이 필요한 경우
private OrderSpecifier<?> orderSort(Sort sort) {
    for (Sort.Order o : sort) {
        PathBuilder<Order> pathBuilder = new PathBuilder<>(Order.class, "order");
        return new OrderSpecifier(
            o.isAscending() ? com.querydsl.core.types.Order.ASC
                            : com.querydsl.core.types.Order.DESC,
            pathBuilder.get(o.getProperty())
        );
    }
    return order.createdAt.desc();
}
```

### fetchJoin 사용 기준

- 엔티티 그래프가 필요한 경우(서비스 레이어에서 연관 엔티티 접근) → `fetchJoin()` 사용
- DTO Projection으로 필요한 필드만 가져오는 경우 → 일반 `join` 사용
- 컬렉션(`@OneToMany`) fetchJoin은 페이징과 함께 사용하지 않습니다. `@BatchSize`로 대체합니다.

```java
// Good - ToOne 관계 fetchJoin
queryFactory
    .selectFrom(order)
    .leftJoin(order.member, member).fetchJoin()
    .fetch();

// Bad - 컬렉션 fetchJoin + 페이징 (데이터 전체 메모리 로딩)
queryFactory
    .selectFrom(order)
    .leftJoin(order.orderItems, orderItem).fetchJoin()
    .offset(pageable.getOffset())
    .limit(pageable.getPageSize())
    .fetch();
```

### 금지사항

- `fetchResults()`, `fetchCount()`는 deprecated이므로 사용하지 않습니다. count 쿼리를 직접 작성합니다.
- `JPAQueryFactory`를 직접 생성하지 않습니다. Bean 주입으로만 사용합니다.
- Repository 레이어에서 `@Transactional`을 선언하지 않습니다. 트랜잭션은 Service에서 관리합니다.

## Rationale

## Exception

## Override