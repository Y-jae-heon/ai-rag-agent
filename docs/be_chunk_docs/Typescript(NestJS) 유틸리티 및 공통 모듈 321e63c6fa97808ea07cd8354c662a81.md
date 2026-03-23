# Typescript(NestJS) 유틸리티 및 공통 모듈

생성일: 2026년 3월 12일 오후 4:20
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 4:20
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:13
버전: r0
ID: BE-14
활성여부: Active

## Title

NestJS 코드 아키텍처 - 개발 워크플로우

## Rule

### **날짜 및 시간 (Date & Time)**

모든 api 반환은 기본적으로 KST로 반환합니다.

- **KST 기준**: 서버는 UTC 기반으로 동작하지만, 비즈니스 로직상 한국 시간(KST)이 필요한 경우 `src/shared/utils/date.util.ts`를 사용합니다.
- **변환 함수**:
    - `utcToKst(date)` : DB(UTC) 시간을 KST 문자열(`YYYY-MM-DDTHH:mm:ss`)로 변환 (사용자 표시용).
    - `kstToUtc(string)` : 사용자 입력(KST)을 DB 저장용 UTC Date로 변환.
    - `nowKst()` : 현재 KST 시간을 구함 (배치/스케줄러 등).

### **암호화 (Crypto / PII)**

- **개인정보(PII) 보호** : 주민번호, 전화번호 등 민감 정보는 평문으로 저장하지 않습니다.
- **PiiCryptoService:** `src/shared/crypto/services/pii-crypto.service.ts` 를 주입받아 사용합니다.
    - **알고리즘** : `AES-256-GCM` 을 사용하며, IV와 AuthTag를 포함하여 `Buffer` 형태로 반환합니다.
    - **DB 저장**: `VARBINARY` 타입 컬럼에 저장합니다 (예: `phone_aes VARBINARY(255)` ).
    - **HMAC**: 검색이 필요한 경우(예: 전화번호 검색), 별도의 HMAC 컬럼(`phone_hmac`)에 해시값을 저장하여 비교합니다.

## Rationale

## Exception

## Override