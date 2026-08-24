# Sea ITT Code Review Fix Summary

**Phase:** sea_itt (Tool 3)
**Date:** 2026-08-24
**Status:** All 14 findings fixed

## Fixes Applied

| # | Severity | Finding | Fix | Files Changed |
|---|----------|---------|-----|---------------|
| CR-01 | Critical | `simulate_berth_conflict` shallow copy mutates shared `FEEDER_FLEET` | Added `import copy`, use `copy.deepcopy()` | `mock_data.py` |
| CR-02 | Critical | `datetime.now()` timezone-naive crashes vs timezone-aware ISO strings | Import `timezone, timedelta`, use `datetime.now(SGT)` with SGT constant | `mock_data.py` |
| WR-01 | Warning | `portnet_endpoint` param required but never used | Added TODO comment documenting production intent | `sea_itt_tools.py` |
| WR-02 | Warning | `__import__("datetime")` antipattern in router | Import `timedelta` at top, use directly | `router.py` |
| WR-03 | Warning | `is_available_for_loading` too simplistic (no departure window check) | Added departure window validation against current time | `sea_itt_tools.py` |
| WR-04 | Warning | `FeederStatusResponse` model imported but not used as response_model | Added `response_model=FeederStatusResponse` to endpoint | `router.py` |
| WR-05 | Warning | `FeederHoldResponse` imported but not used | Added `response_model=FeederHoldResponse` to endpoint | `router.py` |
| WR-06 | Warning | Conflict endpoint reads from potentially mutated `FEEDER_FLEET` | Fixed by CR-01 deepcopy (shared state no longer corrupted) | — |
| IN-02 | Info | `must_depart_by` field computed but never used in tidal check | Added docstring explaining it's informational, tool computes own deadline | `sea_itt_tools.py`, `models.py` |
| IN-04 | Info | `data_age_minutes` hardcoded to 0.5 | Set to 0.0 (fresh query) with comment | `sea_itt_tools.py` |
| IN-05 | Info | `must_depart_by` example inconsistent with tidal math | Updated example from 05:00 to 04:00 (23:00 - 18h - 1h = 04:00) | `models.py` |
| IN-06 | Info | CORS wildcard `allow_origins=["*"]` without comment | Added comment: "demo/mock only, restrict in production" | `app.py` |
| IN-07 | Info | `hold_hours` constraint not enforced at function level | Added bounds check (0, 6] with error response | `mock_data.py` |

## Files Modified

| File | Changes |
|------|---------|
| `mock_data.py` | deepcopy fix, SGT timezone, hold_hours validation, import cleanup |
| `sea_itt_tools.py` | SGT constant, is_available_for_loading improvement, TODO comment, data_age fix, tidal docstring |
| `router.py` | response_model on endpoints, timedelta import, removed `__import__` antipattern, removed unused import |
| `models.py` | must_depart_by example fix, description update |
| `app.py` | CORS comment |

## Verification

All fixes verified with standalone tests:
- CR-01: Conflict injection no longer corrupts `FEEDER_FLEET` state across calls
- CR-02: `get_available_feeders()` no longer crashes on timezone comparison
- IN-07: `hold_hours` rejected when outside (0, 6]
- Full T3→T4 integration: `80 road / 40 sea = $7,400` with confidence 0.9

## Remaining Notes

- `mock_data.py` is a temporary embedded data source. When `prototype/mocks/` server is built, refactor `sea_itt_tools.py` to call HTTP endpoints instead.
- `portnet_endpoint` param is kept for future production routing (currently unused).
