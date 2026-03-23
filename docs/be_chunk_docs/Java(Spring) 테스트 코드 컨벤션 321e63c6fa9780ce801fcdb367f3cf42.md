# Java(Spring) 테스트 코드 컨벤션

생성일: 2026년 3월 12일 오후 8:18
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 8:18
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 8:19
버전: r0
ID: BE-34
활성여부: Active

## 1. 테스트 종류 및 범위

| 테스트 종류 | 어노테이션/도구 | 범위 | 속도 |
| --- | --- | --- | --- |
| 단위 테스트 | `@ExtendWith(MockitoExtension.class)` | 단일 클래스 | 빠름 |
| 슬라이스 테스트 (Web) | `@WebMvcTest` | Controller 레이어 | 보통 |
| 슬라이스 테스트 (DB) | `@DataJpaTest` | Repository 레이어 | 보통 |
| 통합 테스트 | `@SpringBootTest` | 전체 컨텍스트 | 느림 |

**원칙**: 테스트 피라미드를 준수합니다. 단위 테스트를 최대한 많이 작성하고, 통합 테스트는 핵심 흐름에만 사용합니다.

```
        /\
       /  \        ← @SpringBootTest (적게)
      /----\
     /      \      ← @WebMvcTest, @DataJpaTest (적당히)
    /--------\
   /          \    ← Unit Test with Mockito (많이)
  /____________\
```

---

## 2. 네이밍 컨벤션

### 2-1. 테스트 클래스명

- 테스트 대상 클래스명 + `Test` 접미사를 사용합니다.

```java
// ✅ 올바른 예
class OrderServiceTest { }
class OrderControllerTest { }
class OrderRepositoryTest { }

// ❌ 잘못된 예
class TestOrderService { }
class OrderServiceTests { }
```

### 2-2. 테스트 메서드명

- **한글 또는 영문 모두 허용**하나, 팀 내 한 가지로 통일합니다.
- 형식: `[메서드명]_[시나리오]_[기대결과]` 또는 자연어 서술

```java
// ✅ 영문 형식
@Test
void createOrder_whenOutOfStock_throwsException() { }

// ✅ 한글 형식 (권장 - 가독성 우선)
@Test
void 재고_부족_시_주문_생성하면_예외가_발생한다() { }

// ✅ @DisplayName 활용 (영문 메서드 + 한글 설명)
@Test
@DisplayName("재고가 부족할 때 주문을 생성하면 OutOfStockException이 발생한다")
void createOrder_whenOutOfStock_throwsException() { }

// ❌ 잘못된 예
@Test
void test1() { }

@Test
void testCreateOrder() { }
```

### 2-3. @DisplayName 규칙

- `@DisplayName`은 **조건 + 행위 + 결과** 형태로 작성합니다.
- `~하면 ~한다` 형태의 자연어 서술을 사용합니다.

```java
// ✅ 올바른 예
@DisplayName("이미 취소된 주문을 다시 취소하면 IllegalStateException이 발생한다")
@DisplayName("유효한 회원이 상품을 장바구니에 담으면 장바구니 항목이 추가된다")

// ❌ 잘못된 예
@DisplayName("주문 취소 테스트")
@DisplayName("test cancel order")
```

---

## 3. 테스트 구조 (Given-When-Then)

모든 테스트는 **Given-When-Then** 패턴으로 작성합니다. 주석으로 구분을 명시합니다.

```java
@Test
@DisplayName("유효한 주문 요청이 들어오면 주문이 정상적으로 생성된다")
void createOrder_withValidRequest_returnsCreatedOrder() {
    // given
    Member member = MemberFixture.createDefaultMember();
    Product product = ProductFixture.createProductWithStock(10);
    OrderCreateRequest request = new OrderCreateRequest(member.getId(), product.getId(), 2);

    given(memberRepository.findById(member.getId())).willReturn(Optional.of(member));
    given(productRepository.findById(product.getId())).willReturn(Optional.of(product));

    // when
    OrderResponse response = orderService.createOrder(request);

    // then
    assertThat(response.getStatus()).isEqualTo(OrderStatus.PENDING);
    assertThat(response.getQuantity()).isEqualTo(2);
}
```

**규칙**:

- `// given`, `// when`, `// then` 주석을 항상 명시합니다.
- 각 섹션은 빈 줄로 구분합니다.
- `when` 섹션은 단일 동작(메서드 호출) 하나만 포함합니다.

---

## 4. 단위 테스트 (Unit Test)

### 4-1. 기본 구조

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @InjectMocks
    private OrderService orderService;

    @Mock
    private OrderRepository orderRepository;

    @Mock
    private ProductRepository productRepository;

    @Mock
    private MemberRepository memberRepository;
}
```

### 4-2. 도메인 객체 단위 테스트

외부 의존성이 없는 도메인 객체는 순수 단위 테스트로 작성합니다.

```java
class OrderTest {

    @Test
    @DisplayName("주문 수량이 0 이하이면 주문을 생성할 수 없다")
    void createOrder_withZeroQuantity_throwsException() {
        // given
        int invalidQuantity = 0;

        // when & then
        assertThatThrownBy(() -> new Order(invalidQuantity))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("주문 수량은 1개 이상이어야 합니다.");
    }
}
```

### 4-3. @Nested 클래스를 활용한 테스트 그룹화

관련된 테스트는 `@Nested`로 그룹화합니다.

```java
class OrderServiceTest {

    @Nested
    @DisplayName("주문 생성 시")
    class CreateOrder {

        @Test
        @DisplayName("재고가 충분하면 주문이 생성된다")
        void success() { }

        @Test
        @DisplayName("재고가 부족하면 예외가 발생한다")
        void failWhenOutOfStock() { }
    }

    @Nested
    @DisplayName("주문 취소 시")
    class CancelOrder {

        @Test
        @DisplayName("대기 중인 주문은 취소할 수 있다")
        void success() { }

        @Test
        @DisplayName("이미 배송된 주문은 취소할 수 없다")
        void failWhenAlreadyShipped() { }
    }
}
```

---

## 5. 통합 테스트 (Integration Test)

### 5-1. 기본 구조

```java
@SpringBootTest
@Transactional
class OrderIntegrationTest {

    @Autowired
    private OrderService orderService;

    @Autowired
    private MemberRepository memberRepository;

    @Autowired
    private ProductRepository productRepository;

    @Test
    @DisplayName("주문부터 결제까지 전체 흐름이 정상 동작한다")
    void orderAndPayment_fullFlow_success() {
        // given
        Member member = memberRepository.save(MemberFixture.createDefaultMember());
        Product product = productRepository.save(ProductFixture.createProductWithStock(10));

        // when
        OrderResponse orderResponse = orderService.createOrder(
                new OrderCreateRequest(member.getId(), product.getId(), 2)
        );

        // then
        assertThat(orderResponse.getId()).isNotNull();
        assertThat(orderResponse.getStatus()).isEqualTo(OrderStatus.PENDING);
    }
}
```

**규칙**:

- `@SpringBootTest`는 통합 테스트에만 사용합니다. 불필요한 컨텍스트 로딩을 피합니다.
- `@Transactional`을 클래스 레벨에 선언하여 테스트 후 롤백을 보장합니다.
- 실제 외부 서비스(결제, 메일 등)는 `@MockBean`으로 대체합니다.

### 5-2. 외부 의존성 처리

```java
@SpringBootTest
@Transactional
class OrderIntegrationTest {

    @MockBean
    private PaymentGateway paymentGateway; // 외부 결제 서비스는 Mock으로 대체

    @MockBean
    private EmailSender emailSender; // 이메일 발송은 Mock으로 대체
}
```

---

## 6. 슬라이스 테스트

### 6-1. Controller 테스트 (`@WebMvcTest`)

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private OrderService orderService;

    @Test
    @DisplayName("POST /api/orders - 유효한 요청이면 201 Created를 반환한다")
    void createOrder_withValidRequest_returns201() throws Exception {
        // given
        OrderCreateRequest request = new OrderCreateRequest(1L, 1L, 2);
        OrderResponse response = OrderResponse.builder()
                .id(1L)
                .status(OrderStatus.PENDING)
                .build();

        given(orderService.createOrder(any())).willReturn(response);

        // when & then
        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(1L))
                .andExpect(jsonPath("$.status").value("PENDING"))
                .andDo(print());
    }

    @Test
    @DisplayName("POST /api/orders - 수량이 없으면 400 Bad Request를 반환한다")
    void createOrder_withoutQuantity_returns400() throws Exception {
        // given
        OrderCreateRequest request = new OrderCreateRequest(1L, 1L, null); // quantity 누락

        // when & then
        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }
}
```

### 6-2. Repository 테스트 (`@DataJpaTest`)

```java
@DataJpaTest
@ActiveProfiles("test")
class OrderRepositoryTest {

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private TestEntityManager em;

    @Test
    @DisplayName("회원 ID로 주문 목록을 조회하면 해당 회원의 주문만 반환된다")
    void findByMemberId_returnsMemberOrders() {
        // given
        Member member = em.persist(MemberFixture.createDefaultMember());
        Order order1 = em.persist(OrderFixture.createOrder(member));
        Order order2 = em.persist(OrderFixture.createOrder(member));
        em.flush();
        em.clear();

        // when
        List<Order> orders = orderRepository.findByMemberId(member.getId());

        // then
        assertThat(orders).hasSize(2)
                .extracting(Order::getMember)
                .extracting(Member::getId)
                .containsOnly(member.getId());
    }
}
```

---

## 7. Fixture 및 테스트 데이터 관리

### 7-1. Fixture 클래스 작성 규칙

테스트 데이터는 별도의 Fixture 클래스로 분리합니다.

```java
// src/test/java/com/example/fixture/MemberFixture.java
public class MemberFixture {

    public static Member createDefaultMember() {
        return Member.builder()
                .email("test@example.com")
                .name("테스트유저")
                .status(MemberStatus.ACTIVE)
                .build();
    }

    public static Member createMemberWithEmail(String email) {
        return Member.builder()
                .email(email)
                .name("테스트유저")
                .status(MemberStatus.ACTIVE)
                .build();
    }

    public static Member createInactiveMember() {
        return Member.builder()
                .email("inactive@example.com")
                .name("비활성유저")
                .status(MemberStatus.INACTIVE)
                .build();
    }
}
```

**규칙**:

- Fixture 클래스는 `src/test/java` 하위에 `fixture` 패키지로 분리합니다.
- `createDefault*()` 메서드는 가장 일반적인 케이스의 객체를 반환합니다.
- 특정 값이 필요한 경우 파라미터를 받는 메서드를 추가합니다.
- Fixture 클래스는 `public static` 팩토리 메서드만 포함합니다.

### 7-2. @ParameterizedTest 활용

여러 케이스를 반복 테스트할 때 사용합니다.

```java
@ParameterizedTest
@DisplayName("잘못된 수량으로 주문 시 예외가 발생한다")
@ValueSource(ints = {0, -1, -100})
void createOrder_withInvalidQuantity_throwsException(int invalidQuantity) {
    assertThatThrownBy(() -> new Order(invalidQuantity))
            .isInstanceOf(IllegalArgumentException.class);
}

@ParameterizedTest
@DisplayName("다양한 주문 상태에 따라 취소 가능 여부가 결정된다")
@CsvSource({
        "PENDING, true",
        "CONFIRMED, true",
        "SHIPPED, false",
        "DELIVERED, false",
        "CANCELLED, false"
})
void isCancellable_byOrderStatus(OrderStatus status, boolean expected) {
    // given
    Order order = OrderFixture.createOrderWithStatus(status);

    // when
    boolean result = order.isCancellable();

    // then
    assertThat(result).isEqualTo(expected);
}
```

---

## 8. Assertion 작성 원칙

### 8-1. AssertJ 사용

`JUnit5`의 기본 `Assertions` 대신 **AssertJ**를 사용합니다.

```java
// ❌ JUnit5 기본 Assertions 사용 금지
assertEquals(expected, actual);
assertTrue(result);
assertNotNull(response);

// ✅ AssertJ 사용
assertThat(actual).isEqualTo(expected);
assertThat(result).isTrue();
assertThat(response).isNotNull();
```

### 8-2. 체이닝을 활용한 가독성 향상

```java
// ❌ 분리된 assertions
assertThat(response.getId()).isNotNull();
assertThat(response.getStatus()).isEqualTo(OrderStatus.PENDING);
assertThat(response.getQuantity()).isEqualTo(2);

// ✅ SoftAssertions으로 묶기 (모든 실패를 한번에 확인)
assertSoftly(softly -> {
    softly.assertThat(response.getId()).isNotNull();
    softly.assertThat(response.getStatus()).isEqualTo(OrderStatus.PENDING);
    softly.assertThat(response.getQuantity()).isEqualTo(2);
});
```

### 8-3. 예외 검증

```java
// ✅ 예외 타입과 메시지 모두 검증
assertThatThrownBy(() -> orderService.createOrder(invalidRequest))
        .isInstanceOf(OutOfStockException.class)
        .hasMessage("재고가 부족합니다. 상품 ID: 1");

// ✅ 특정 예외 타입만 검증
assertThatExceptionOfType(OutOfStockException.class)
        .isThrownBy(() -> orderService.createOrder(invalidRequest));

// ✅ 예외 없이 정상 실행 검증
assertThatCode(() -> orderService.createOrder(validRequest))
        .doesNotThrowAnyException();
```

### 8-4. 컬렉션 검증

```java
List<Order> orders = orderService.getOrders(memberId);

// ✅ 크기와 내용 동시 검증
assertThat(orders)
        .hasSize(3)
        .extracting(Order::getStatus)
        .containsExactlyInAnyOrder(
                OrderStatus.PENDING,
                OrderStatus.CONFIRMED,
                OrderStatus.SHIPPED
        );

// ✅ 특정 필드 기반 검증
assertThat(orders)
        .extracting("id", "status")
        .contains(
                tuple(1L, OrderStatus.PENDING),
                tuple(2L, OrderStatus.CONFIRMED)
        );
```

---

## 9. Mocking 전략

### 9-1. Mockito BDDMockito 사용

`Mockito.when()` 대신 **BDDMockito** 스타일을 사용합니다.

```java
import static org.mockito.BDDMockito.*;

// ❌ 기존 Mockito 스타일
when(orderRepository.findById(anyLong())).thenReturn(Optional.of(order));
verify(orderRepository, times(1)).save(any(Order.class));

// ✅ BDDMockito 스타일
given(orderRepository.findById(anyLong())).willReturn(Optional.of(order));
then(orderRepository).should(times(1)).save(any(Order.class));
```

### 9-2. 인자 매처 (Argument Matchers)

```java
// ✅ 정확한 값을 알 때
given(orderRepository.findById(1L)).willReturn(Optional.of(order));

// ✅ 타입만 알 때
given(orderRepository.save(any(Order.class))).willReturn(savedOrder);

// ✅ 특정 조건을 만족해야 할 때
given(orderRepository.save(argThat(o -> o.getQuantity() > 0))).willReturn(savedOrder);

// ❌ 혼용 금지 - 하나라도 매처 쓰면 전부 매처를 사용해야 함
given(service.method(1L, any())).willReturn(result); // ❌ 컴파일 에러 아니지만 런타임 에러
given(service.method(eq(1L), any())).willReturn(result); // ✅ eq()로 감싸야 함
```

### 9-3. void 메서드 Mocking

```java
// ✅ void 메서드에서 예외 발생시키기
willThrow(new RuntimeException("메일 발송 실패"))
        .given(emailSender).send(any());

// ✅ void 메서드 호출 검증
then(emailSender).should().send(any());
then(emailSender).should(never()).send(any());
```

### 9-4. @Spy 사용 기준

```java
// ✅ 일부 메서드만 Mocking하고 나머지는 실제 구현을 사용할 때
@Spy
private OrderPriceCalculator priceCalculator; // 실제 객체를 감시

// ✅ 특정 메서드만 stubbing
doReturn(1000).when(priceCalculator).calculateDiscount(any());
```

---

## 10. 테스트 격리 및 독립성

### 10-1. 테스트 간 의존성 제거

```java
// ❌ 테스트 순서에 의존 - 금지
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class OrderServiceTest {

    static Long savedOrderId; // 공유 상태 - 금지

    @Test
    @Order(1)
    void createOrder() {
        savedOrderId = orderService.create(...).getId();
    }

    @Test
    @Order(2)
    void cancelOrder() {
        orderService.cancel(savedOrderId); // 이전 테스트에 의존
    }
}

// ✅ 각 테스트는 독립적으로 실행 가능해야 함
class OrderServiceTest {

    @Test
    void cancelOrder_withPendingOrder_success() {
        // given - 이 테스트 내에서 모든 준비를 완료
        Order order = OrderFixture.createPendingOrder();
        given(orderRepository.findById(anyLong())).willReturn(Optional.of(order));

        // when
        orderService.cancel(1L);

        // then
        assertThat(order.getStatus()).isEqualTo(OrderStatus.CANCELLED);
    }
}
```

### 10-2. 통합 테스트 데이터 격리

```java
// ✅ @Transactional로 각 테스트 후 롤백
@SpringBootTest
@Transactional // 각 테스트 메서드 실행 후 자동 롤백
class OrderIntegrationTest { }

// ✅ @BeforeEach로 초기화
@DataJpaTest
class OrderRepositoryTest {

    @BeforeEach
    void setUp() {
        orderRepository.deleteAll();
    }
}
```

### 10-3. 테스트 프로파일

```yaml
# src/test/resources/application-test.yml
spring:
  datasource:
    url: jdbc:h2:mem:testdb;MODE=MySQL
  jpa:
    hibernate:
      ddl-auto: create-drop
```

```java
@ActiveProfiles("test")
@DataJpaTest
class OrderRepositoryTest { }
```

---

## 11. 금지 패턴 (Anti-Patterns)

### 11-1. 테스트에서 절대 금지

```java
// ❌ Thread.sleep 사용 금지 - 비결정적 테스트
Thread.sleep(1000);

// ❌ System.out.println 사용 금지 - 로그 프레임워크 또는 andDo(print()) 사용
System.out.println("결과: " + response);

// ❌ 테스트 내 조건 분기 금지 - 각각 별도 테스트로 분리
if (condition) {
    assertThat(result).isEqualTo(A);
} else {
    assertThat(result).isEqualTo(B);
}

// ❌ 비어있는 테스트 금지
@Test
void createOrder() {
    // TODO: 나중에 작성
}

// ❌ 프로덕션 코드에서만 쓰이는 메서드를 테스트를 위해 추가 금지
// 테스트를 위해 public getter를 추가하는 행위
```

### 11-2. Mocking 관련 금지 패턴

```java
// ❌ 테스트 대상(SUT) 자체를 Mock 금지
@InjectMocks
private OrderService orderService;

@Spy // ❌ 테스트 대상에 @Spy 사용 금지
private OrderService orderService;

// ❌ 과도한 Mocking - 비즈니스 로직 검증 없이 구현만 검증
given(orderService.createOrder(any())).willReturn(mockResponse);
// ...
verify(orderService).createOrder(any()); // 구현 세부사항만 검증
```

### 11-3. Assertion 관련 금지 패턴

```java
// ❌ assertTrue/assertFalse 단독 사용 - 실패 메시지가 불명확
assertTrue(order.isCancellable());

// ❌ 너무 많은 단언 - 테스트 범위가 모호해짐
// 하나의 테스트는 하나의 행위를 검증해야 함

// ❌ 검증 없는 테스트 (assertThat 누락)
@Test
void createOrder_shouldNotThrow() {
    orderService.createOrder(request); // 아무것도 검증하지 않음
}

// ✅ 명시적으로 예외 없음을 검증
@Test
void createOrder_shouldNotThrow() {
    assertThatCode(() -> orderService.createOrder(request))
            .doesNotThrowAnyException();
}
```

---

## 12. 패키지 구조

```
src/
├── main/
│   └── java/com/example/
│       └── domain/
│           └── order/
│               ├── Order.java
│               ├── OrderController.java
│               ├── OrderService.java
│               └── OrderRepository.java
└── test/
    └── java/com/example/
        ├── domain/
        │   └── order/
        │       ├── OrderTest.java                  # 도메인 단위 테스트
        │       ├── OrderController.java            # 컨트롤러 슬라이스 테스트
        │       ├── OrderServiceTest.java           # 서비스 단위 테스트
        │       └── OrderRepositoryTest.java        # 레포지토리 슬라이스 테스트
        ├── integration/
        │   └── OrderIntegrationTest.java           # 통합 테스트
        └── fixture/
            ├── MemberFixture.java                  # 회원 픽스처
            ├── ProductFixture.java                 # 상품 픽스처
            └── OrderFixture.java                   # 주문 픽스처
```

**규칙**:

- 테스트 패키지 구조는 프로덕션 코드 패키지 구조를 그대로 따릅니다.
- `fixture` 패키지는 `test` 루트에 공통으로 위치합니다.
- 통합 테스트는 별도 `integration` 패키지로 분리합니다.

---