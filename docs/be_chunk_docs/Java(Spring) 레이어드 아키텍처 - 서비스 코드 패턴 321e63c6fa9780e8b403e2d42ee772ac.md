# Java(Spring) 레이어드 아키텍처 - 서비스 코드 패턴

생성일: 2026년 3월 12일 오후 7:29
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 7:29
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:44
버전: r0
ID: BE-19
활성여부: Active

## Title

Java(Spring) 레이어드 아키텍처 - 서비스 코드 패턴

## Rule

### Service

- 역할 : 비즈니스 로직 수행, 트랜잭션 관리
- 로직 : 서비스 레이어에서 로직은 도메인 로직의 오케스트레이션을 관리합니다. 즉 핵심 도메인 로직은 엔티티에 작성합니다.
- 리턴타입 : 특별한 목적이 있는 메서드가 아니라면 기본적으로 DTO가 아닌 **엔티티 형태로 리턴**합니다.
    - 서비스 레이어의 재사용성을 높이기 위해 엔티티를 리턴하고, 최종 사용처에서 엔티티를 가공해서 사용합니다.
    - ex) 컨트롤러 레이어에서 엔티티 구조를 숨기기 위해 Response Dto 로 변환해 리턴합니다.

```java
@Transactional
public Order createOrder(CreateOrderReq dto) {
	// 1. 상품 조회
	List<Product> products = productRepository.findAllById(dto.getProductIds());
	
	// 2. 주문 엔티티 생성 (수량 검증등 도메인 로직은 엔티티로 위임)
	Order order = Order.create(
	  dto.getMemberId(),
	  products,
	  dto.getItems()
	);
	
	// 3. 주문 저장
	orderRepository.save(order);
	
	// 4. 저장된 주문 리턴 (추후 재사용성을 위해)
	return order;
}
```

## Rationale

## Exception

## Override