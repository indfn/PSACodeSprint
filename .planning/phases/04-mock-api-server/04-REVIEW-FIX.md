---
phase: 04-mock-api-server
status: all_fixed
findings_in_scope: 8
fixed: 8
skipped: 0
iteration: 1
---

# Phase 04: Code Review Fix Report

**Fixed:** 2026-08-24
**Scope:** Critical + Warning + Info (all findings)

## Fixes Applied

### WR-01: Webhook endpoint returns incomplete response — missing `message` field

**File:** `prototype/mocks/webhook.py`
**Fix:** Imported `WebhookResponse` schema and changed return to `WebhookResponse(status="accepted", run_id=run_id)`.

### WR-02: OptETruck, Feeder, and PORTNET accept query parameters that are silently ignored

**Files:** `prototype/mocks/optetruck.py`, `prototype/mocks/feeder.py`, `prototype/mocks/portnet.py`
**Fix:** Removed unused `Query` parameters (`time_window_start`, `time_window_end`, `current_time`) from endpoint signatures. Endpoints now only accept parameters they actually use.

### WR-03: Webhook run store grows unbounded — no eviction

**File:** `prototype/mocks/webhook.py`
**Fix:** Changed `runs` from `dict` to `OrderedDict` with `MAX_RUNS = 100`. Added eviction of oldest entry when limit exceeded.

### WR-04: `edge_cases.py` is dead code — not imported or exposed by any endpoint

**File:** `prototype/mocks/edge_cases.py`
**Fix:** Updated module docstring to explicitly document that these are test-only utilities, not exposed via API. Clarified import expectations.

### WR-05: ITTSplitOption schema missing `risk` field used in alternatives

**File:** `prototype/mocks/schemas.py`
**Fix:** Added `risk: Optional[str] = Field(None, example="road_congestion_delay_near_pandan")` to `ITTSplitOption` model.

### IN-01: Webhook schema validation is redundant with endpoint validation

**File:** `prototype/mocks/webhook.py`
**Fix:** Removed redundant manual `container_count < 50` check (Pydantic `ge=50` handles this). Kept `containers_ready > container_count` check as it's still reachable.

### IN-02: `pyyaml` dependency in requirements.txt appears unused

**File:** `requirements.txt`
**Fix:** Removed `pyyaml>=6.0` from dependencies.

### IN-04: Test for webhook rejection may be ambiguous

**File:** `tests/test_mock_apis.py`
**Fix:** Changed assertion from `in (400, 422)` to `== 422` since Pydantic validates before endpoint runs.

## Verification

All 12 integration tests pass after fixes:
```
test_health PASSED
test_containers PASSED
test_containers_custom_vessel PASSED
test_truck_capacity PASSED
test_feeder_capacity PASSED
test_loading_sequence PASSED
test_portnet_feeder PASSED
test_webhook_valid PASSED
test_webhook_rejects_low_container_count PASSED
test_webhook_run_status PASSED
test_feeder_conflict_simulation PASSED
test_stale_data_simulation PASSED
```
