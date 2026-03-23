# FSD 레이어드 아키텍처 - Feature 구조 규칙

ID: FE-55
버전: r1
생성일: 2026년 3월 16일 오후 8:40
수정 시간: 2026년 3월 16일 오후 9:29
수정자: 무무(염재헌)
작성 상태: 작성완료
작성 시간: 2026년 3월 16일 오후 8:40
작성자: 무무(염재헌)
활성여부: Active

# Title

Feature 구조 규칙

# Rule

features 레이어는 **도메인 기준 (도메인 행동)으로 구조화한다.**

구조 예시

```
features
 ├ user
 │   ├ create
 │   ├ update
 │   └ duplicate-check
 │
 ├ auth
 │   ├ login
 │   └ logout
```

각 feature 내부는 다음 구조를 가진다.

```
ui
api
hooks
model
lib
```

예

```
features/user/create
 ├ ui
 │  └ CreateUserForm.tsx
 ├ api
 │  └ create-user.ts
 ├ hooks
 │  └ use-create-user.ts
 ├ model
 │  └ create-user.schema.ts
 └ lib
    └ mappers.ts
```

# Rationale

Feature를 도메인 기준으로 그룹화하면 다음 장점이 있다.

- 도메인 단위 코드 탐색 가능
- 기능 중복 감소
- 유지보수 편의성 증가

동사 기반 구조만 사용하면 다음 문제가 발생한다.

```
create-user
create-station
create-admin
```

도메인 분리가 어려워진다.

# Exception

도메인에 속하지 않는 공통 기능은 다음 위치에 배치한다.

```
shared
```

예

```
shared/validation
shared/forms
```

# Override

특정 프로젝트에서 기능 구조 변경이 필요한 경우 팀 합의를 통해 조정할 수 있다.