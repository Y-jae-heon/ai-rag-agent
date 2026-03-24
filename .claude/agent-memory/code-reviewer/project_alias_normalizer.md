---
name: alias_normalizer 설계 패턴 및 해결된 결함
description: alias_normalizer.py의 ASCII/비ASCII 분기 설계, re.ASCII 플래그 적용 배경, 괄호로 끝나는 alias 구조적 결함의 해결 경위
type: project
---

`alias_normalizer.py`는 `isascii()`로 ASCII/비ASCII를 분기하여 ASCII alias는 `\b` 정규식 매칭, 비ASCII(한국어 등)는 단순 `in` 검사를 사용한다.

`re.ASCII` 플래그는 P1-BUG-02에서 추가되었다.
**Why:** 기본 유니코드 모드에서 한국어 글자(`에`, `으`, `로` 등)가 `\w`로 분류되어 `"Java에서"` 같은 입력에서 `\b`가 성립하지 않아 매칭이 실패했다.
**How to apply:** ASCII alias 매칭 로직을 리뷰할 때 이 플래그가 있는지 확인한다. 제거하면 한국어 조사 붙은 입력에서 매칭 실패가 재발한다.

P3-BUG-06에서 `)` 로 끝나는 6개 도달 불가 alias(`Java(Spring)`, `java(spring)`, `Kotlin(Spring)`, `kotlin(spring)`, `Typescript(NestJS)`, `typescript(nestjs)`)를 제거했다. 이 alias들은 `\b` 매칭이 작동하지 않아 영구 미매칭 상태였다.

P3-BUG-06에서 `_STACK_ALIASES` dict 순서가 `spring -> kotlin` 에서 `kotlin -> spring` 순으로 변경되었다.
**Why:** `"Kotlin(Spring)으로 개발"` 입력 시 `"Spring"` alias가 먼저 매칭되어 `"spring"`이 반환되는 의미 오류를 수정하기 위함.
**How to apply:** `_STACK_ALIASES`의 dict 순서는 기능적으로 중요하다. `normalize_stack()`은 first-match-wins 방식이므로, `"kotlin"`이 `"spring"`보다 반드시 앞에 위치해야 한다. 순서 변경 시 `test_kotlin_spring_maps_to_kotlin` 테스트 통과 여부를 확인한다.

현재 알려진 잠재적 갭: `"TypeScript"` 단독 alias가 `_STACK_ALIASES`에 없어 `"TypeScript"` 입력 시 `None`이 반환된다. 의도된 동작인지 미확인.
