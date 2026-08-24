---
phase: pre-approval-road-itt
fixed: 2026-08-24
fix_pass: 1
scope: critical + warning
iterations: 1
status: clean
---

# Road ITT — Code Review Fix Summary

**Phase:** pre-approval-road-itt
**Date:** 2026-08-24
**Scope:** Critical + Warning (5 findings fixed)
**Iterations:** 1

## Fixes Applied

| # | ID | Severity | Fix |
|---|-----|----------|-----|
| 1 | WR-01 | Warning | Updated `worst_segment` severity dict to match actual status values (`"moderate_traffic"`, `"moderate_traffic_near_pandan"`) — AYE congestion penalty now applies correctly |
| 2 | WR-02 | Warning | Added `QC_LOADING_BUFFER_MINUTES = 30` constant and subtracted from `latest_arrival_at_tuas` — downstream consumers now get realistic arrival deadline |
| 3 | WR-03 | Warning | Added `import math` and replaced `int()` with `math.ceil()` for transit time adjustments — no longer underestimates by truncation |
| 4 | WR-04 | Warning | Added `POST_PEAK_BUFFER_MINUTES = 20` and post-peak check in `_resolve_transit_time` — departures within 20 min after peak now correctly use peak transit time |
| 5 | WR-05 | Warning | Changed `required_trips` from `capacity.baseline_trips_all_120` (hardcoded 80) to `capacity.total_trips` — esc_5 escalation now uses actual container mix |

## Constants Added

```python
CONGESTION_AYE_MULTIPLIER = 1.3    # AYE congestion adjustment
CONGESTION_WCH_MULTIPLIER = 1.2    # West Coast Highway adjustment
QC_LOADING_BUFFER_MINUTES = 30     # Latest arrival buffer for QC loading
POST_PEAK_BUFFER_MINUTES = 20      # Lingering congestion after peak window
```

## Verification

- Normal case: transit=54min (off-peak, no congestion)
- Peak case: transit=114min (95 base + AYE 30% congestion, ceiled)
- Post-peak case (09:40): transit=95min (peak transit, lingering congestion)
- QC buffer: `latest_arrival_at_tuas` is 30 min before `time_window_end`
- esc_5: now triggers correctly based on actual `total_trips` (48 threshold for 80 trips)

## Remaining Info (7)

IN-01 through IN-07 remain unfixed (out of scope — no `--all` flag).

## Status

**REVIEW.md updated:** `status: clean`, `warning: 0`, `total: 7`
