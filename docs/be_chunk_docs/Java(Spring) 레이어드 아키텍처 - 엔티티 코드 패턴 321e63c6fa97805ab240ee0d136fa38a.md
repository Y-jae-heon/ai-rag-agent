# Java(Spring) 레이어드 아키텍처 - 엔티티 코드 패턴

생성일: 2026년 3월 12일 오후 7:42
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 7:42
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:44
버전: r0
ID: BE-22
활성여부: Active

## Title

Java(Spring) 레이어드 아키텍처 - 엔티티 코드 패턴

## Rule

### Entity

- **역할** : 도메인 상태와 비즈니스 로직을 관리
- JPA 엔티티를 기본 엔티티로 사용합니다.
    - 별도의 순수 엔티티를 가지지 않는 이유로는 순수 엔티티와 JPA 엔티티 분리시 발생하는 변환 비용으로 인한 비용 상승, JPA의 더티체킹 기능을 사용하지 못합니다.
- `CoreEntity` 를 상속해 감사 기능과 소프트 삭제를 기본 정책으로 사용합니다.
    
    ```java
    @MappedSuperclass
    @Getter
    @EntityListeners(AuditingEntityListener.class)
    
    public abstract class CoreEntity {
    
      @CreationTimestamp
      @Column(name = "created_at", updatable = false, nullable = false)
      private LocalDateTime createdAt;
    
      @UpdateTimestamp
      @Column(name = "updated_at", nullable = false)
      private LocalDateTime updatedAt;
    
      @Column(name = "deleted_at")
      private LocalDateTime deletedAt;
    
      public void markDeleted() {
        this.deletedAt = LocalDateTime.now();
      }
    
      public boolean isDeleted() {
        return deletedAt != null;
      }
    }
    ```
    
- 연관관계 필드는 최 하단으로 몰아둡니다.
- `@Column` 을 사용하여 컬럼 정보의 명시적 선언을 권장합니다.
    - **nullable**, length 등을 명시합니다.
- 도메인 무결성을 지키기 위해 `Setter` 사용을 지양합니다.
- ENUM 타입은 `EnumType.STRING` 을 사용합니다.
- 식별자는 기본적으로 `GenerationType.IDENTITY` 를 사용합니다.

### 연관관계

- 연관관계는 **단방향**을 기본으로 설정합니다.
    - 양방향 연관관계가 필요한 경우 연관관계를 설정할 수 있는 메서드를 사용합니다.
    
    ```java
    // Order (주인) 쪽에 편의 메서드 작성
    public void addOrderItem(OrderItem item) {
        this.orderItems.add(item);
        item.setOrder(this);     // 반대편도 함께 세팅
    }
    ```
    
- 연관관계는 LAZY 로딩을 기본으로 합니다. `fetch = FetchType.LAZY`
- `@OneToMany` 와 같은 컬렉션 필드는 안정성을 위해 바로 초기화를 진행합니다.
- 외래키 제약조건을 사용하지 않습니다. `foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT)`

```java
@Entity
@Table(name = "user")
public class UserJpaEntity extends CoreEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(nullable = false, updatable = false)
    private Long id;

    @Column(nullable = false)
    private String email;

    private LocalDateTime lastLoggedInAt;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(
        name = "department_id",
        foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT)
    )
    private DepartmentJpaEntity department;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(
        name = "team_id",
        foreignKey = @ForeignKey(ConstraintMode.NO_CONSTRAINT)
    )
    private TeamJpaEntity team;

}
```

## Rationale

## Exception

## Override