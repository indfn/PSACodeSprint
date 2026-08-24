# Sea ITT Code Review Report

**Reviewed:** 2026-08-24T00:00:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Reviewed the Sea ITT tool (`check_sea_itt_capacity`) — a PORTNET mock API that queries feeder vessel availability, berth status, departure windows, and downstream port tidal constraints. Found **2 critical issues** (shallow copy mutation corrupting shared mock data, timezone-naive/aware datetime comparison crash), **6 warnings** (unused parameters, antipattern imports, response model mismatches, incomplete availability check, missing escalation model), and **6 info items** (unused imports, example inconsistencies, hardcoded values, CORS config, constraint enforcement). The shallow copy bug is particularly dangerous because it silently corrupts `FEEDER_FLEET` state across calls, causing cascading incorrect results for downstream Tool 4.

---

## Critical Issues

### CR-01: Shallow copy in `simulate_berth_conflict` mutates shared `FEEDER_FLEET` data

- **File:** `mock_data.py:217`
- **Description:** `simulate_berth_conflict` calls `base.copy()` (shallow copy), then mutates nested dicts (`departure_window`, `downstream_constraints`) at lines 218-231. Since `FEEDER_FLEET` contains mutable nested dicts, the shallow copy shares references to the same `departure_window` dict. Mutating `conflict["departure_window"]` or reading from `FEEDER_FLEET[feeder_id]["departure_window"]` after the first conflict injection will return corrupted data.
- **Impact:** After `simulate_berth_conflict("FEEDER ATLANTIC-03")` is called, subsequent calls to `get_feeder_status("FEEDER ATLANTIC-03")` return the *delayed* departure window instead of the original. This corrupts all downstream Tool 4 calculations. In a demo with repeated calls, the state drifts silently.
- **Suggested fix:** Use `copy.deepcopy()` or manually reconstruct nested dicts:
  ```python
  import copy
  base = copy.deepcopy(get_feeder_status(feeder_id))
  ```
  Or manually reconstruct the departure window dict:
  ```python
  conflict["departure_window"] = {
      "earliest": delayed_earliest.isoformat(),
      "latest": delayed_latest.isoformat(),
      "requested": base["departure_window"]["requested"],
  }
  ```

---

### CR-02: Timezone-naive `datetime.now()` compared with timezone-aware ISO strings

- **File:** `mock_data.py:169`
- **Description:** `get_available_feeders()` calls `datetime.now()` (returns timezone-naive) and compares it against `datetime.fromisoformat(feeder["departure_window"]["latest"])` which parses timezone-aware ISO strings (e.g., `"2026-08-19T16:00:00+08:00"`). Python raises `TypeError: can't compare offset-naive and offset-aware datetimes`.
- **Impact:** Any call to `GET /portnet/feeders` or internal usage of `get_available_feeders()` without an explicit `current_time` argument will crash with a TypeError. The endpoint becomes non-functional.
- **Suggested fix:** Use timezone-aware datetime as default:
  ```python
  from datetime import datetime, timezone
  now = current_time or datetime.now(timezone.utc)
  ```
  Or, since the mock data uses SGT (+08:00), parse with a fixed offset:
  ```python
  from datetime import timezone, timedelta
  SGT = timezone(timedelta(hours=8))
  now = current_time or datetime.now(SGT)
  ```

---

## Warnings

### WR-01: `portnet_endpoint` parameter is required but never used

- **File:** `sea_itt_tools.py:288`, `sea_itt_tools.py:311`
- **Description:** `check_sea_itt_capacity()` accepts `portnet_endpoint: str` as its first parameter and the schema lists it as a property, but the function body never references it. The tool always reads from the local `FEEDER_FLEET` mock dict regardless of what endpoint is passed.
- **Impact:** LLM agents may spend tokens specifying endpoint URLs that are silently ignored. Misleads integrators into thinking the endpoint is functional.
- **Suggested fix:** Either remove the parameter (and update the schema), or add a comment/TODO indicating it's a placeholder for production routing:
  ```python
  # TODO: In production, use portnet_endpoint to route to live PORTNET API.
  # Currently unused — all data comes from local FEEDER_FLEET mock.
  ```

---

### WR-02: `__import__("datetime")` antipattern in router conflict endpoint

- **File:** `router.py:140`, `router.py:143`
- **Description:** Uses `__import__("datetime").timedelta(...)` instead of importing `timedelta` at the top of the module. This is an antipattern that obscures dependencies, hinders static analysis, and is harder to read.
- **Impact:** Minor code quality issue, but makes the import dependency invisible to linters and IDEs. Could confuse future maintainers.
- **Suggested fix:** Import `timedelta` at the top of the file:
  ```python
  from datetime import datetime, timedelta
  ```
  Then use `timedelta(...)` directly at lines 140 and 143.

---

### WR-03: `is_available_for_loading` property is too simplistic

- **File:** `sea_itt_tools.py:135-136`
- **Description:** `is_available_for_loading` only checks `is_berthed` and `available_capacity_teu > 0`. It does not verify that the departure window hasn't already passed, or that the tidal feasibility is not "missed". A feeder that has departed or whose departure window has closed still reports as "available for loading".
- **Impact:** Tool 4 (compute_itt_split) may incorrectly allocate containers to a feeder that can no longer accept them, leading to a bad sea/road split decision.
- **Suggested fix:** Add departure window check:
  ```python
  @property
  def is_available_for_loading(self) -> bool:
      if not self.is_berthed or self.available_capacity_teu <= 0:
          return False
      try:
          dep_latest = datetime.fromisoformat(self.departure_window["latest"])
          return dep_latest > datetime.now(timezone.utc)
      except (ValueError, KeyError):
          return False
  ```

---

### WR-04: `FeederStatusResponse` model doesn't match router output

- **File:** `router.py:61-69`, `models.py:156-172`
- **Description:** The router at `get_feeder_status_endpoint` returns a raw dict with fields like `departure_status: "on_schedule"` and `delay_minutes: 0`. The imported `FeederStatusResponse` Pydantic model is never used as the return type. Additionally, the model defines `data_timestamp: str` (required) but the router's dict includes it — however the mismatch between model and actual response means OpenAPI docs will be inaccurate.
- **Impact:** FastAPI OpenAPI schema won't reflect the actual response shape. API consumers relying on generated clients will get incorrect type information.
- **Suggested fix:** Use the Pydantic model as the return type:
  ```python
  @router.get("/feeder/{feeder_id}", response_model=FeederStatusResponse)
  async def get_feeder_status_endpoint(feeder_id: str):
  ```

---

### WR-05: `FeederHoldResponse` model imported but never used

- **File:** `router.py:19`, `router.py:72-83`
- **Description:** `FeederHoldResponse` is imported from `models.py` but `request_feeder_hold` returns the raw dict from `get_feeder_hold_cost()` instead. The response model is dead code in the router context.
- **Impact:** OpenAPI docs won't document the hold response schema accurately. API consumers can't generate typed clients.
- **Suggested fix:** Either use `response_model=FeederHoldResponse` on the endpoint, or remove the unused import.

---

### WR-06: `inject_berth_conflict` override path reads from potentially mutated `FEEDER_FLEET`

- **File:** `router.py:137-138`
- **Description:** When `delay_minutes != 120`, the conflict endpoint reads `FEEDER_FLEET[feeder_id]["departure_window"]["earliest"]` to recalculate. If CR-01 (shallow copy) has already corrupted `FEEDER_FLEET`, this reads the wrong original time, compounding the error.
- **Impact:** Double-corruption: the conflict endpoint calculates delay from an already-delayed departure time, producing an incorrect new window.
- **Suggested fix:** After fixing CR-01 with deepcopy, also store original departure windows separately or use a snapshot approach. Alternatively, accept the original window as a parameter.

---

## Info

### IN-01: Unused import `timedelta` in `router.py`

- **File:** `router.py:13`
- **Description:** `timedelta` is imported but never used directly (the `__import__` workaround at line 140 bypasses it).
- **Impact:** Dead import; linters will flag it.
- **Suggested fix:** Either use `timedelta` directly (fixes WR-02) or remove the import.

---

### IN-02: `DownstreamConstraints.must_depart_by` field is computed but never used in feasibility check

- **File:** `models.py:78-81`, `sea_itt_tools.py:190-254`
- **Description:** `DownstreamConstraints` has a `must_depart_by` field (e.g., `"2026-08-20T04:00:00+08:00"`), but `_check_tidal_feasibility()` computes `latest_safe_departure` independently from `tidal_window - transit - buffer`. The `must_depart_by` value is never consulted during the tidal feasibility calculation.
- **Impact:** If `must_depart_by` is set to a different value than the computed `latest_safe_departure` (due to port-specific scheduling rules), the tool ignores it and may give incorrect feasibility results.
- **Suggested fix:** Either use `must_depart_by` as the authoritative deadline (if it comes from the port authority), or document that it's informational only and the tool computes its own deadline.

---

### IN-04: `data_age_minutes` is hardcoded to `0.5`

- **File:** `sea_itt_tools.py:402`
- **Description:** `result["data_age_minutes"] = 0.5` is hardcoded. In production, this should reflect actual data staleness from the PORTNET API.
- **Impact:** The staleness check (`esc_4` trigger mentioned in models.py docstring) will never fire because data always appears fresh.
- **Suggested fix:** Compute from `data_timestamp` vs `current_time`, or add a TODO comment.

---

### IN-05: Inconsistent example in `DownstreamConstraints.must_depart_by`

- **File:** `models.py:79`
- **Description:** The example for `must_depart_by` is `"2026-08-19T05:00:00+08:00"` (Aug 19 05:00), but the `tidal_window` example is `"2026-08-19T23:00:00+08:00"` (Aug 19 23:00). With 18 hrs transit + 1 hr buffer, the actual must-depart-by should be `23:00 - 19h = 04:00` on Aug 19 — the example says 05:00, which is 1 hour too late. This is a documentation inconsistency.
- **Impact:** Misleading for API consumers reading the schema docs.
- **Suggested fix:** Update example to `"2026-08-19T04:00:00+08:00"` to match the math.

---

### IN-06: CORS wildcard configuration (`allow_origins=["*"]`)

- **File:** `app.py:28`
- **Description:** CORS middleware allows all origins, methods, and headers. Acceptable for a mock/demo API but should not ship to production.
- **Impact:** In production, this would allow any website to make authenticated cross-origin requests.
- **Suggested fix:** For demo purposes this is fine, but add a comment:
  ```python
  # NOTE: Wildcard CORS for demo/mock only. Restrict in production.
  ```

---

### IN-07: Pydantic `FeederHoldRequest.hold_hours` constraint `le=6` not enforced at tool level

- **File:** `models.py:39`, `mock_data.py:287-334`
- **Description:** `FeederHoldRequest` enforces `hold_hours: float = Field(..., gt=0, le=6)` via Pydantic validation, but `get_feeder_hold_cost()` in `mock_data.py` accepts any float with no upper bound check. If called directly (not via the router), there's no validation.
- **Impact:** Direct function calls bypass Pydantic validation, allowing unbounded hold durations that could produce unrealistic cost calculations.
- **Suggested fix:** Add a guard in `get_feeder_hold_cost()`:
  ```python
  if hold_hours <= 0 or hold_hours > 6:
      return {"status": "error", "error": f"hold_hours must be between 0 and 6, got {hold_hours}"}
  ```

---

_Reviewed: 2026-08-24T00:00:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
