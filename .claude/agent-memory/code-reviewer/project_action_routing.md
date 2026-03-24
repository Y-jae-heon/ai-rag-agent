---
name: action_routing 레이어 설계 패턴
description: HandlerContext/BaseHandler 구조적 특징, Any 타입 미구체화 현황, 디버그 print 잔존 패턴, answer_type 이중 관리 구조 — 이 레이어 리뷰 시 반복 확인 필요
type: project
---

## HandlerContext 타입 현황

`HandlerContext` (base_handler.py)의 `resolution`과 `understanding` 필드가 모두 `Any` 타입으로 선언되어 있다. `arbitrary_types_allowed = True`가 설정되어 있으므로 `TYPE_CHECKING` 블록을 통한 구체 타입 선언이 가능하다.

**Why:** 순환 임포트 방지를 위해 임시로 `Any`를 사용한 것으로 보인다. 타입 구체화는 별도 티켓(TK-02)으로 예정되어 있다고 docstring에 명시됨.

**How to apply:** action_routing 레이어 파일을 리뷰할 때 `Any` 타입 필드를 발견하면 `TYPE_CHECKING` 패턴으로 구체화를 권장하되 Critical/Major로 올리지 말고 Major 수준으로 유지한다.

## 디버그 print 잔존 패턴

`compare_handler.py`, `discover_handler.py`, `summarize_handler.py`, `extract_handler.py` 모두 ChromaDB 호출 전후에 `print(f"[ChromaDB] ...")` 패턴이 남아 있다. `logger`가 이미 각 파일에 선언되어 있으므로 `logger.debug`로 교체해야 한다.

**Why:** 개발 디버깅 단계에서 추가된 임시 print 문으로, 아직 정리되지 않은 상태.

**How to apply:** 이 레이어의 어떤 파일을 리뷰해도 print 문은 Major 수준으로 지적한다.

## _get_sections 중복

`compare_handler.py`와 `summarize_handler.py`의 `_get_sections` 구현이 거의 동일하다. 공통 유틸리티로 추출하지 않았다.

**Why:** P1 단계에서 핸들러를 각자 독립적으로 구현한 결과로 보임.

**How to apply:** 동일 로직을 발견하면 Minor 수준으로 공통화를 권장한다.

## answer_type 이중 관리 구조 (알려진 구조적 결함)

`valid_answer_types` (query.py의 set)과 `QueryResponse.answer_type` (models.py의 Literal)이 중복 선언되어 있다. 두 곳을 항상 동시에 수정해야 하며, 한쪽만 수정하면 silent 변환 버그가 재발한다.

- P3-BUG-04에서 `"not_found"` 누락을 두 곳 모두 수정하여 해결했으나, `"compare"` answer_type도 동일하게 누락 상태임이 확인되었다 (2026-03-24).
- `HandlerResult.answer_type`이 `str`로 선언되어 handler 레이어에서 임의 값 반환을 타입 시스템이 막지 못한다. `query.py`의 런타임 집합 비교에만 의존하는 구조.

**Why:** 초기 구현 시 handler 레이어와 API 레이어의 answer_type 범위를 별도 관리한 결과.

**How to apply:** answer_type 관련 수정 리뷰 시 세 곳(query.py set, models.py Literal, base_handler.py HandlerResult)이 모두 동기화되어 있는지 확인한다. `"compare"` 누락도 함께 지적한다.
