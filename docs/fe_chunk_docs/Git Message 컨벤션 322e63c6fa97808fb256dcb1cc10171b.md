# Git Message 컨벤션

ID: FE-2
버전: r0
생성일: 2026년 3월 13일 오후 3:44
수정 시간: 2026년 3월 16일 오후 12:56
수정자: 무무(염재헌)
역할: FE
작성 상태: 작성완료
작성 시간: 2026년 3월 13일 오후 3:44
작성자: 무무(염재헌)
활성여부: Active

## Title

Git Commit Message Convention

---

## Rule

Git commit 메시지는 **변경 내용을 빠르게 이해할 수 있도록 일정한 형식으로 작성한다.**

기본 구조

```
[prefix]: commit message
```

prefix는 변경 유형을 나타낸다.

사용 가능한 prefix

```
feat
fix
update
init
build
refactor
chore
ui
assets
```

prefix 의미

feat

새로운 기능을 추가할 때 사용한다.

fix

버그 수정 작업에 사용한다.

update

기능 삭제 또는 정책 변경에 사용한다.

init

프로젝트 초기 설정에 사용한다.

build

의존성 변경 또는 build 설정 변경에 사용한다.

refactor

기능 변경 없이 코드 구조를 개선할 때 사용한다.

chore

사소한 코드 정리 작업에 사용한다.

ui

UI 스타일 수정 작업에 사용한다.

assets

이미지 또는 static 파일 변경에 사용한다.

---

### commit 메시지 작성 규칙

commit 메시지는 명령형으로 작성한다.

prefix 뒤에는 `:`와 공백을 사용한다.

문장 끝에 마침표를 사용하지 않는다.

---

### commit 메시지 예시

```
feat: add coupon list page
fix: resolve login token error
refactor: simplify payment service logic
assets: update main banner image
```

---

### 확장 구조

commit 메시지는 다음 구조로 확장할 수 있다.

```
header
body
footer
```

예

```
feat: add coupon list page

- coupon list API 연결
- pagination 구현
```

---

## Rationale

commit 메시지는 코드 변경 이력을 설명하는 핵심 기록이다.

일관된 메시지 규칙은 다음 효과를 제공한다.

- 코드 변경 추적 용이
- 코드 리뷰 이해도 향상
- 자동 changelog 생성 가능

---

## Exception

개인 실험 브랜치에서는 commit 메시지 규칙을 완화할 수 있다.

---

## Override

프로젝트에 따라 prefix 종류는 확장될 수 있다.