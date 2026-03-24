# P3-BUG-06: alias_normalizer 도달 불가 alias 및 Kotlin(Spring) 의미 오류

우선순위: P3
작성일: 2026-03-24
출처: QA Report — ai-work/qa/qa-report-P1-BUG-02-alias-normalizer-re-ascii-2026-03-24.md Issue #1, Code Review Compliance

## 현상

### 현상 A: Kotlin(Spring) 입력 시 의미 오류

`normalize_stack("Kotlin(Spring)으로 개발")` → `"spring"` (기대: `"kotlin"`)

`Kotlin(Spring)` 조합은 Kotlin 위주 개발을 의미하지만, `"spring"` 문서가 반환된다.

### 현상 B: 도달 불가 alias 6개 잔존

`_STACK_ALIASES` 내 `)` 로 끝나는 alias들(`Java(Spring)`, `kotlin(spring)` 등)은
`re.ASCII` 모드에서 `\\b`가 `)` (ASCII `\\W`)와 단어 경계를 이루지 못해 영구적으로 매칭에 실패한다.

```python
# 예: alias = "Java(Spring)"
pattern = r"\bJava\(Spring\)\b"
# "Java(Spring) 으로" → ")" 뒤 " "(공백, \\W) → \\b 없음 → 매칭 실패
```

## 원인

### 현상 A 원인

`_STACK_ALIASES` dict 순회 시 `"spring"` 키가 `"kotlin"` 키보다 먼저 처리되고,
`"Spring"` alias가 입력 내 `(Spring)` 부분에 매칭되기 때문이다.
`Kotlin(Spring)` 전용 alias 자체는 현상 B의 `\\b` 이슈로 미동작 중이므로 방어 로직 없음.

### 현상 B 원인

`re.ASCII` 모드에서 `\\b`는 `[a-zA-Z0-9_]` 경계로만 작동한다.
alias 마지막 문자가 `)`, `-` 등 `\\W`인 경우 이어지는 공백도 `\\W`이므로
`\\W`-`\\W` 경계에서 `\\b`가 성립하지 않는다.

## 도달 불가 alias 목록

`_STACK_ALIASES` 내 `)` 로 끝나는 alias (추정 목록, 구현 시 실제 파일 확인 필요):

- `"Java(Spring)"`, `"java(spring)"`
- `"Kotlin(Spring)"`, `"kotlin(spring)"`
- 기타 괄호 종료 alias

## 수정 방향

**옵션 A (권장)**: 도달 불가 alias 제거 후 단순 alias로 커버

```python
# 제거
"Java(Spring)", "java(spring)", "Kotlin(Spring)", "kotlin(spring)"
# → "Java", "java", "Kotlin", "kotlin" alias가 이미 존재하므로 기능 동일
```

**옵션 B (대안)**: `_matches_alias()`에서 alias 마지막 문자가 `\\W`인 경우 후행 `\\b` 생략

```python
suffix = r"\b" if alias[-1].isalnum() or alias[-1] == "_" else ""
pattern = r"\b" + re.escape(alias) + suffix
```

## 테스트 케이스

| 입력                                         | 기대값                                         |
| -------------------------------------------- | ---------------------------------------------- |
| `normalize_stack("Kotlin(Spring)으로 개발")` | `"kotlin"`                                     |
| `normalize_stack("Java(Spring) 프로젝트")`   | `"spring"` (Java alias 또는 Spring alias 매칭) |
| `normalize_stack("Kotlin으로 테스트 작성")`  | `"kotlin"` (회귀 없음)                         |
| `normalize_stack("Java에서 트랜잭션 관리")`  | `"spring"` (회귀 없음)                         |

## 완료 기준

- [x] 도달 불가 alias(`)` 종료) 식별 및 제거 또는 처리 전략 결정
- [x] `normalize_stack("Kotlin(Spring)으로 개발")` → `"kotlin"` 반환
- [x] 기존 테스트 케이스 회귀 없음 (P2-BUG-05 테스트 파일로 검증)
