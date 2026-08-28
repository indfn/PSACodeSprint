---
phase: 06
status: dirty
issues: 19
critical: 2
high: 6
medium: 7
low: 4
reviewer: gsd-code-reviewer
depth: deep
scope: HEAD
date: 2026-08-28
files_reviewed_list:
  - app/agent/state.py
  - app/agent/prompts.py
  - app/agent/nodes.py
  - app/agent/graph.py
  - app/agent/run.py
  - app/agent/monitor.py
  - app/agent/escalation.py
  - app/agent/confidence.py
  - app/agent/trace.py
  - app/agent/validation.py
  - app/agent/resilience.py
  - app/agent/sse.py
  - app/agent/problem_switcher.py
  - app/agent/tool_schemas.py
  - app/hitl/models.py
  - app/hitl/gates.py
  - app/hitl/handler.py
  - app/shared/logging.py
---

# Phase 06 Deep Review — PSA Nexus Agent Core (LangGraph + HITL + Escalation + Resilience)

## Summary

Phase 6 delivers the LangGraph agent core across 18 files: `StateGraph` with 4 nodes (`agent`, `tools`, `hitl`, `monitor`), `MemorySaver` with `thread_id`, single `hitl_node` using `interrupt()`/`Command(resume=)`, 5 HITL gates with per-gate `timeout`/`timeout_action`, 7 escalation triggers, deterministic confidence fallback plus `risk_score` in every `TraceEntry`, monitoring loop with deviation re-compute, SSE broadcaster with replay buffer, rate-limit retry + fallback provider, `fallback_used` flag with distinct `timeout` vs `503` handling, container truncation for checkpoint `deepcopy`, hallucinated-tool handling, structured JSON logging, and 6 input-validation guardrails. Charter workflow (webhook → T1/T2/T3 → T4 → HITL-1 → HITL-2/HITL-3 → dispatch/hold → T5 → HITL-4 → monitor → deviation → HITL-5 → delta dispatch → T5_2) completes end-to-end in `test_agent_e2e`.

Two critical charter-breakers block production readiness: (1) `HITL MODIFY` re-compute always fails because `handler.py` calls `asyncio.run()` inside a running LangGraph event loop — charter A-09 *MODIFY must re-validate + re-run Tool 4 + re-present card* never executes; (2) `tool_node` truncates `get_itt_candidates` `containers` to 5 elements for checkpoint storage and then writes the truncated payload into `context.candidates`, so the subsequent `compute_itt_split` receives only 5/120 containers and optimiser cost/math is silently wrong (also blinds `weight_bounds` guardrail). Six high-severity deviations remain: escalation thresholds artificially suppressed vs charter, HITL stale-resume gate normalization missing, webhook past-departure validation downgraded to warning (422 not returned), edge-case injection global-mutates mock data breaking concurrency isolation, manual `messages.append()` against `Annotated[list, operator.add]` risks checkpoint duplication, and `hitl_node` guard duplication. Remaining medium/low items are guardrail timing, SSE persistence, broad `except: pass` masking, and payload duplication.

**Verdict:** `status: dirty` — fix C1/C2 + H1-H3 before Phase 7 UI integration; H4 (concurrency) before any multi-user demo.

## Stats

- Files reviewed: 18 source (14 agent + 3 hitl + 1 shared) + 2 auxiliary (`app/main.py`, `app/shared/models.py`) cross-referenced
- Lines reviewed: ~3,900 (nodes.py 1,046, graph.py 102, run.py 255, monitor.py 259, escalation.py 195, handler.py 285, etc.)
- Graph assembly: `StateGraph(AgentState)` with `START->agent`, `agent->[tools|hitl|monitor|END]`, `tools->agent`, `hitl->agent`, `monitor->[hitl|agent|END]`, singleton `MemorySaver` via `build_graph()` reuse (`graph.py:60-95`)
- HITL gates: 5 gates at `hitl/models.py:54-131` with correct timeouts `1800/900/900/600/1800` and actions `escalate/cancel_dispatch/escalate/hold_sequence/halt`
- Trace/escalation: `risk_score` present in every `log_trace` call (`trace.py:30-48`, `nodes.py:389-390`, `nodes.py:718`, `monitor.py:174`), `confidence` clamped `0.0-1.0` (`nodes.py:256-258`)
- Tool handling: `timeout (+5s outer wait_for) vs 503 distinct` (`nodes.py:538-598`), `fallback_used` set in both branches (`nodes.py:548-580`, `trace.py:714-718`)
- Resilience: `chat_with_rate_limit` retries `2**attempt` + fallback provider (`resilience.py:12-83`), `is_hitl_stale` used in both `run.py:191-216` and `app/main.py:194-205` and `gates.py:163-175`
- SSE: `SSEBroadcaster` with `deque(maxlen=100)` + `Last-Event-ID` replay (`sse.py:19-100`)

## Severity Table

| Severity | Count | Meaning |
|----------|-------|---------|
| Critical | 2 | Charter §4/A-09 broken, wrong optimisation cost, data loss, stale HITL race |
| High | 6 | Escapes charter thresholds, 422 contract broken, concurrency corruption, checkpoint semantics wrong |
| Medium | 7 | Incomplete guardrail timing, SSE durability, provider wiring, validation blind spots, reliability |
| Low | 4 | Style, typing, log hygiene, dead code |

## Detailed Findings

### Critical

#### CR-01 — HITL MODIFY re-compute always fails (`asyncio.run` inside running loop)
- **File:** `app/hitl/handler.py:181-216`
- **Category:** bug / charter-violation (A-09)
- **Description:** Charter A-09 *MODIFY* requires: re-validate vs LTA/feeder/timeline guardrails, re-run Tool 4 `compute_itt_split` with `modifications`, present updated cost, re-request approval. `handle_hitl_response` implements this via an inner `async def _rerun()` + `asyncio.run(_rerun())`. `hitl_node` (`app/hitl/gates.py:84`) is invoked inside `graph.ainvoke(...)` which runs on a live asyncio event loop. `asyncio.run()` raises `RuntimeError: cannot be called from a running event loop`. Code tries to detect this with `get_running_loop()` + `raise RuntimeError("in async loop — defer")` but then falls through to the same `asyncio.run()` in the `except RuntimeError` handler (line 204), so the second call also raises. Outer `except Exception as exc` catches it and appends `Re-compute after MODIFY failed: ...` to messages without updating `split_result` — the card is re-presented with stale cost. MODIFY appears to work in manual tests (`test_hitl` may call handler outside graph) but fails end-to-end. The `modifications` payload is also never validated for type safety (caller can send arbitrary dict that overwrites constraints).
- **Fix:**
```python
# app/hitl/handler.py — make handler async and await registry.call directly
async def handle_hitl_response(state, gate, decision, registry=None):
    ...
    elif d == "modify":
        ...
        if not validation.get("valid"):
            ...
            return state
        # A-09: re-run Tool 4 inside the graph's async context
        from app.tools.registry import registry as _reg
        reg = registry or _reg
        ctx = state.get("context", {}) or {}
        result = await reg.call(
            "compute_itt_split",
            candidates=ctx.get("candidates", {}),
            road_capacity=ctx.get("road_capacity", {}),
            sea_capacity=ctx.get("sea_capacity", {}),
            tuas_vessel_departure=ctx.get("tuas_vessel_departure"),
            constraints={**ctx.get("constraints", {}), **modifications},
            _run_id=state.get("run_id",""),
        )
        out = result.output if hasattr(result, "output") else result.get("output", {})
        state.setdefault("context", {})["split_result"] = out.get("optimal_split", out)
        state["context"]["split_alternatives"] = out.get("alternatives", [])
        ...

# app/hitl/gates.py — make hitl_node async, await handler
async def hitl_node(state):
    ...
    decision = interrupt(interrupt_payload)
    ...
    updated = await handle_hitl_response(state, gate_for_handler, decision)
    return updated
```
Add `pytest` covering `modify` inside `graph.ainvoke` (not direct handler call) asserting `split_result` changed.

#### CR-02 — Container truncation poisons downstream optimiser and guardrails
- **File:** `app/agent/nodes.py:616-634` (serialisation), `app/agent/nodes.py:638-649` (context write + messages), `app/agent/validation.py:21-38` (`_guard_weight_bounds`)
- **Category:** bug / correctness / checkpoint
- **Description:** To avoid the 40 s `MemorySaver` deepcopy (120 containers × ~1 KB ≈ 120 KB per checkpoint × multiple copies), `tool_node` truncates `get_itt_candidates` output to 5 containers and stores the truncated dict in both `tool_results[call_id]` and `context.candidates` (line 643). Subsequent `compute_itt_split` receives `candidates` with only 5 containers via `ctx.get("candidates", {})` (line 94-95 in `monitor.py`, line 855-860 in `nodes.py`). Optimiser therefore optimises the wrong problem — the charter 80/40=$10,400 math is computed from a stubbed snapshot (`generate_containers()` fallback inside `_MockProvider`), masking the production bug. `_guard_weight_bounds` likewise scans only the 5 retained containers, missing weight violations in the other 115. Trace/messages also truncate independently (lines 692-697, 714-718), but the canonical stored state is already lossy. The comment says "Avoid 40s deepcopy" but the fix trades correctness for speed — checkpoint still deepcopies the messages list which now holds a truncated but still nested `containers` list plus duplicated JSON strings.
- **Fix:** Keep full result for computation, truncate only for checkpoint-persisted copies. Pattern:
```python
# keep full output for logic
full_out = result_obj.output if hasattr(result_obj, "output") else {}
full_serialised = {"output": full_out, "confidence": conf, "metadata": meta}
# write full to context for optimiser
if name == "get_itt_candidates":
    ctx["candidates"] = full_out
    ctx["_candidates_full_len"] = len(full_out.get("containers", []))
# store truncated ONLY in checkpoint-visible fields (tool_results + messages + trace)
trunc = _truncate_for_checkpoint(full_out)  # keep 5 + counts, already implemented
serialised_for_state = {"output": trunc, "confidence": conf, "metadata": meta}
results[call_id] = serialised_for_state
# also keep full containers in a non-checkpoint sidecar if needed, e.g. `state["_full_candidates"]` excluded via `Annotated[..., None]` or external store keyed by run_id
```
For validation, run guardrail against `full_out` or against a separate `state["_full_candidates"]` cached outside checkpoint. Add assertion in test: after `get_itt_candidates`, `ctx["candidates"]["total_containers"] == 120` while `tool_results[x]["output"]["containers_truncated_total"] == 120`.

---

### High

#### HI-01 — Escalation thresholds intentionally suppressed vs charter §4 (triggers #3 and #5 never fire on nominal)
- **File:** `app/agent/escalation.py:25-38` (`check_cost_exceeded`), `app/agent/escalation.py:76-124` (`check_road_capacity`), `app/agent/nodes.py:663-667` (action_cost comment)
- **Category:** bug / charter-violation
- **Description:** Charter §4 authoritative: `| 3 | Financial recovery cost > limit | action_cost > $10,000 | escalate to Duty Manager |` and `| 5 | Road ITT capacity below threshold | available_trucks < 60% required | escalate to human |`. Implementation suppresses both on the nominal path:
  - `check_cost_exceeded` returns `False` unless `ctx["action_cost"]` is explicitly set (lines 30-33). `ctx["action_cost"]` is set to `cost_vs_baseline.direct_transport_savings` (1600, <10000) in `nodes.py:665`, so `$10,400` total transport cost never triggers. Charter reads "financial recovery cost" as incremental, but the doc comment says "do NOT auto-derive from total_transport_cost which is 10400 ... would always fire" — the fix makes trigger #3 dead unless a test injects `action_cost`.
  - `check_road_capacity` (lines 98-111) returns `False` if `available >= max_per_wave (20)` even though `required = 80` and `available/required = 0.25 < 0.6`. Comment: "Total 60 trips can be done over multiple waves with 20 trucks" — wave-based execution is not in the charter and the per-wave capacity (20) equals `available`, so nominal never escalates. This hides a real charter violation where road fleet is insufficient for a single-wave but the demo pretends multi-wave.
  Plan §5.11 verification 5 says all 7 triggers use charter thresholds exactly — current code fails strict comparison.
- **Fix:** Align to charter verbatim, keep nominal green via charter-compliant setup (not via code suppression):
```python
def check_cost_exceeded(state, threshold_dollars=10000) -> bool:
    ctx = state.get("context", {}) or {}
    # Charter §4: action_cost is total_transport_cost from optimiser
    # For nominal, cost $10,400 should NOT fire only if threshold is $10,000 and charter allows $10,400 as *optimised* (incurred regardless) — the *recovery* cost is savings vs baseline.
    # Clarify: if charter means incremental, document and expose both; else use total and adjust fixture to $9,500
    cost = ctx.get("action_cost") or (ctx.get("split_result", {}) or {}).get("total_transport_cost")
    return float(cost) > threshold_dollars if cost is not None else False

def check_road_capacity(state, threshold_ratio=0.6) -> bool:
    ctx = state.get("context", {}) or {}
    required = (ctx.get("split_result", {}) or {}).get("road_trips") or ctx.get("required_trucks") or 0
    available = ctx.get("available_trucks") or (ctx.get("road_capacity", {}) or {}).get("available_trucks") or 0
    if not required: return False
    return (float(available) / float(required)) < threshold_ratio
```
Then adjust demo fixtures so nominal `available`/`required` and `cost` don't trip (e.g., set `available=50` for test or `threshold=65%`), or accept that nominal *should* escalate and update verification expectation. Document wave assumption in `constraints` rather than hard-coding bypass.

#### HI-02 — HITL stale-resume gate normalization missing → wrong 422 vs silent accept
- **File:** `app/agent/resilience.py:108-126` (`is_hitl_stale`), `app/main.py:197-205`, `app/hitl/gates.py:163-175`
- **Category:** bug / security
- **Description:** `is_hitl_stale` compares `pending_id != gate_id` with strict `==` (line 122). HITL gates exist in three forms (`HITL-1`, `hitl_1`, `hitl-1`/`hitl_1` lower) added at `models.py:96-135` and normalised elsewhere via `lower().replace("-","_")` (e.g., `nodes.py:46`, `handler.py:102-103`). A stale resume with `gate_id: "hitl_1"` against pending `HITL-1` will be considered mismatch and incorrectly return `True` (stale) even when it's the same gate, or the inverse — a resume for a different gate may pass through. `app/main.py:197-205` re-checks stale *before* `Command(resume=)`, while `gates.py:163` re-checks *after* interrupt resume. The two checks use different logic (`runs[run_id]["status"]` terminal vs `is_hitl_stale`), so a timeout that set status `halted` but left `hitl_pending` intact could be considered not stale by one and stale by the other, creating a race where late `approve` is either accepted after halt or rejected with inconsistent error message (`hitl_pending is None` vs `status in terminal`). Missing `hitl_gate_entered_at` TTL check — charter requires 30-min second-level halt if Duty Manager silent, but timeout is not driven by a background timer; stale detection is the only guard.
- **Fix:**
```python
def _norm(g): return str(g).lower().replace("-", "_") if g else ""
def is_hitl_stale(state, gate_id=None) -> bool:
    status = state.get("status", "")
    pending = state.get("hitl_pending")
    pid = _norm(pending.get("gate_id") if isinstance(pending, dict) else getattr(pending, "gate_id", None) if pending else None)
    gid = _norm(gate_id)
    if pending is None and status in ("halted","cancelled","holding","completed","failed"):
        return True
    if status in ("halted","cancelled","holding") and gid:
        # only stale if same gate already terminal; different gate is not stale (new HITL-5)
        if pid and pid != gid:
            return False  # pending is HITL-5, stale check for HITL-1 should not block
        if pid is None:
            return True
        # add TTL check per gate timeout_seconds
        entered = state.get("hitl_gate_entered_at")
        if entered:
            from datetime import datetime, timezone
            try:
                age = (datetime.now(timezone.utc) - datetime.fromisoformat(entered.replace("Z","+00:00"))).total_seconds()
                gate_timeout = (pending.get("timeout_seconds", 1800) if isinstance(pending, dict) else 1800)
                if age > gate_timeout:
                    return True
            except Exception:
                pass
    return False
```
Apply same `_norm` in `app/main.py:192` and `gates.py:166`. Add test: `resume after halted with gate_id alias hitl_1 → 422` and `resume after HITL-1 approved, now waiting HITL-2 with old HITL-1 gate_id → not stale`.

#### HI-03 — Webhook past `tuas_vessel_departure` silently accepted (should be 422)
- **File:** `app/agent/run.py:37-48`, `app/main.py:72-86`, `app/agent/resilience.py:129-141`
- **Category:** bug / validation
- **Description:** Requirement A-21 + Plan Success Criteria 8: *Input validation guardrails checked at webhook bootstrap (422, not 500)*. `create_initial_state` validates `container_count >=50` strictly (raises `ValueError` → `receive_webhook` maps to 422). But `tuas_vessel_departure <= now` only logs `structured_log("vessel_departure_in_past")` and continues (line 46). Pydantic `ITTCoordinationEvent.tuas_vessel_departure` is `str` without `ge`/`future` validator, so FastAPI returns 200. Mock tool data uses `2026-08-19T20:00:00+08:00` which is in the past relative to real `2026-08-28` execution time — every demo event would be "departed" but monitor still computes margin as positive. `validate_webhook_event` in `resilience.py` checks `vessel_id`/`tuas_vessel_departure` presence but not future-ness and is never called by `receive_webhook`. Second-level `containers_ready > container_count` yields 400 not 422 (line 84).
- **Fix:**
```python
# app/shared/models.py — add validator
from pydantic import field_validator
from datetime import datetime, timezone, timedelta
class ITTCoordinationEvent(BaseModel):
    ...
    @field_validator("tuas_vessel_departure")
    @classmethod
    def _must_be_future(cls, v: str):
        try:
            dt = datetime.fromisoformat(v.replace("Z","+00:00"))
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            if dt <= datetime.now(timezone.utc) + timedelta(minutes=30):
                raise ValueError("tuas_vessel_departure must be > now + 30min")
        except ValueError:
            raise
        except Exception:
            raise ValueError("invalid tuas_vessel_departure")
        return v

# app/main.py — call resilience helper and normalise 422
ok, err = validate_webhook_event(event.model_dump())
if not ok:
    raise HTTPException(status_code=422, detail=err)
```
Keep demo fixtures with `+7 days` departure. Map `containers_ready` violation to 422 as well.

#### HI-04 — Edge-case injection mutates global mock data → concurrent runs corrupt each other
- **File:** `app/main.py:296-328` (`inject_edge_case`), `app/tools/edge_cases.py:37-41` (mutates `app.mocks.data.FEEDER_DATA`), `app/agent/monitor.py:39-49`, `app/agent/escalation.py:66-71` (`mock_data._stale_minutes`)
- **Category:** bug / concurrency
- **Description:** Plan §6.12 explicitly requires *Concurrency isolation — per-`run_id` overrides in `app.mocks.data:_overrides: dict[run_id, dict]`*. Implementation does global mutation: `inject_feeder_berth_conflict(feeder_id, new_departure)` overwrites `FEEDER_DATA["departure_window"]["latest"]` and `berth_status`, `inject_stale_data(time_offset_minutes)` sets `app.mocks.data._stale_minutes`. All subsequent `check_sea_itt_capacity` calls for *any* `run_id` see the conflict, so two parallel demos (one nominal, one with injected conflict) both deviate. `app/main.py:312` tries to mark `ctx["injected_edge"]` but `monitor_node` ignores it and reads global via `registry.call(... _run_id=state.get("run_id"))` — `registry.call` does not check `_overrides` (added in fix `M5` placeholder but not wired for sea). No `POST /agent/reset-mocks` isolation, and `MemorySaver` stores per-thread checkpoints but mock data is process-global. Tests may pass sequentially but `pytest -x -k e2e` with `asyncio.gather` would flake.
- **Fix:** Implement per-run overrides as designed:
```python
# app/mocks/data.py
_overrides: dict[str, dict] = {}
def get_feeder_data(feeder_id, run_id=""):
    base = FEEDER_DATA[feeder_id]
    ov = _overrides.get(run_id, {}).get(feeder_id)
    return {**base, **ov} if ov else base

# app/tools/edge_cases.py
def inject_feeder_berth_conflict(feeder_id, new_departure, run_id=""):
    if run_id:
        _overrides.setdefault(run_id, {})[feeder_id] = {"berth_status": "conflict", "departure_window": {"latest": new_departure}}
    else:
        # legacy global for backwards compat
        FEEDER_DATA[feeder_id]["berth_status"] = "conflict"

# app/agent/monitor.py — pass _run_id through
result = await registry.call("check_sea_itt_capacity", feeder_id=feeder_id, current_time=_now_iso(), _run_id=state.get("run_id"))

# app/main.py inject — forward run_id
inject_feeder_berth_conflict(feeder_id=feeder_id, new_departure=..., run_id=run_id or payload.get("run_id"))
```
Also include `run_id` in `get_trace`/`stream` reset paths and document "single demo at a time" limitation if not fixed.

#### HI-05 — `messages` mutated via `append` against `Annotated[list, operator.add]` — checkpoint duplication & unbounded growth
- **File:** `app/agent/nodes.py:332-339` (hallucinated retry append), `app/agent/nodes.py:346-350` (assistant with tool_calls), `app/agent/nodes.py:373-374`, `app/agent/nodes.py:639-703` (tool results loop)
- **Category:** bug / quality
- **Description:** `AgentState` defines `messages: Annotated[list[dict], operator.add]` (`state.py:13`). Idiomatic LangGraph nodes return `{"messages": [new_msg]}` and the reducer concatenates. This codebase mutates `state["messages"]` in place via `state.setdefault("messages", []).append(...)` and returns the full `state` dict. On checkpoint replay, LangGraph restores `state` from `MemorySaver` and then re-applies the reducer delta — existing messages may be duplicated. Worse, `tool_node` appends one entry per tool call per iteration; with 7 tool batches the list grows to ~25 messages, each JSON-encoded in truncated form but still containing `container_ids` (80 ids × ~12 chars ≈ 1 KB per message). Combined with `trace` (≈15 entries) the checkpoint size exceeds `MemorySaver`'s intended small state, re-introducing the deepcopy cost truncation was meant to avoid. The `hitl_handler` also does `state["messages"].append(...)` on `reject`/`modify` (lines 125-129, 171, 212).
- **Fix:** Return deltas for `messages` instead of mutating:
```python
# inside agent_node, instead of state.setdefault(...).append(...)
new_messages = []
if invalid_calls and not valid_calls:
    new_messages.append({"role": "user", "content": f"Unknown tools: ..."})
    return {"messages": new_messages, "pending_tool_calls": [], "status": "running"}
elif valid_calls:
    new_messages.append({"role": "assistant", "content": content or "", "tool_calls": [...]})
    return {"messages": new_messages, "pending_tool_calls": valid_calls, "status": "calling_tools", ...}
# LangGraph reducer will add them once
```
If in-place mutation is retained, ensure `AgentState` uses `total=False` correctly and that nodes *do not* also return `messages` delta — pick one pattern. Add assertion in `test_agent_e2e` that `len(messages)` after two full cycles equals expected count, not double.

#### HI-06 — `hitl_node` guard duplicated and races with `resume_agent` stale check
- **File:** `app/hitl/gates.py:163-175` (post-resume terminal guard), `app/agent/run.py:200-216` (`is_hitl_stale` before `Command(resume=)`), `app/main.py:188-209` (duplicate terminal check in `hitl_respond`)
- **Category:** bug / quality
- **Description:** Stale-resume protection exists in three places with different predicates: `gates.py` checks `status in (halted,cancelled,holding) and hitl_pending is None` *after* `interrupt` resume; `run.py` checks `is_hitl_stale` *before* `Command(resume=)`; `main.py` checks `runs[run_id]["status"]` terminal *before* fetching checkpoint. The in-memory `runs` dict and the `MemorySaver` checkpoint can diverge (webhook stores `state` snapshot, resume updates it, but `clear`/`reset` may evict one). A timeout handler (`handler.py:227-278` `d=="timeout"`) sets `hitl_pending=None` and `status=halted|holding|cancelled`; if the client then `POST /agent/hitl/respond` with stale data, `main.py:190` raises 422 from `runs` cache even though checkpoint may have already advanced to next gate (`HITL-5`) where resume *should* succeed. Conversely, if `runs` was evicted (`MAX_RUNS` overflow), `main.py` falls through to checkpoint check which may incorrectly allow a late HITL-1 approve after global timeout. No `hitl_gate_entered_at` TTL comparison is used.
- **Fix:** Single source of truth — checkpoint, not `runs`. Remove `runs[run_id]["status"]` early return in `app/main.py:188-192` and rely solely on `is_hitl_stale(vals, gate_id)` against checkpoint `vals`. Deduplicate to one implementation (e.g., `resilience.is_hitl_stale`) called both in `gates.py` (after) and `main.py`/`run.py` (before). Include `hitl_gate_entered_at` age check as in HI-02.

---

### Medium

#### MD-01 — Guardrails checked only after tool batch, not at webhook bootstrap / before T4 / before post-approval
- **File:** `app/agent/nodes.py:772-784` (post-batch `validate_all`), `app/agent/run.py:19-48` (no `validate_all` call), `app/agent/monitor.py` (no pre-T4 check)
- **Category:** quality / charter (A-21)
- **Description:** Requirement A-21 + Plan §6.8: *6 guards checked at webhook bootstrap + before each Tool 4 computation + before each post-approval tool*. Current code calls `validate_all(state)` only after `tool_node` completes a batch (line 774). No validation at `create_initial_state` (webhook) — `weight_bounds` in particular cannot fire until after `get_itt_candidates` returns, so Scenario 2 (incomplete data, missing `weight_kg`) is detected only via `confidence` penalty (`nodes.py:777-781` sets `confidence=0.6`) rather than direct guardrail failure and alternative tool query. No pre-`compute_itt_split` explicit check; if `block_capacity` fails, optimiser still runs and may return overflow routing without `guardrail_failed` metadata. `validation.py:177-204` dutifully logs `guardrail_failed` but callers ignore return value except for that one `weight_bounds` confidence override.
- **Fix:** Call `validate_all` in three places:
```python
# run.py create_initial_state — after building context
from app.agent.validation import validate_all
fails = validate_all(state)
if any(f["guard"]=="weight_bounds" for f in fails):
    state["confidence"] = 0.6  # or reject event with 422

# nodes.py agent_node — before setting HITL-1
if state.get("context", {}).get("split_result"):
    fails = validate_all(state)
    if fails:
        state["messages"].append({"role": "user", "content": f"Guardrails failed: {fails}. Re-optimise."})
        continue

# tool_node — before dispatch_road_itt/request_feeder_hold (post-approval)
fails = validate_all(state)
if any(f["guard"] in ("vessel_margin","tidal_window") for f in fails):
    return error ToolResult with confidence 0.0
```
Add `pytest` for each guard (e.g., `inject weight=0 → validate_all returns weight_bounds failure → confidence 0.6 → escalation #1`).

#### MD-02 — `weight_bounds` blind to truncated containers (only first 5 checked)
- **File:** `app/agent/validation.py:21-38` (`_guard_weight_bounds`), `app/agent/nodes.py:616-643` (truncation)
- **Category:** bug / quality
- **Description:** Directly caused by CR-02. `_guard_weight_bounds` iterates `candidates.get("containers", [])` which after `tool_node` truncation has length 5. A malformed payload with `weight_kg <=0` in container #50 passes guard, causing Scenario 2 ("incomplete data") to not trigger guardrail but instead rely on `deterministic_score` staleness penalty. Also, no check for `weight_kg is None` vs `0` distinction per YAML — both should fail but message only lists first 5.
- **Fix:** Fix CR-02 first (keep full candidates for validation). Additionally, validate against the *tool output before truncation* — pass `full_out` to guardrail or re-fetch from `state["_full_candidates"]`. Include property test: inject one bad weight at index 100, assert `validate_all` fails.

#### MD-03 — Tool `timeout` vs `503` distinction conflated by string matcher
- **File:** `app/agent/nodes.py:538-569` (`asyncio.wait_for` outer), `app/agent/nodes.py:569` (`"timeout" in str(exc).lower()`)
- **Category:** quality
- **Description:** Plan Success Criteria 7: *tools (timeout vs 503 distinct, partial batch)*. Outer `asyncio.TimeoutError` branch correctly logs `tool_timeout_fallback` with `fallback_used` and duration `timeout_sec*1000`. Generic `except Exception` branch checks `is_503 = "503" in exc or "service unavailable" or "timeout" in str(exc)` — so a tool that raises `TimeoutError("upstream timeout")` as a string exception will be misclassified as 503 fallback (`tool_error_fallback`) not timeout. The two branches also produce different `metadata.error` values (`"timeout"` vs actual exc string), breaking downstream `deterministic_score` error counting (`confidence.py:44-50` checks `meta.get("error")`). Partial-batch handling (continue on blocked_hitl / fallback) is correct but not tested for mixed success+timeout in same batch — if one tool times out and fallback succeeds, confidence not downgraded.
- **Fix:**
```python
try:
    result_obj = await asyncio.wait_for(registry.call(...), timeout=timeout_sec+5)
except asyncio.TimeoutError as te:
    # dedicated timeout path
    ...
except Exception as exc:
    if "503" in str(exc) or "service unavailable" in str(exc).lower():
        # 503 path
        ...
    else:
        # other error — no fallback unless in FALLBACKS
```
Remove `"timeout"` from `is_503`. Add test: batch `[check_road(timeout), check_sea(success)]` → one fallback_used, one not, trace contains both `tool_result` events.

#### MD-04 — SSE broadcaster replay not durable across restart; heartbeat not in buffer
- **File:** `app/agent/sse.py:19-100`, `app/main.py:252-273`, `app/agent/trace.py:69-80`
- **Category:** quality
- **Description:** `SSEBroadcaster` stores buffers in process memory (`self.buffers: dict[str, deque]`). Plan §6.12: *SSE disconnect — Last-Event-ID replay*. Implementation correctly replays buffered events on `GET /agent/stream/{run_id}` (line 72-77) and heartbeats live clients every 15 s (line 86). But heartbeat (`: heartbeat`) is *not* buffered, so a client that connects after a quiet period gets no data until next real event and may time out. Buffers are lost on server restart — `MemorySaver` checkpoint replays state but not SSE history, so `export_trace` and SSE diverge. `clear(run_id)` is called by `POST /agent/reset/{run_id}` but not on `halted`/`completed` — `buffers` leaks for abandoned runs (`MAX_RUNS` does not clear SSE). `publish` with `run_id=""` silently drops (line 31-32) — early `create_initial_state` errors never stream. No `retry:` field in SSE format.
- **Fix:** Buffer heartbeats or document non-persistence. Add `run_id` TTL (e.g., 30 min LRU) mirroring `MAX_RUNS`. Ensure `publish` raises or logs when `run_id` empty. Consider persisting last 100 events to `runs[run_id]["trace"]` as fallback replay source when `broadcaster` buffer missing. Add `retry: 3000` in `_format_sse`.

#### MD-05 — Provider rate-limit fallback env wiring incomplete; `adapt_tools_for_provider` double-conversion not fixed
- **File:** `app/agent/nodes.py:171-193` (schema adaptation comment), `app/agent/resilience.py:86-105` (`_try_fallback_provider`), `app/configs/pb-12-itt.yaml` (llm.fallback fields)
- **Category:** bug / quality
- **Description:** `chat_with_rate_limit` falls back to `cfg.llm.fallback_provider` (lines 93-103) constructing dict with `fallback_model/api_key_env/base_url`. But `ProblemConfig` YAML actually nests fallback as `llm.fallback.{provider,model,api_key_env}` in some phases, and flat `llm.fallback_provider` in others — the lookup `llm.get("fallback_provider")` may miss. No test covers 429 → fallback path with real `create_provider` (requires `api_key` present). `nodes.py:171-193` notes adapter double-conversion for Anthropic but leaves workaround comment without code: `adapt_tools_for_provider(raw_schemas, provider_name)` produces Anthropic `input_schema` format, but `AnthropicProvider.chat` expects OpenAI `tools` and does its own conversion — passing pre-converted Anthropic format would double-wrap. Current path falls back to mock provider when `api_key == ""`, masking the bug in production with real key.
- **Fix:** Test provider matrix with real adapters: `pytest test_provider -k anthropic` with `tools=[{name, description, parameters}]` and assert no `KeyError`. Make `_try_fallback_provider` handle both flat and nested shapes:
```python
fb = llm.get("fallback") or {}
fb_name = llm.get("fallback_provider") or fb.get("provider")
fb_model = llm.get("fallback_model") or fb.get("model")
```
In `nodes.py`, pass `raw_schemas` to `provider.chat` and let provider do its own adaptation; remove manual `adapt_tools_for_provider` call or make it conditional on `provider_name in ("mock",)`.

#### MD-06 — HITL fast-path duplication drifts from canonical sequence logic
- **File:** `app/agent/nodes.py:28-80` (pre-LLM fast-path), `app/agent/nodes.py:430-467` (post-LLM deterministic gating)
- **Category:** quality
- **Description:** Two implementations set HITL gates deterministically: early fast-path (before LLM) and late gating (after LLM confidence + escalation). Fast-path sets `HITL-1..4` based on `split_result`/`hitl_history`/`tuas_sequence`; late gating repeats same `has("HITL-1")` checks but adds `dispatched` guard for HITL-4. They can diverge: fast-path sets `HITL-4` when `ctx.tuas_sequence` exists, late gating requires `tuas_sequence OR dispatched` — a state with `tuas_sequence` but not `dispatched` triggers HITL-4 via fast-path but not via late gating, causing double HITL-4 on next iteration. Fast-path also bypasses LLM reasoning entirely (returns without LLM call), so if LLM would have chosen different tool sequence for a non-PB-12 problem, that reasoning is skipped. Not triggered for PB-12 happy path but violates platform generality (F-13/PB-01).
- **Fix:** Keep single canonical setter `def _ensure_next_hitl(state)->bool` called from one place (e.g., after escalation check). Remove early fast-path or make it delegate to same helper. Add problem-agnostic guard: only fast-path for PB-12 when `state["problem_id"]=="pb-12-itt"`; otherwise always call LLM.

#### MD-07 — `risk_score` semantics undocumented and boosted inconsistently vs charter confidence trajectory
- **File:** `app/agent/confidence.py:135-154` (`compute_risk_score`), `app/agent/monitor.py:85-87`, `app/agent/trace.py:36-48`
- **Category:** quality
- **Description:** Charter expects trace confidence `0.95 → 0.78 → 0.90` across happy → deviation → recovery. `compute_risk_score` is `1 - confidence + 0.15*escalation_count + 0.1 if deviation_log` (lines 141-154). Monitor sets `state["confidence"]=0.78` and `state["escalation"]={"trigger":"feeder_berth_conflict"}` simultaneously, so `risk = 0.22 + 0.15 + 0.1 = 0.47`, but `monitor.py:174` hardcodes `risk_score: 0.78` in `deviation_detected` trace entry (not computed). `handler.py:98` sets `state["confidence"]=0.90` on HITL-5 approve, clearing deviation, so risk returns to `0.10`. Charter trajectory is reproduced via hardcoded assignments, not derived — `risk_score` appears in trace but is not used for any gate decision (escalation uses `confidence`, not risk). Hardcoding makes the observable metric brittle if confidence is tuned.
- **Fix:** Derive `risk_score` uniformly everywhere (remove `0.78` literal in `monitor.py:174` and use `compute_risk_score(state)`). Document formula in `PLAN.md` success criteria 6 and add trace assertion: `assert 0.4 <= risk_after_deviation <= 0.5`.

---

### Low

#### LO-01 — `validate_webhook_event` in resilience.py never wired; dead code
- **File:** `app/agent/resilience.py:129-141`, `app/main.py:72-73`
- **Category:** quality
- **Description:** Helper `validate_webhook_event(data)->(bool,str)` checks `container_count >=50`/`vessel_id`/`tuas_vessel_departure` presence but duplicates Pydantic validation and is never called by `receive_webhook` or `run_demo`. Tests may import it directly, giving false coverage. Remove or wire as in HI-03.
- **Fix:** Either delete and rely on Pydantic, or call it as pre-check for dict payloads in `/agent/run-demo`.

#### LO-02 — Broad `except Exception: pass` hides real failures (30+ sites)
- **File:** `app/agent/nodes.py:79-80,95-96,138-139,427-428`, `app/agent/monitor.py:28-29,224-230`, `app/agent/validation.py:183-195`, `app/shared/logging.py:54` etc.
- **Category:** quality
- **Description:** Found 50+ `except Exception: pass`/`continue` without logging (see grep: `except Exception` on nodes). Examples: `deterministic_score` timestamp parse (confidence.py:80), SSE publish (nodes.py:95), provider creation (nodes.py:126). Real misconfiguration (e.g., `yaml.YAMLError` in `load_problem_config`, `KeyError` in `registry`) is silently swallowed, falling back to stub/mock and making debugging hard — same anti-pattern flagged as H3 in Phase 5 review and now replicated.
- **Fix:** At minimum `warnings.warn` or `structured_log(..., level="warning", exception=...)` in each except. Reserve bare `pass` for truly expected `RuntimeError: no running loop` only.

#### LO-03 — `SYSTEM_PROMPT` eager load at import hides config errors + logging `ensure_ascii=True` vs fallback mismatch
- **File:** `app/agent/prompts.py:105-111`, `app/shared/logging.py:40-49`
- **Category:** quality
- **Description:** Module-level `try: load_problem_config("pb-12-itt"); SYSTEM_PROMPT = build... except: SYSTEM_PROMPT="..."` runs on import; if YAML is corrupt the error is swallowed and the fallback prompt contains no system/tool list, so `_MockProvider` still works but real problems silently degrade. `structured_log` uses `ensure_ascii=True` for stdout but `ensure_ascii` absent for file append (line 65 `json.dumps(entry, default=str)`), so log file may contain raw `→` that Windows `cp1252` cannot encode on replay. Minor.
- **Fix:** Remove eager `SYSTEM_PROMPT`; make `build_system_prompt` the only entry point and call lazily in `build_agent_messages`. Normalise file append to also `ensure_ascii=True` or use `encoding="utf-8"` open.

#### LO-04 — `graph.py` singleton checkpointer leaks `run_id` state indefinitely; `buffers` unbounded for abandoned runs
- **File:** `app/agent/graph.py:59-60` (`_checkpointer = MemorySaver()`), `app/agent/sse.py:45-96`, `app/main.py:68-69` (`MAX_RUNS=100`)
- **Category:** quality
- **Description:** `MemorySaver` and `SSEBroadcaster` hold per-`run_id` state forever until `reset_graph()`/`clear()`. `MAX_RUNS` evicts from `runs` dict but not from `MemorySaver` or `SSEBroadcaster.buffers`/`queues`. Long-running demo server will accumulate checkpoint graphs (each state ~50 KB × messages+trace) without TTL. Not a demo-blocker but will OOM over days. Also `reset_graph()` creates new `MemorySaver()` but old one is not GC'd until all threads release.
- **Fix:** Add TTL eviction (e.g., 30 min LRU) for both stores; clear checkpoint on `/agent/reset/{run_id}` via `graph.get_state` delete emulation or document restart requirement. Add periodic sweep in `run_agent` after `MAX_RUNS` eviction.

---

## Positive Observations

- **HITL `interrupt`/`Command` pattern correct:** single `hitl_node` per Plan §6.5, publishes `hitl_card` via singleton broadcaster then `decision = interrupt(payload)` (gates.py:161), resumes via `graph.ainvoke(Command(resume=decision), config={"configurable":{"thread_id": run_id}})` in `run.py:224` and `main.py:212`. `thread_id == run_id` consistently (run.py:133).
- **Singleton `MemorySaver` reuse keeps checkpoint persistence** — `build_graph()` caches `MemorySaver` and compiled graph (graph.py:60-68, 98-102), `reset_graph()` for tests is explicit. Router separation (pure `route_after_agent`, gating in `agent_node`) avoids checkpoint mutation miss.
- **`fallback_used` flag + distinct `timeout` vs `503` paths + partial-batch continue** implemented with correct metadata (`nodes.py:548-595`) and per-tool trace with `fallback_used` and `risk_score` — success criteria 7 met.
- **SSE broadcaster replay with `Last-Event-ID`** (sse.py:55-77, main.py:260-262) and buffering before `GET /stream` connects — required for demo race fix (U-09).
- **Truncation for checkpoint is at least attempted** (nodes.py:616-624, 689-697) and per-tool `log_trace` capping, preventing the reported 40 s deepcopy in load tests.
- **Hallucinated-tool handling is robust:** validates `registry.get_tool(name) is None`, appends `hallucinated_tool` trace, publishes SSE `tool_call error:hallucinated`, and injects retry message with `Available tools: registry.list()` (nodes.py:303-340) — matches PLAN §6.3 invalid_calls handling.
- **Structured logging per G-23:** `structured_log(event_type, run_id, step, **payload)` emits `timestamp, run_id, step, event_type, payload` JSON lines to stdout + optional `LOG_FILE` (shared/logging.py:15-39), used in every node (`structured_log("trace"|"escalation"|"tool_result"|"hitl_card"|...)`).
- **Problem-switcher consumer ownership preserved:** `app/agent/problem_switcher.py` is narrow consumer of `registry` (Phase 5 pattern kept), `app/main.py:449-477` lazily merges `registry.list()` + YAML tools via `dict.fromkeys()` and filters `event_trigger`.

## Verification Against PLAN.md

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Graph defined with all nodes + edges (including monitor + resilience) | ✅ `graph.py:70-95` |
| 2 | Agent reasons via LLM (rate-limit retry + fallback), selects tools | ✅ `nodes.py:196-212` `resilience.py:12-83`, mock fallback for tests |
| 3 | All 5 HITL gates pause via `interrupt()`/`Command(resume=)` with `thread_id`; stale resume rejected | ⚠️ Pauses ✅, stale normalize missing (HI-02/HI-06), modify fails (CR-01) |
| 4 | All 7 escalation triggers detect thresholds; `risk_score` in every TraceEntry | ⚠️ Triggers present but #3/#5 suppressed vs charter (HI-01); risk hardcoded (MD-07) |
| 5 | Confidence + `risk_score` propagated; threshold 0.85 | ✅ `nodes.py:246-260,388-390` `confidence.py:135-154` `trace.py:36-48` |
| 6 | Trace (with `risk_score`, `fallback_used`, `hallucinated_tool`) + `deviation_log` + structured logging | ✅ but truncation poisons (CR-02/MD-02), SSE not durable (MD-04) |
| 7 | E2E: webhook (422) → agent → tools (timeout vs 503 distinct, partial) → HITL → monitor → deviation → re-plan → result | ⚠️ Webhook future-departure not 422 (HI-03), MODIFY re-plan fails (CR-01) |
| 8 | Monitoring loop (inject → re-query T3 → detect → re-compute → HITL-5 → delta) | ✅ `monitor.py:13-259` but global mutation breaks concurrency (HI-04) |
| 9 | Provider observability `latency_ms/usage/raw/finish_reason` logged | ⚠️ Logged only for mock; real provider latency not consistently in trace |
| 10 | LangSmith export failure does not crash | ✅ try/except in `trace.py:53-66` |

## Severity Counts

- Critical 2, High 6, Medium 7, Low 4 — **19 total**
- Must-fix before Phase 7: CR-01, CR-02, HI-01, HI-02, HI-03

## Recommendations

1. **Fix CR-01 first (30 min):** make `hitl_node`/`handle_hitl_response` async, `await registry.call` — then `POST /agent/hitl/respond {gate_id:"HITL-1", decision:"modify", modifications:{road_containers:100}}` actually recomputes and returns new `cost_breakdown`.
2. **Fix CR-02 (45 min):** keep full `candidates` for optimiser/validation, truncate only for checkpoint fields; add regression test with 120 containers + bad weight at index 100.
3. **Align escalation to charter (20 min, HI-01):** remove wave-based bypass, use exact charter thresholds, update fixtures so nominal `available_trucks=50` and `cost` not tripping, document incremental vs total.
4. **Harden stale resume (15 min, HI-02/HI-06):** normalize gate ids, add TTL check, single source of truth in checkpoint.
5. **Wire webhook 422 (10 min, HI-03):** add `field_validator` for `tuas_vessel_departure` future and call `validate_webhook_event`.
6. **Per-run overrides for concurrency (30 min, HI-04):** implement `_overrides[run_id]` in `app/mocks/data.py` and forward `_run_id` via `inject_edge_case`.
7. **De-duplicate HITL gating and fix `messages` reducer pattern (30 min, HI-05/MD-06).**

---
*Generated by deep review against PLAN.md, REQUIREMENTS.md A-01..A-23, prior phase 05-REVIEW style, charter thresholds, import graphs, and cross-file call chains.*
