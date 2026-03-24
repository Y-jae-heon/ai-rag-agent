---
name: action_routing 반복 패턴 및 위험 영역
description: action_routing 모듈의 고위험 코드 영역, 반복 결함 패턴, 테스트 커버리지 공백
type: project
---

router.py의 route_and_execute()는 HandlerContext를 직접 생성하는 유일한 entry point이지만, 이 함수에 대한 직접 테스트가 없다. handler 단위 테스트는 make_context() 헬퍼로 HandlerContext를 직접 생성하므로 router를 경유하지 않는다.

**Why:** P2-BUG-03에서 understanding=understanding 줄이 주석 처리되는 버그가 발생했는데, 이를 잡는 테스트가 없어 코드 리뷰에서야 발견되었다. 동일한 패턴의 버그(context 필드 누락/주석)가 재발해도 현재 테스트 스위트는 탐지 불가.

**How to apply:** action_routing 관련 QA 시 반드시 route_and_execute() 직접 호출 테스트 존재 여부 확인. 없으면 High 이슈로 분류.

## 반복 패턴

- 모든 handler (_get_sections, _get_section_headings, _mmr_search)에 debug print()가 잔존. ChromaDB 호출 전후 print는 기존 부채이나 매 요청에 실행됨.
- compare_handler.py의 handle() 본문에 resolution_a, resolution_b를 출력하는 print가 2건 추가됨 (P2-BUG-03 수정 시 삽입 추정). 다른 handler에 없는 패턴.
- HandlerContext.understanding 타입이 Any + default=None으로 선언되어 있어, 새 handler가 understanding을 사용할 때 타입 안전성 없음.

## valid_answer_types silent 변환 패턴 (P3-BUG-04 QA에서 발견)

- `query.py`의 `valid_answer_types` set과 `models.py`의 `Literal`은 이중 관리 구조. 값을 추가할 때 한쪽 누락 시 silent clarify 변환 재발.
- 현재(2026-03-24 기준) `SummarizeHandler`가 `"summarize"`를 반환하나 `valid_answer_types`에는 `"summary"`만 있어 요약 응답이 항상 `"clarify"`로 변환되는 잔존 버그 존재.
- `_build_response()` 함수에 직접 단위 테스트가 없어 이 패턴의 회귀가 자동 감지되지 않음.
- QA 시 handler 파일 전수 조사(`answer_type=` 값 추출)와 `valid_answer_types` 집합 비교를 반드시 수행할 것.
