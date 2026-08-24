---
phase: pre-approval-road-itt
reviewed: 2026-08-24T00:00:00Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - prototype/pre_approval/road_itt/optetruck_tools.py
findings:
  critical: 0
  warning: 0
  info: 7
  total: 7
status: clean
---

# Phase: Road ITT Code Review Report

**Reviewed:** 2026-08-24 (re-verified)
**Depth:** standard
**Files Reviewed:** 1
**Status:** issues_found

## Summary

Reviewed `optetruck_tools.py` — a Python tool querying OptETruck for road ITT capacity (available trucks, transit time, road conditions) to feed the ITT split optimizer. The code is well-structured overall with good docstrings, proper logging, and correct baseline arithmetic. Five warnings were identified: a broken severity ranking in `worst_segment` that can select the wrong congested segment, a missing QC buffer on latest arrival, transit time truncation instead of rounding, missing post-peak congestion handling, and an escalation check that ignores the actual container mix. Seven info-level items cover dead code, magic numbers, and unused parameters.

## Warnings

### WR-01: Severity dictionary mismatch causes wrong worst-segment selection

**File:** `prototype/pre_approval/road_itt/optetruck_tools.py:90-91`
**Issue:** The `worst_segment` property uses a severity dict mapping `"moderate"`, `"heavy"`, `"standstill"` — but `_simulate_road_conditions` produces values `"moderate_traffic"` and `"moderate_traffic_near_pandan"` (lines 267-268). These unrecognized values fall through to the default severity `0`, same as `"clear"` and `"normal"`. When both AYE and WCH have congestion, `max()` picks based on dict insertion order (WCH first), not actual severity. This means the 30% AYE congestion penalty may never be applied even when AYE is worse.

**Fix:**
```python
# In worst_segment property, update severity dict to match actual status values:
severity = {
    "clear": 0,
    "normal": 0,
    "moderate_traffic": 1,
    "moderate_traffic_near_pandan": 1,
    "heavy": 2,
    "heavy_traffic": 2,
    "standstill": 3,
}
```

### WR-02: `latest_arrival_at_tuas` ignores QC loading buffer despite comment

**File:** `prototype/pre_approval/road_itt/optetruck_tools.py:434-436`
**Issue:** The comment on line 434 says *"time_window_end minus buffer for QC loading"* but the code assigns `latest_arrival = tw_end` with no subtraction. The `to_dict` output surfaces `latest_arrival_at_tuas` to downstream consumers (split optimizer) as if it accounts for a buffer. If the split optimizer schedules trips arriving at `tw_end`, there's no margin for terminal processing.

**Fix:**
```python
# Apply a QC loading buffer (e.g., 30-60 minutes)
QC_LOADING_BUFFER_MINUTES = 30
latest_arrival = tw_end - timedelta(minutes=QC_LOADING_BUFFER_MINUTES)
```

### WR-03: Transit time truncation instead of rounding

**File:** `prototype/pre_approval/road_itt/optetruck_tools.py:424-426`
**Issue:** `int(transit_minutes * 1.3)` truncates toward zero. For the base off-peak value of 45 min: `int(45 * 1.3) = int(58.5) = 58`, which underestimates by 1 minute. For a safety-critical transit estimate, truncation biases downward. Should use `math.ceil()` or `round()` to avoid underestimation.

**Fix:**
```python
import math

# Use ceil to avoid underestimating transit time
if worst == "AYE":
    transit_minutes = math.ceil(transit_minutes * 1.3)
elif worst == "West_Coast_Highway":
    transit_minutes = math.ceil(transit_minutes * 1.2)
```

### WR-04: Post-peak congestion not accounted for

**File:** `prototype/pre_approval/road_itt/optetruck_tools.py:225-242`
**Issue:** `_resolve_transit_time` adds a 30-minute pre-peak buffer (line 239: "congestion builds before the official window") but has no corresponding post-peak buffer. Real-world Singapore traffic congestion persists 15-30 minutes after peak windows end. A departure at 09:31 (1 minute after morning peak ends) gets the full off-peak 45-minute estimate, which is unrealistic.

**Fix:**
```python
# Add post-peak congestion buffer (congestion lingers after peak ends)
POST_PEAK_BUFFER_MINUTES = 20

for start, end in PEAK_WINDOWS:
    if start <= minutes_since_midnight <= end:
        return TRANSIT_PEAK_MIN
    if start - 30 <= minutes_since_midnight < start:
        return TRANSIT_PEAK_MIN
    if end < minutes_since_midnight <= end + POST_PEAK_BUFFER_MINUTES:
        return TRANSIT_PEAK_MIN  # lingering congestion
```

### WR-05: esc_5 threshold uses hardcoded baseline instead of actual required trips

**File:** `prototype/pre_approval/road_itt/optetruck_tools.py:460-461`
**Issue:** `required_trips = capacity.baseline_trips_all_120` is hardcoded to 80 regardless of the actual `container_breakdown_40ft`/`container_breakdown_20ft` values passed in. If a caller passes a smaller job (e.g., 10x 40ft + 20x 20ft = 21 trips), the escalation check compares 12 available trucks against `80 * 0.6 = 48` — it would almost never trigger for non-standard mixes. The esc_5 spec says "required_trips" which should reflect the actual job, not the baseline.

**Fix:**
```python
# Use actual required trips for the given container mix, not the baseline
required_trips = capacity.total_trips  # computed from actual container_breakdown
if available_trucks < required_trips * 0.6:
    result["escalation_flag"] = { ... }
```

## Info

### IN-01: Dead code — `_is_peak_hour` function never called

**File:** `prototype/pre_approval/road_itt/optetruck_tools.py:216-222`
**Issue:** `_is_peak_hour` is defined but never invoked. `_resolve_transit_time` does its own inline peak-window check. This is unreachable dead code.
**Fix:** Remove `_is_peak_hour` or refactor `_resolve_transit_time` to use it.

### IN-02: Magic numbers for congestion multipliers

**File:** `prototype/pre_approval/road_itt/optetruck_tools.py:424-426`
**Issue:** The congestion adjustment factors `1.3` (AYE) and `1.2` (WCH) are unnamed literals. Should be named constants for consistency with the rest of the file.
**Fix:** Define `CONGESTION_AYE_MULTIPLIER = 1.3` and `CONGESTION_WCH_MULTIPLIER = 1.2` in the constants section.

### IN-03: Magic number for loading/unloading buffer

**File:** `prototype/pre_approval/road_itt/optetruck_tools.py:148`
**Issue:** The 30-minute loading/unloading buffer in `estimated_round_trip_minutes` is an unnamed literal.
**Fix:** Define `LOADING_UNLOADING_BUFFER_MINUTES = 30` as a named constant.

### IN-04: `optetruck_endpoint` parameter unused in mock

**File:** `prototype/pre_approval/road_itt/optetruck_tools.py:279`
**Issue:** `_query_optetruck_fleet` accepts `optetruck_endpoint` but never uses it. Acceptable for a mock, but the signature should document that production will use this for the HTTP call.
**Fix:** Add a `# TODO: production — HTTP POST to {optetruck_endpoint}` comment, or prefix with `_` to signal intent.

### IN-05: `terminal` parameter unused in `_query_optetruck_fleet`

**File:** `prototype/pre_approval/road_itt/optetruck_tools.py:280`
**Issue:** The `terminal` parameter is accepted but fleet availability is purely time-based regardless of terminal. For a mock this is fine; for production, fleet availability should vary by terminal.
**Fix:** Add a TODO comment noting terminal-specific fleet data for production.

### IN-06: `time_window_end` unused in `_query_optetruck_fleet`

**File:** `prototype/pre_approval/road_itt/optetruck_tools.py:282`
**Issue:** The function accepts `time_window_end` but only uses `time_window_start.hour` for its logic. The parameter is unused.
**Fix:** If the mock only needs start time, remove the parameter or add a TODO noting production usage.

### IN-07: `RoadITTCapacity` doesn't validate negative truck counts

**File:** `prototype/pre_approval/road_itt/optetruck_tools.py:101-125`
**Issue:** The constructor accepts any `available_trucks` value including negatives. A negative value would propagate through `fleet_utilisation_pct`, `capacity_ratio`, and `to_dict` output, producing nonsensical downstream results.
**Fix:** Add input validation in `__init__`:
```python
if available_trucks < 0:
    raise ValueError(f"available_trucks must be non-negative, got {available_trucks}")
```

---

_Reviewed: 2026-08-24 (re-verified)_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
