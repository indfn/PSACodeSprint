# Phase 5 Review Fix Report

**Date:** 2026-08-27
**Review:** 05-REVIEW.md (15 issues: 1 Critical, 4 High, 6 Medium, 4 Low)
**Fix commits:** 10 fix commits + 1 test update on top of `1889143`

## Summary Table

| Issue | Severity | File:Line | Fix | Status |
|-------|----------|-----------|-----|--------|
| C1 — YAML tool names diverge from charter | Critical | `app/configs/pb-12-itt.yaml:28-53` | Renamed `query_container_readiness`→`get_itt_candidates`, `compute_optimal_split`→`compute_itt_split`; added `dispatch_road_itt`, `request_feeder_hold`, `notify_parties` with `tool_6/7/8`; kept `receive_webhook` with `type: event_trigger`; filtered trigger in `app/main.py:182-196,209-220` | ✅ Fixed |
| H1 — post_approval guard no-op | High | `app/tools/registry.py:120-121`, `app/tools/base.py:69,123` | Registry now returns `ToolResult(error=hitl_required, confidence=0.0)`; removed dead `_hitl_approved` re-insertion in BaseTool; added negative test `test_post_approval_guard_rejects_without_hitl` | ✅ Fixed |
| H2 — weight_bounds guardrail absent | High | `app/tools/optimiser.py:358-381` | Added `weight_bounds_valid` to `guardrails_checked` scanning `candidates.containers[].weight_kg` for None/≤0, downgrades confidence to 0.6, sets `metadata.guardrail_failed=weight_bounds` | ✅ Fixed |
| H3 — silent swallow of import errors | High | `app/tools/registry.py:60-78`, `app/tools/optimiser.py:17-24,115-120` | Added `warnings.warn` with exc for factory fallback, narrows `_load_cost_params` to `FileNotFoundError/ImportError` + generic warn, same for `compute_itt_split_default` | ✅ Fixed |
| H4 — receive_webhook counted as tool | High | `app/configs/pb-12-itt.yaml:50-53`, `app/main.py:182-196` | Merged with C1: `type: event_trigger` and `type != event_trigger` filter in both switch and active-problem endpoints | ✅ Fixed |
| M1 — notify parties warn-only | Medium | `app/tools/notify.py:84-126` | Downgrade confidence to 0.7 when unknown parties, set `metadata.unknown_parties`, keep warning | ✅ Fixed |
| M2 — _load_cost_params silent catch | Medium | `app/tools/optimiser.py:17-24` | Narrowed to specific exceptions, added warning metadata, preserves `cost_params_source` | ✅ Fixed (with H3) |
| M3 — registry vs YAML test gap | Medium | `app/tests/test_registry.py:109-114` | Added `test_yaml_charter_names_match_toolsets` asserting filtered YAML == TOOLSETS["pb-12-itt"] and 8 tools | ✅ Fixed |
| M4 — SSE sticky cache | Medium | `app/tools/notify.py:40-64`, `app/mocks/routers/notify.py:18-37` | Removed permanent `_broadcaster_checked`, retry import each call, cache only success, warn on publish failure | ✅ Fixed |
| M5 — deep-copy aliasing risk | Medium | `app/tools/edge_cases.py:1-10` | Added docstring noting demo-only not thread-safe, needs lock/per-run copy, autouse fixture isolation | ✅ Fixed |
| M6 — fallback live data | Medium | `app/tools/fallbacks.py:21-51` | Cache `copy.deepcopy` snapshot at module init (`_LAST_TRUCK_SNAPSHOT`, `_LAST_FEEDER_SNAPSHOT`), return deepcopy with `fallback_used` flag | ✅ Fixed |
| L1 — broad except + silent pass SSE | Low | `app/tools/notify.py:105-116`, `app/mocks/routers/notify.py:38-39` | Changed `except Exception: pass` to `except Exception as e: warnings.warn(str(e))` | ✅ Fixed |
| L2 — type looseness string→number | Low | `app/tools/base.py:69-93`, `app/tools/request_feeder_hold.py:32` | Added lightweight type coercion in BaseTool.call for `integer`/`number` schemas, returns `type_mismatch` error if not convertible | ✅ Fixed |
| L3 — dead hitl round-trip | Low | `app/tools/base.py:69,123` | Removed re-insertion and post-pop of `_hitl_approved`; registry is authoritative | ✅ Fixed |
| L4 — missing __init__ re-export | Low | `app/tools/__init__.py` | Added `from .registry import registry, TOOLSETS, FALLBACKS` | ✅ Fixed |

## Verification

```
python3 -m pytest app/tests/ -v          # 127 passed, 3 skipped, 24 warnings
python3 -m pytest app/tests/test_registry.py app/tests/test_roi.py app/tests/test_tools.py app/tests/test_robustness.py -v  # 70 passed, 3 skipped
Manual:
  registry.register_for_problem("pb-12-itt") -> 8 tools (charter names)
  registry.register_for_problem("pb-01-berth") -> 5 tools
  load_problem_config("pb-12-itt") -> 8 filtered tools, receive_webhook excluded
  registry.call("dispatch_road_itt", _hitl_approved=False) -> hitl_required error confidence 0
  Optimiser with weight None -> weight_bounds_valid failed, confidence 0.6
  /agent/switch-problem/pb-12-itt -> tools excludes event_trigger, matches registry
```

## Commits

- `e9a0b5c` fix(05-C1-H4): align YAML charter names and filter event_trigger
- `33bf9a0` fix(05-H1): enforce post_approval guard
- `387b5fc` fix(05-H2): add weight_bounds guardrail
- `1b81b65` fix(05-H3-M2): warn on factory fallback and narrow except
- `5f47ec4` fix(05-M1): downgrade confidence for unknown parties
- `7a5c5ec` fix(05-M4-L1): retry SSE broadcaster and warn
- `5ddba4e` fix(05-M3-H1): add YAML parity + negative guard tests
- `1ea74bf` fix(05-M5): document edge hooks isolation
- `850a010` fix(05-M6): cache last-known-good snapshots
- `b2bb1d2` fix(05-L2-L3-L4): type coercion, dead code, re-export
- `234d041` fix(05-tests): update expectations for 8 tools + trigger

All 15 issues resolved. Ready for Phase 6.
