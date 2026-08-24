---
phase: 04-mock-api-server
reviewed: 2026-08-24T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - prototype/main.py
  - prototype/__init__.py
  - prototype/mocks/__init__.py
  - prototype/mocks/schemas.py
  - prototype/mocks/data.py
  - prototype/mocks/citos_ppt.py
  - prototype/mocks/citos_tuas.py
  - prototype/mocks/optetruck.py
  - prototype/mocks/feeder.py
  - prototype/mocks/portnet.py
  - prototype/mocks/webhook.py
  - prototype/mocks/edge_cases.py
  - requirements.txt
  - tests/__init__.py
  - tests/test_mock_apis.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 04: Code Review Report

**Reviewed:** 2026-08-24T00:00:00Z
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

Reviewed 15 files comprising the PSA Mock API Server prototype: FastAPI application wiring (main.py), Pydantic schemas (schemas.py), mock data generation (data.py), 6 endpoint routers (citos_ppt, citos_tuas, optetruck, feeder, portnet, webhook), edge case simulation library (edge_cases.py), requirements.txt, and integration tests.

Overall the codebase is clean and well-structured for a prototype. All routers are correctly wired to main.py, schemas are comprehensive, and test coverage hits all major endpoints. No critical security issues — this is a mock API serving static data behind CORS `*` which is acceptable for a prototype.

Key findings: 1 returned response missing a schema-defined field, 1 edge case module that's dead code from the server's perspective, several query parameters accepted but silently ignored, and an unused `pyyaml` dependency.

## Warnings

### WR-01: Webhook endpoint returns incomplete response — missing `message` field

**File:** `prototype/mocks/webhook.py:51`
**Issue:** The `receive_webhook` endpoint returns `{"status": "accepted", "run_id": run_id}` but the `WebhookResponse` schema (schemas.py:178-181) defines a `message` field with a default value: `"ITT coordination request received. Agent triggered."`. The endpoint does not return the `WebhookResponse` model — it returns a raw dict missing the `message` key. Consumers expecting the full schema will get an incomplete response. Additionally, the function doesn't use the `WebhookResponse` Pydantic model at all, so FastAPI won't auto-serialize it.
**Fix:**
```python
# In webhook.py, import and use the schema:
from prototype.mocks.schemas import ITTCoordinationEvent, WebhookResponse

# Change return to:
return WebhookResponse(status="accepted", run_id=run_id)
```

### WR-02: OptETruck, Feeder, and PORTNET accept query parameters that are silently ignored

**File:** `prototype/mocks/optetruck.py:12-13`, `prototype/mocks/feeder.py:12`, `prototype/mocks/portnet.py:12`
**Issue:** Several endpoints accept query parameters but never pass them to the data functions:
- `optetruck.py`: `time_window_start` and `time_window_end` are accepted but `get_truck_data(terminal)` is called without them
- `feeder.py`: `current_time` is accepted but `get_feeder_data(feeder_id)` ignores it
- `portnet.py`: `current_time` is accepted but only used for `last_sync` annotation, not data computation

This creates a misleading API contract — callers may pass time window parameters expecting behavior changes that never occur. For a mock API this is low-risk, but it can confuse downstream consumers.
**Fix:** Either pass these parameters through to the data functions (even if unused), or remove them from the endpoint signatures and document that the mock returns static data regardless of input.

### WR-03: Webhook run store grows unbounded — no eviction

**File:** `prototype/mocks/webhook.py:10`
**Issue:** The `runs: dict[str, dict] = {}` is an in-memory dict that accumulates entries on every webhook call but never evicts them. In a long-running demo or stress test, this will grow without bound. For a prototype this is acceptable for short demos, but it's a latent bug.
**Fix:** Add a simple eviction strategy:
```python
from collections import OrderedDict

MAX_RUNS = 100
runs: OrderedDict[str, dict] = OrderedDict()

# In receive_webhook, after inserting:
if len(runs) > MAX_RUNS:
    runs.popitem(last=False)  # evict oldest
```

### WR-04: `edge_cases.py` is dead code — not imported or exposed by any endpoint

**File:** `prototype/mocks/edge_cases.py`
**Issue:** The `edge_cases.py` module defines `simulate_feeder_conflict` and `simulate_stale_data` functions plus an `EDGE_CASES` registry, but none of these are imported by `main.py` or any router. They're only used in tests. This means edge case simulation cannot be triggered via the API — a caller would need to import the module directly. The module's docstring says "per Master Charter §7" suggesting it should be accessible.
**Fix:** Either expose edge cases via an endpoint (e.g., `GET /api/edge-cases` listing available cases, or a query param `?edge_case=ec_1` on relevant endpoints), or move the registry into the test file and document that these are test-only utilities.

### WR-05: ITTSplitOption schema missing `risk` field used in alternatives

**File:** `prototype/mocks/schemas.py:107-116`, `prototype/mocks/data.py:277,288`
**Issue:** The `ITTSplitOption` Pydantic model defines fields for `road_containers`, `road_breakdown`, etc., but the `alternatives` list in `data.py` (lines 277, 288) includes an extra `"risk"` key that is not declared in the schema. Pydantic v2 allows extra fields by default, so this doesn't error — but it means the `risk` field is silently available as an untyped dict attribute rather than a validated field. If a consumer iterates over `model_fields` or serializes with `model_dump()`, the behavior depends on `model_config`.
**Fix:** Add the `risk` field to the schema:
```python
class ITTSplitOption(BaseModel):
    # ... existing fields ...
    risk: Optional[str] = Field(None, example="road_congestion_delay_near_pandan")
```

## Info

### IN-01: Webhook schema validation is redundant with endpoint validation

**File:** `prototype/mocks/webhook.py:20-24`, `prototype/mocks/schemas.py:169`
**Issue:** The `ITTCoordinationEvent` schema declares `container_count: int = Field(..., ge=50)`, meaning FastAPI returns 422 for values < 50 before the endpoint's manual check at line 20-24 ever executes. The manual `HTTPException(400)` is dead code for the `container_count < 50` case (though the `containers_ready > container_count` check at line 26 is still reachable). This is harmless but confusing.
**Fix:** Either remove the redundant `container_count < 50` check (keep only the `containers_ready` check), or remove `ge=50` from the schema and rely on the endpoint check.

### IN-02: `pyyaml` dependency in requirements.txt appears unused

**File:** `requirements.txt:4`
**Issue:** `pyyaml>=6.0` is listed as a dependency but no file in the prototype imports `yaml`. This is a dead dependency.
**Fix:** Remove `pyyaml>=6.0` from requirements.txt unless a future phase plans to use YAML parsing.

### IN-03: `data.py` uses `random.Random(42)` for reproducibility — good for tests, but DG container assignment is non-deterministic in edge cases

**File:** `prototype/mocks/data.py:56,70-73,90-94`
**Issue:** The container generation uses a seeded RNG (`random.Random(42)`) which makes output deterministic. However, the DG container assignment at lines 70-73 uses probabilistic logic (`rng.random() < 0.05`) that may or may not assign exactly 3 DG containers in the first pass, requiring the while loop at lines 90-94 to top up. This is fine because the seed makes it deterministic, but it's worth noting that changing the seed would change DG count distribution. The while loop is correct and will terminate (it only runs if dg_count < 3, and there are 120 containers).
**Fix:** No action needed — the seeded RNG ensures determinism. This is informational only.

### IN-04: Test for webhook rejection may be ambiguous

**File:** `tests/test_mock_apis.py:131`
**Issue:** The test `test_webhook_rejects_low_container_count` asserts `response.status_code in (400, 422)`. The comment says "Pydantic ge=50 validation returns 422 before endpoint runs" — this is correct: the `ITTCoordinationEvent` schema has `container_count: int = Field(..., ge=50)`, so a value of 30 triggers a 422 from FastAPI/Pydantic before the endpoint's manual check at line 20-24 even runs. The assertion allows both codes, which is correct but makes the test less precise.
**Fix:** Clarify which code is expected: `assert response.status_code == 422` since Pydantic validates before the endpoint runs. The manual check at webhook.py:20-24 is unreachable for values < 50 due to schema validation.

### IN-05: `portnet.py` mutates dict returned by `get_feeder_data` — correct but fragile

**File:** `prototype/mocks/portnet.py:16-17`
**Issue:** The `get_feeder_status` endpoint calls `get_feeder_data(feeder_id)` which returns a new dict each call (no shared state), then adds `portnet_source` and `last_sync` keys to it. This is safe because `get_feeder_data` creates a fresh dict each time. However, if `get_feeder_data` were ever changed to return a cached/shared dict, this mutation would be a bug. For a prototype this is fine.
**Fix:** No action needed for prototype. For production code, consider `data = get_feeder_data(feeder_id) | {"portnet_source": "community_sync", "last_sync": current_time}` to avoid in-place mutation.

---

_Reviewed: 2026-08-24T00:00:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
