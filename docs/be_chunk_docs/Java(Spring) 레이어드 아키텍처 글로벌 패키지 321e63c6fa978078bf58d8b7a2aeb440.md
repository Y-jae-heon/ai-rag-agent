# Java(Spring) 레이어드 아키텍처 글로벌 패키지

생성일: 2026년 3월 12일 오후 7:53
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 7:53
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:56
버전: r0
ID: BE-29
활성여부: Active

## Title

Java(Spring) 레이어드 아키텍처 글로벌 패키지

## Rule

### annotation

어노테이션과, 이를 이용하는 Resolver, AoP 로직이 포함됩니다.

### config

DataSource, Jpa, Redis 등 설정 정보가 포함됩니다.

### dto

전역적으로 사용하는 DTO 들을 정의합니다. `ObjectResponse` 

### exception

예외와, 예외 전역 핸들러를 정의합니다.

## Rationale

## Exception

## Override