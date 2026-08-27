---
phase: 05
status: dirty
issues: 15
critical: 1
high: 4
medium: 6
low: 4
reviewer: senior-code-reviewer
depth: deep
scope: c984075..HEAD
date: 2026-08-27
---

# Phase 5 Deep Review — Tool Integration + Notification + Robustness

## Summary

Phase 5 delivers all 8 PB-12 tools + 5 PB-01 stubs, registry, fallbacks, edge hooks, ROI math and 4 robustness scenarios. ToolResult contract, timeout, hallucination handling, confidence ranges, and mock-data mutation are correct and 68/71 tests pass (3 skipped S4-await-Phase-6). One critical charter drift (YAML tool names ≠ charter names) and a no-op post-approval guard require fixes before Phase 6. Weight-bounds guardrail is tested only via helper, not enforced in optimiser. Remaining issues are medium/low quality, security and typing gaps.

## Stats

- Files changed (Phase 5): 25 (14 source + 4 tests + 4 mock routers + 2 mock data + 1 main + summary)
- Tools implemented: 8 PB-12 + 5 PB-01 = 13 + 2 fallback stubs; TOOLSETS 7 problems
- Tests: 68 passed, 3 skipped, 0 failed (pytest app/tests/test_registry|tools|roi|robustness -v)
- Registry: canonical owner verified — `app/agent/problem_switcher.py` is consumer (`switch_problem` + lazy registry import in `app/main.py:182-193`)
- Cost math: $10,400 verified (`60*150 + 40*35`), $8K/incident ROI aliases present

## Severity Table

| Severity | Count | Meaning |
|----------|-------|---------|
| Critical | 1 | Breaks charter, cost wrong, switch fails |
| High | 4 | Incorrect logic, missing guardrail, hallucination/fallback broken, security bypass |
| Medium | 6 | Inconsistent metadata, incomplete validation, test gap, naming drift |
| Low | 4 | Style, typing, docs, dead code |

## Detailed Findings

### Critical

#### C1 — YAML tool names diverge from charter (charter constraint violated)
- **File:** `app/configs/pb-12-itt.yaml:28-53`
- **Category:** bug / charter-violation
- **Description:** Charter (§6) requires exact names `get_itt_candidates`, `check_road_itt_capacity`, `check_sea_itt_capacity`, `compute_itt_split`, `update_tuas_loading_sequence`, `dispatch_road_itt`, `request_feeder_hold`, `notify_parties`. YAML defines `query_container_readiness` (≠ `get_itt_candidates`), `compute_optimal_split` (≠ `compute_itt_split`) and includes `receive_webhook` (event trigger, not a tool). Registry `TOOLSETS["pb-12-itt"]` correctly uses charter names, so `app/main.py:182-196` merges `registry.list()` + `[t.name for t in config.tools]` via `dict.fromkeys()` and returns 9 deduped names containing the drifted YAML names. Clients reading `/agent/switch-problem` or `/agent/active-problem` see names that cannot be `registry.call()`ed (hallucinated). Plan §5.11 success criterion 5 and verification loop 5 fail if checked against YAML.
- **Fix:** Rename YAML entries to `get_itt_candidates` and `compute_itt_split`; remove or tag `receive_webhook` as `type: event_trigger` excluded from tool list merge. Alternatively make `switch_problem_endpoint` filter `config.tools` by `type != "event_trigger"` and map legacy names via alias table.

### High

#### H1 — post_approval guard is a no-op (security bypass)
- **File:** `app/tools/registry.py:120-121`, `app/tools/base.py:69-70,123-124`
- **Category:** security
- **Description:** `registry.call()` does `if tool.post_approval and not kwargs.pop("_hitl_approved", False): pass` — `pass` enforces nothing. `BaseTool.call()` re-injects `_hitl_approved` into kwargs then discards it. `DispatchRoadITTTool` and `RequestFeederHoldTool` (`post_approval=True`) can be executed without HITL approval. Plan §5.7/verification 7 says they must reject calls without prior approval; charter post_approval guard expected defense-in-depth. `test_robustness:100` passes `_hitl_approved=True` but negative case never tested via registry.
- **Fix:** In `registry.call`, return `ToolResult(output={"error":"HITL approval required..."}, confidence=0.0, metadata={"error":"hitl_required"})` when guard fires. Keep Phase 6.4 `tool_node` as authoritative check. Add test: `await registry.call("dispatch_road_itt", ..., _hitl_approved=False)` → error.

#### H2 — weight_bounds guardrail absent from optimiser (missing charter guardrail)
- **File:** `app/tools/optimiser.py:358-364`, `app/tests/test_robustness.py:22-28`
- **Category:** bug / quality
- **Description:** Charter + Plan §5.5 list 4 guardrails: `containers_per_block ≤ max`, `sea_containers ≤ feeder_available_teu`, `itt_arrival < vessel_departure - 60min`, `feeder_departure < tidal_deadline`, plus S2 requires `weight_bounds` (`weight_kg` missing/≤0). `optimiser.py:358` builds `guardrails_checked` with exactly 4 entries — weight check omitted. S2 coverage lives only in `_weight_bounds_guard` helper inside `test_robustness.py`, not in production code. `tuas_loading`/`container_readiness` also don't validate weights.
- **Fix:** Add `weight_bounds` to `optimiser.py` (or `container_readiness.py`) — scan `candidates["containers"]` for `weight_kg is None or <=0`, add `weight_bounds_valid` to `guardrails_checked`, downgrade confidence and emit `guardrail_failed` metadata when violated. Mirror S2 helper logic. Update verification 8.

#### H3 — silent swallow of import errors hides broken tool factory
- **File:** `app/tools/registry.py:69-70`, `app/tools/optimiser.py:111-112`, `app/tools/optimiser.py:17-24`
- **Category:** bug / quality
- **Description:** `_create_tool_by_name` catches `Exception` and returns `_GenericStubTool(name)` without logging. If a PB-12 module has a syntax error or missing dependency, `register_for_problem("pb-12-itt")` silently registers a stub that returns `{"stub":True}` with 0.9 confidence — tests could pass with wrong implementation. Same pattern in optimiser (`compute_itt_split_default` fallback) and `_load_cost_params`. Violates fail-fast, complicates debugging of platform switch.
- **Fix:** Log `warnings.warn` or `logger.warning` with `exc_info` when fallback to stub; optionally expose `metadata["_factory_fallback"]`. Keep stub for unknown problems but not for known `TOOLSETS` names — re-raise or return error ToolResult for `pb-12-itt`/`pb-01-berth`.

#### H4 — YAML `receive_webhook` counted as tool causes registry/YAML count mismatch
- **File:** `app/configs/pb-12-itt.yaml:50-53`, `app/main.py:182-196`, `.planning/phases/05-tool-integration/PLAN.md:65`
- **Category:** bug
- **Description:** YAML lists 6 tools including `receive_webhook` (trigger). `TOOLSETS["pb-12-itt"]` lists 8 charter tools. `register_for_problem` correctly loads 8; `load_problem_config("pb-12-itt")` exposes 6. Verification loop 12 expects switch to be symmetric; `app/tests/test_registry.py:109` iterates all 7 TOOLSETS but never asserts against YAML. Integration risk: Phase 6 may iterate `config.tools` expecting 8.
- **Fix:** Remove `receive_webhook` from `tools:` or give it `type: event_trigger` and filter in `switch_problem_endpoint` + docs. Align TOOLSETS authority: registry is SSoT, YAML is config source — reconcile and test `set(registry.list()) ⊆ set(cfg tool names mapped via alias)`.

### Medium

#### M1 — notify parties validation is warn-only (incomplete per Plan §5.10)
- **File:** `app/tools/notify.py:84-87`
- **Category:** quality
- **Description:** Plan says "Validate parties against known stakeholders in ProblemConfig". Implementation only `warnings.warn` for unknown parties, still sends and returns `status:sent` with 1.0 confidence. No rejection, no confidence downgrade. `KNOWN_STAKEHOLDERS` includes lowercase aliases (`citos_ppt`, `feeder`) that bypass useful validation.
- **Fix:** Downgrade confidence to 0.7 and set `metadata["unknown_parties"]` or reject if all parties unknown. Source validation from `ProblemConfig.systems`.

#### M2 — `_load_cost_params` silent catch masks YAML errors
- **File:** `app/tools/optimiser.py:17-24`
- **Category:** quality
- **Description:** Returns `{}` on any exception, falling back to hardcoded defaults (`150`, `35`, `800`, `4500`). Corrupt YAML or missing `cost_params` goes undetected; ROI test would still pass with wrong cluster assumptions. Violates charter ROI traceability (§5).
- **Fix:** Catch only `FileNotFoundError`/`yaml.YAMLError`, log warning, include `cost_params_source: "defaults (fallback)"` already present but also add warning metadata.

#### M3 — registry vs YAML naming drift not covered by tests
- **File:** `app/tests/test_registry.py:109-114`, `app/configs/pb-12-itt.yaml`
- **Category:** quality / test-gap
- **Description:** `test_register_for_problem_all_7` asserts `set(r.list()) == set(expected)` against `TOOLSETS`, not against YAML. No test asserts charter names match YAML `tools[].name`. Drift in C1/H4 would not be caught.
- **Fix:** Add test that loads YAML and asserts mapped names equal `TOOLSETS["pb-12-itt"]` (with alias for legacy `query_container_readiness` if kept).

#### M4 — SSE broadcaster single-check cache makes fallback permanent
- **File:** `app/tools/notify.py:40-64`, `app/mocks/routers/notify.py:18-37`
- **Category:** bug
- **Description:** `_broadcaster_checked`/`_broadcaster_cache` is set true on first `ImportError` and never re-tried. If `app.agent.sse` is loaded after first notify call (lazy Phase 7 wiring), subsequent `notify_parties` calls never publish SSE `notification` events. Graceful fallback becomes sticky failure. Plan §5.10 requires SSE `notification` event.
- **Fix:** Retry import after `N` calls or on each failure with exponential backoff, or invalidate cache when import succeeds. Same pattern in `notify.py` router.

#### M5 — `inject_feeder_berth_conflict`/`reset_edge_cases` deep-copy aliasing risk
- **File:** `app/tools/edge_cases.py:37-41`, `app/mocks/data.py:209-210`
- **Category:** bug
- **Description:** `reset_edge_cases` does `FEEDER_DATA.clear(); FEEDER_DATA.update(copy.deepcopy(_FEEDER_DATA_ORIGINAL))`. If edge hook added new keys (`conflict`, `delay_minutes`, `edge_case_note`), `clear+update` restores them but `FEEDER_DATA` identity is preserved (good). However `_FEEDER_DATA_ORIGINAL` was taken at import time via `copy.deepcopy(FEEDER_DATA)` — if `FEEDER_DATA` is mutated elsewhere before import snapshot, original is already polluted in long-running server. Current code correcta for test isolation but production server with concurrent injections needs copy-on-reset isolation.
- **Fix:** Already mitigated by `autouse` fixture in `test_tools.py:8-27` and `FEEDER_DATA` being module-global. Document that edge hooks are demo-only, not thread-safe; consider lock or per-run copy.

#### M6 — fallback tools share live mock data (not last-known-good snapshot)
- **File:** `app/tools/fallbacks.py:21-51`
- **Category:** quality
- **Description:** `CachedRoadCapacityTool`/`CachedSeaCapacityTool` call `get_truck_data()`/`get_feeder_data()` live, not a cached snapshot. After `inject_feeder_berth_conflict`, fallback returns conflicted data rather than last-known-good conservative defaults flagged `fallback_used:true`. Plan §5.1 says "return last-known-good or conservative defaults". Correct behavior per tests (`test_fallbacks_do_not_pollute_primary_outputs` expects isolation) but semantics are live read.
- **Fix:** Cache copy at module init or on first success, return deep copy with `fallback_used`. Acceptable as-is if documented; currently metadata correctly flags `fallback_used`.

### Low

#### L1 — broad `except Exception` + silent `pass` in SSE paths
- **File:** `app/tools/notify.py:105-116`, `app/mocks/routers/notify.py:38-39`
- **Category:** quality
- **Description:** Both `try: broadcaster.publish` blocks swallow all exceptions. Real SSE misconfiguration (e.g., `TypeError` in payload) is hidden. OK for robustness but should log.
- **Fix:** `except Exception as e: warnings.warn(str(e))` or `logger.debug`.

#### L2 — type looseness: `request_feeder_hold` accepts `hold_hours` as string via cast
- **File:** `app/tools/request_feeder_hold.py:32-33`, `app/tools/dispatch_road_itt.py:60-66`
- **Category:** quality
- **Description:** `float(hold_hours)` will coerce `"2"` successfully though JSON schema says `type:number`. BaseTool `call` does not validate types beyond presence/hallucination; relies on `execute` to coerce. No Pydantic/JSON-Schema validation as Plan §5.1 wrapper describes.
- **Fix:** Add lightweight type check (e.g., `jsonschema` or manual) in `BaseTool.call` or document that wrapper validates required/hallucinated only; full schema validation deferred.

#### L3 — dead code in `BaseTool.call` hitl round-trip
- **File:** `app/tools/base.py:69-70,123-124`
- **Category:** quality
- **Description:** `hitl_approved` popped at entry, re-inserted into `kwargs` before `execute`, then popped again after result. Neither `execute` implementations read `_hitl_approved` (they rely on registry guard). The re-insertion is dead. Harmless but confusing.
- **Fix:** Keep only registry-level pop; remove re-insertion in base wrapper, or make `BaseTool.call` enforce `post_approval` directly.

#### L4 — missing `app/tools/__init__.py` re-export not versioned but present
- **File:** `app/tools/__init__.py`
- **Category:** docs
- **Description:** Single docstring, no registry re-export. Not a bug; but `from app.tools.registry import registry` is canonical — worth re-exporting `registry`, `TOOLSETS`, `FALLBACKS` for discoverability.
- **Fix:** Add `from .registry import ...` to package init.

## Positive Observations

- **ToolResult contract exemplary:** `ToolResult(output, confidence, metadata)` with `tool_name/timestamp/duration_ms/run_id` auto-populated in `BaseTool.call:117-122`, hallucinated-arg and `missing_required` distinct errors, timeout via `asyncio.wait_for` — matches charter exactly.
- **Registry single-ownership is clean:** `app/tools/registry.py` is sole owner; `app/agent/problem_switcher.py` is narrow consumer, `app/main.py:151-205` lazily imports registry and tolerates `ImportError` — no duplicate definitions, switch endpoint compatible via `dict.fromkeys` merge.
- **Mock-data mutation hooks are correct:** `edge_cases.inject_*` mutates `app.mocks.data.FEEDER_DATA` / `_stale_minutes` so next `SeaITTCapacityTool`/`ContainerReadinessTool` sees conflict/staleness (`data.py:137-142` and `get_feeder_data:212-219`). `reset_edge_cases` restores via `deepcopy(_FEEDER_DATA_ORIGINAL)` and autouse fixture guarantees isolation across 68 tests.
- **Cost/ROI aliases thorough:** `optimiser.py:131-141` provides `baseline_all_road`, `baseline_all_road_cost`, `baseline`, `optimised`, `optimised_transport_cost`, `savings`, etc., keeping Plan aliases and charter math (`$12K→$10.4K→$1.6K→$8K`) all wired and tested.
- **Fallback isolation tested:** `fallbacks.py` sets `output.fallback_used` + `metadata.fallback_used/fallback_for` with `confidence 0.6`; `test_robustness:292-317` proves `tool_error` vs `tool_timeout` distinct paths and that 4 parallel fallbacks don't pollute primaries.
- **Peak-aware road logic recycled, not re-derived:** `_is_peak` with 30m pre-peak + 20m lingering and `PEAK_WINDOWS`, time-of-day fleet `18/20/22`, `cost_per_trip:150`, `capacity_ratio`, `esc_5` — faithful to prototype `optetruck_tools`.
- **PB-01 sibling proof is real:** Routers `vtis/optevoyage/berth` mounted behind `ImportError` guards in `app/main.py:19-60`, tool classes exist and `registry._MODULE_MAP` resolves them; switch `pb-12-itt ↔ pb-01-berth` verified end-to-end.
- **Notify SSE graceful:** `notify.py:108-116` + `routers/notify.py:18-37` both `try: from app.agent.sse else from app.main` and swallow, never crashes tool call; log + SSE + trace_hint triple-write is robust.

## Verification Against PLAN.md

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `pytest test_tools.py` all PB-12 pass | ✅ 42 passed |
| 2 | `pytest test_registry.py` (clear/register_many/switch) | ✅ 15 passed |
| 3 | Each tool returns valid ToolResult | ✅ via `TestToolResultFormat` + `test_robustness` |
| 4 | Tool 4 split 80/40=$10,400 + cost_vs_baseline+roi | ✅ `test_optimiser_80_40`, `test_roi` |
| 5 | JSON schemas match charter tool names | ⚠️ registry yes, YAML no (C1) |
| 6 | Edge hooks mutate mock → next T3 sees conflict | ✅ `TestEdgeCases` |
| 7 | Post-approval reject without HITL | ❌ guard is `pass` (H1) |
| 8 | Input validation guardrails (weight/vessel/tidal) | ⚠️ weight missing (H2), others ✅ |
| 9 | Notification SSE + trace | ✅ `TestNotifyParties` |
| 10 | Sibling stubs switch correctly | ✅ `TestPB01Switch` |
| 11 | 4 robustness scenarios | ✅ S1-S3 pass, S4 skipped pending Phase 6 (3 skipped) |
| 12 | Problem switching pb-01 ↔ pb-12 | ✅ via registry; endpoint merges YAML drift (C1) |

## Severity Counts

- Critical 1, High 4, Medium 6, Low 4 — **15 total**
- Must-fix before Phase 6: C1, H1, H2

## Recommendations

1. Fix C1 YAML rename + trigger filter — 15 min
2. Implement H1 guard return instead of `pass` + add negative test — 10 min
3. Add weight_bounds to optimiser guardrails (reuse robustness helper) — 20 min
4. Add warning/log in `_create_tool_by_name` fallback and invalidate SSE broadcaster cache — 10 min

---
*Generated by deep review against PLAN.md, charter constraints, cross-file import graphs and call chains.*
