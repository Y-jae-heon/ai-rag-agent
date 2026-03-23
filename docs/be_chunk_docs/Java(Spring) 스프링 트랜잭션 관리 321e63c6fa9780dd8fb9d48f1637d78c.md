# Java(Spring) 스프링 트랜잭션 관리

생성일: 2026년 3월 12일 오후 7:44
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 7:44
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:56
버전: r0
ID: BE-24
활성여부: Active

## Title

Java(Spring) 트랜잭션 관리

## Rule

### 트랜잭션

- 트랜잭션 경계는 `Service` 레이어에서만 선언합니다.
- 클래스 레벨에서 `@Transactioinal(readOnly = true)` 를 선언하고, 쓰기 메서드에서만 `@Transactional` 을 오버라이딩 합니다.
    - 더티체킹 스킵, 읽기전용 DB로 전환 가능
- 특별한 이유가 없다면 전파는 기본값인 `REQUIRED` 를 사용합니다.

## Rationale

## Exception

## Override