# Phase 07.1: Integrated Verification — System-Level E2E, Resilience, and Cross-Problem Regression

## Goal
Prove the entire PSA Nexus platform works as one system before deploy. Aggregate every seam (webhook → agent → tools → HITL → monitor → SSE → problem-switch) into a single local gate that catches integration failures cheaply — before Docker, deck, and video burn time.

## Depends on
Phase 7 (Web UI complete). Transitively requires Phase 4 (foundation + platform), Phase 5 (tools + notification + robustness stubs), Phase 6 (agent core + monitor + resilience). Must run locally via `TestClient` + real SSE broadcaster, not only mocked unit tests.

## Requirements
Covers no new customer requirements — verifies existing F/T/A/U/D requirements in integrated context. Traceable to:
- F-01..F-13 (foundation + platform switch)
- T-01..T-18 (all tools + notification)
- A-01..A-23 (agent core, HITL, escalation, confidence, trace — must be exercised together)
- U-01..U-12 (UI + SSE + HITL cards)
- D-05 (pre-deploy verification completeness, CodeSprint 5.3 robustness)

## Success Criteria
1. Full 17-step happy + deviation E2E passes via HTTP (`POST /webhook/itt-coordination` → HITL resume via `POST /agent/hitl/respond` with `thread_id`) with real SSE stream — not mocked agent_node alone
2. All 5 HITL gates verified for approve/reject/modify/timeout/stale (per-gate timeout_action + 30-min halt)
3. Resilience matrix green: LLM 429→retry→fallback, tool 503/timeout→fallback, partial batch continues, hallucinated tool→error ToolResult, concurrent runs isolated, webhook 422 on bad input
4. Robustness S1–S4 (nominal / incomplete / 503 / safety) re-run in integrated context — not just isolated tool tests
5. Cross-problem regression: PB-12 ↔ PB-01 switch changes tool set, prompt, SSE, and mock data — both E2Es pass sequentially
6. Trace completeness: every `TraceEntry` has `risk_score`, all 10 SSE event types observed, `deviation_log` populated on deviation, structured JSON logs emitted, cost/ROI `$10.4K` + `$8K/incident` correct
7. Single command `pytest app/tests/integration/ -v` is the gate — `Phase 8` deploy blocked until it is green

## Architecture

```
                pytest app/tests/integration/  (gate)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   TestClient (FastAPI)  SSE stream   provider (mocked + real smoke)
        │                  │                  │
        └─────────┬────────┴────────┬─────────┘
                  ▼                 ▼
           POST /webhook/itt-coordination ──► run_agent(event, broadcaster)
                  │                              │
                  │ thread_id=run_id ────────────┤
                  │                              ▼
                  │                     LangGraph (agent→tools→hitl→monitor)
                  │                              │
                  │ SSE: thinking/tool/hitl/    tool registry (TOOLSETS per problem)
                  │ trace/deviation/notification │
                  │                              │
           POST /agent/hitl/respond  ◄──── interrupt({card}) + Command(resume=)
                  │
           POST /agent/inject-edge-case (mutates app/mocks/data.py → monitor re-query sees it)
           POST /agent/switch-problem/{id} (swaps YAML + TOOLSETS + prompt)
```

## Plan

### 07.1.1: Integration Harness & Fixtures
**Duration:** ~1 hour
**What:** Single reusable harness so every integration test talks to the real FastAPI app, not isolated functions.
**Depends on:** 07-web-ui (needs `app/main.py` + `app/agent/sse.py` + `app/agent/graph.py` compiled)
**Steps:**
1. Create `app/tests/integration/__init__.py` + `app/tests/integration/conftest.py`:
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from app.main import app
   from app.mocks.data import reset_mocks
   from app.agent.sse import broadcaster

   @pytest.fixture
   def client():
       with TestClient(app) as c:
           yield c

   @pytest.fixture(autouse=True)
   def clean_mocks():
       reset_mocks()  # clear edge-case injections between tests
       yield
       reset_mocks()
       # cleanup broadcaster buffers
       for run_id in list(broadcaster.buffers.keys()):
           broadcaster.cleanup(run_id)

   @pytest.fixture
   def charter_event():
       return {
           "event_type": "ITT_COORDINATION_REQUEST",
           "timestamp": "2026-08-19T10:30:00+08:00",
           "source": "CITOS_PPT",
           "priority": "high",
           "origin_terminal": "PPT",
           "destination_terminal": "TUAS",
           "vessel_id": "MV PACIFIC STAR",
           "tuas_vessel_departure": "2026-08-19T20:00:00+08:00",
           "container_count": 120,
           "containers_ready": 120,
           "blocks_affected": ["B-07","B-08","B-12","B-14"],
           "dg_containers": 3,
           "priority_containers": 45,
           "requested_by": "PPT_Yard_Planner_Lim",
           "notes": "Priority transhipment",
       }

   @pytest.fixture
   def mock_llm(monkeypatch):
       # deterministic tool-calling sequence: T1→T2→T3→T4→HITL-1→... for offline CI
       # real LLM smoke is a separate marked test (requires API key)
       ...
   ```
2. Create `app/tests/integration/helpers.py`:
   - `start_run(client, event) -> run_id` (POST /webhook)
   - `get_stream_events(client, run_id) -> list[dict]` (GET /agent/stream/{run_id} with timeout — use `httpx` async streaming for SSE; `TestClient` for webhook/HITL sync calls)
   - `hitl_respond(client, run_id, gate_id, decision, modifications=None) -> response`
   - `inject_edge(client, run_id, type)` + `switch_problem(client, id)`
   - `assert_trace_has(trace, node, action)` + `assert_sse_seen(events, event_type)`
   - `collect_trace(client, run_id) -> trace` (GET /runs/{run_id} or from HITL response)
3. Verify harness isolates runs: two concurrent `start_run` produce distinct `run_id` and independent `broadcaster.buffers[run_id]`.

**Verification:**
```bash
pytest app/tests/integration/test_harness.py -v  # 2 runs don't leak mocks or SSE
```

### 07.1.2: Full E2E — 17-Step Happy + Deviation via HTTP + SSE
**Duration:** ~1.5 hours
**What:** The charter 17-step workflow exercised through real HTTP endpoints and real SSE — not `run_agent()` mocked in isolation.
**Depends on:** 07.1.1, 6.11 (unit E2E exists but bypasses webhook/SSE/thread_id)
**Steps:**
1. Create `app/tests/integration/test_e2e_system.py`:
   - **Happy path (10 steps):** `POST /webhook` → SSE `thinking`/`tool_call` → `T1 get_itt_candidates` (120 containers) → `T2 road` → `T3 sea` → `T4 compute_itt_split` → assert `total_transport_cost == 10400` (60×150+40×35) and `cost_vs_baseline.savings == 1600` → `HITL-1` (30 min) approve → `HITL-2` (15 min) approve → `dispatch_road_itt` + `request_feeder_hold` → `T5 update_tuas_loading` → `HITL-4` (10 min) approve → `completed`. Verify: `deviation_log == []`, confidence `~0.95`, 5 gates fired with correct `timeout_action` per gate.
   - **Deviation path (7 more):** After dispatch, `POST /agent/inject-edge-case {type: feeder_conflict}` mutates `app/mocks/data.py` → `monitor_node` re-queries `T3` → detects `berth_status: conflict`, logs `deviation_log[0].type == feeder_berth_conflict`, drops confidence `0.78` → fires escalation #1 (`<0.85`) + #2 (`>1.5h`) → re-computes `T4` `80/40→100/20` → `HITL-5` emergency card → approve → delta dispatch `+4 trucks` → second `T5` → `completed`. Verify: second `T5` has updated ETAs, `deviation_log` non-empty, confidence recovers `~0.90`, SSE saw `deviation` + `escalation` events.
2. SSE assertions: before any `hitl_respond`, open `GET /agent/stream/{run_id}` and assert buffered replay works — events emitted before SSE connect are replayed (race fix from 7.1). Assert all 10 event types appear (U-02's 8 core + notification + heartbeat): `thinking, tool_call, tool_result, hitl_card, escalation, trace_entry, confidence_update, deviation, notification, heartbeat` — buffered replay already covered.
3. Webhook validation: `POST /webhook` with `container_count: 10` → `422`, `container_count: 60` but `tuas_vessel_departure: past` → `422`, `weight_kg: 99999` → guardrail rejects — all without reaching agent.

**Verification:**
```bash
pytest app/tests/integration/test_e2e_system.py -v  # both paths green
pytest app/tests/integration/test_e2e_system.py -k deviation -v
```

### 07.1.3: HITL Lifecycle Matrix (5 Gates × 5 Outcomes)
**Duration:** ~1 hour
**What:** Every HITL gate must handle all 5 outcomes correctly with real `interrupt()` + `Command(resume=)` + `thread_id`. Unit test `test_hitl.py` mocks handler — this tests via HTTP.
**Depends on:** 07.1.1, 6.5 (HITL gates implemented)
**Steps:**
1. Create `app/tests/integration/test_hitl_matrix.py` — parametrized:
   ```python
   @pytest.mark.parametrize("gate", ["HITL-1","HITL-2","HITL-3","HITL-4","HITL-5"])
   @pytest.mark.parametrize("outcome", ["approve","reject","modify","timeout","stale"])
   def test_hitl_outcome(client, charter_event, gate, outcome): ...
   ```
   - **approve:** `POST /agent/hitl/respond {decision: approve}` → `hitl_pending` cleared, trace `hitl:approve`, next gate or `completed`.
   - **reject:** with `reason` → `alternatives[]` presented or `HITL-5` escalation if none — verify `hitl_history` + trace `hitl:reject` + no `dispatched` set.
   - **modify:** send `modifications: {road_containers: 100, sea_containers: 20}` → validate LTA/feeder/timeline, re-run `T4`, new card with updated `cost_breakdown: $11,200` re-presented at same gate — verify second `hitl_card` has new cost.
   - **timeout:** invoke `handle_hitl_response` timeout path per gate: `HITL-1→escalate`, `HITL-2→cancel_dispatch`, `HITL-3→escalate`, `HITL-4→hold_sequence`, `HITL-5→halt` — verify `status` in `("escalated","cancelled","holding","halted")` and second-level 30-min halt if `HITL-5` also times out.
   - **stale:** after timeout sets `status: halted`, send late `POST /agent/hitl/respond` → expect `422 {error: stale, status: halted}` — not silent accept.
2. Also test `Last-Event-ID` SSE replay: disconnect mid-run, reconnect `GET /agent/stream/{run_id}` with `Last-Event-ID` → buffered events replayed via `sse.py` deque.

**Verification:**
```bash
pytest app/tests/integration/test_hitl_matrix.py -v  # 25 cases
```

### 07.1.4: Resilience & Fault Injection (Chaos Matrix)
**Duration:** ~1.5 hours
**What:** Competition will probe failures — this runs the chaos suite in integrated context against real registry/broadcaster, not mocked `tool_node` alone.
**Depends on:** 07.1.1, 6.12 (resilience.py), 5.1 (fallbacks registered)
**Steps:**
1. Create `app/tests/integration/test_resilience_system.py`:
   - **LLM 429 retry→fallback:** monkeypatch first `provider.chat` to raise `RateLimitError(429)` twice → assert `chat_with_rate_limit` retries 2× (exponential backoff) then falls back to `fallback_provider` (from `ProblemConfig.llm.fallback`) → trace has `rate_limited` + `fallback_used`, run still completes.
   - **Tool 503 vs timeout distinct:** mock `check_road_itt_capacity` to raise `503`, `get_itt_candidates` to `TimeoutError` → assert `tool_error_fallback` vs `tool_timeout_fallback` distinct trace entries, both show `fallback_used: true` when `FALLBACKS[cached_*]` exists, `false` when no fallback.
   - **Partial batch:** invoke `tool_node` with 3 `pending_tool_calls` where middle fails → assert batch continues, 2 results + 1 error in `tool_results`, no abort, SSE has 2 `tool_result` + 1 error entry.
   - **Hallucinated tool:** LLM returns `fake_tool_xyz` → `agent_node` filters, logs `hallucinated_tool` trace, returns `ToolResult(error: unknown tool)` without crash, prompts retry with `Available tools: [...]`.
   - **Webhook validation:** invalid `ITTCoordinationEvent` (count<50, past departure, blocks>4500) → `POST /webhook` returns `422` (Pydantic), never creates `run_id`.
   - **Concurrency isolation:** fire 3 `POST /webhook` concurrently (via `asyncio.gather` + `httpx.AsyncClient`) with different `vessel_id` → assert 3 distinct `run_id`/`thread_id`, per-run `broadcaster.buffers` isolated, `GET /runs/{run_id}` returns correct `problem_config` per run, SSE for run A never receives events for run B.
   - **Edge injection per-run isolation:** inject `feeder_conflict` on run A → assert run B's next `T3` still sees `berth_status: available` (per-run mock isolation via `reset_mocks` + `run_id`-scoped mutation if implemented).

**Verification:**
```bash
pytest app/tests/integration/test_resilience_system.py -v
pytest app/tests/integration/test_resilience_system.py -k "concurrency or 429" -v
```

### 07.1.5: Robustness Scenarios (S1–S4) — Integrated Re-Run
**Duration:** ~1 hour
**What:** Re-exercise CodeSprint 5.3 robustness scenarios that were stubbed in `5.13` (S1–S3 mocked, S4 skipped before HITL-5) now against the full stack.
**Depends on:** 07.1.1, 5.13 (stubs exist), 6.5/6.6 (HITL-5 + triggers)
**Steps:**
1. Create `app/tests/integration/test_robustness_system.py` — 4 scenarios via harness (not isolated tool mocks):
   - **S1 Nominal:** charter event + all mocks healthy → auto-approve `HITL-1..4` → `completed`, cost `$10.4K`, trace clean.
   - **S2 Incomplete:** `containers[0].weight_kg = None` (missing) → guardrail fires at webhook bootstrap → agent queries secondary or asks via HITL `weight unknown, verify?` → resolves with operator input → completes — trace shows `guardrail_failed: weight_bounds`.
   - **S3 API Failure:** `GET /api/optetruck/capacity` returns `503` → `tool_node` logs `tool_error`, retries/`fallback_used: true` via `cached_road_capacity`, notifies via `notify_parties` → SSE `notification` + `fallback_used` in trace.
   - **S4 Safety Escalation:** `T4` output triggers `cost > $10K` (Trigger #3) or `tuas_vessel_departure` shifts `+2.5h` → agent halts, emits `HITL-5 {gate_id, approval_card, escalation: cost_exceeded}` → verify `hitl_pending.gate_id == HITL-5`, `status: escalated`, not auto-dispatched.
2. Each scenario asserts: correct `notification` (where applicable) to `parties: [PPT_Yard, Tuas_Yard, Feeder_Operator]`, correct SSE types, correct `confidence` drop on S2/S4.

**Verification:**
```bash
pytest app/tests/integration/test_robustness_system.py -v  # all 4 pass post-Phase 6
```

### 07.1.6: Cross-Problem Regression (PB-12 ↔ PB-01)
**Duration:** ~1 hour
**What:** Nexus is a platform — prove switching doesn't leak tools, prompts, or mock state. `4.8`/`5.11` stubbed PB-01 tools, but never ran E2E back-to-back.
**Depends on:** 07.1.1, 4.8 (switcher), 5.11 (PB-01 stubs)
**Steps:**
1. Create `app/tests/integration/test_switch_regression.py`:
   - `POST /agent/switch-problem/pb-01-berth` → assert `registry.list()` now has `query_vessel_arrival, check_berth_availability, check_qc_availability, compute_berth_reassignment, notify_vessel_operator` and NOT `get_itt_candidates`; `GET /agent/switch-problem/pb-12-itt` → tool set flips back; `build_system_prompt` contains correct `Problem: Berth Delay` vs `ITT Coordination`.
   - Run full `PB-12` E2E (via 07.1.2 helper) → `completed`.
   - Switch to `PB-01` → run minimal `PB-01` E2E (VTIS→OptEVoyage→CITOS berth, 2 HITL gates) → `completed` → assert `tool_results` keys are PB-01 tools.
   - Switch back to `PB-12` → re-run `PB-12` E2E → completes again — proves no `registry` leak.
   - Mock isolation: after `PB-12` `inject_feeder_conflict`, switch to `PB-01` → assert `VTIS` berth data still `available` (no cross-problem mock mutation).
   - SSE: open `GET /agent/stream/{pb12_run_id}` and `GET /agent/stream/{pb01_run_id}` concurrently → each stream only sees its run's events.

**Verification:**
```bash
pytest app/tests/integration/test_switch_regression.py -v
```

### 07.1.7: Trace, Streaming & Observability Audit
**Duration:** ~45 min
**What:** Audit that observability is complete — the judge scores trace, guardrails, and cost/ROI.
**Depends on:** 07.1.1..07.1.6 (needs runs to audit)
**Steps:**
1. Create `app/tests/integration/test_observability_audit.py`:
   - After any E2E run, fetch `export_trace(run_id)` → assert every `TraceEntry` has `risk_score` (CodeSprint 4.3), `timestamp`, `duration_ms`, `confidence`; `risk_score = 1 - confidence + 0.15*escalations` formula holds.
   - Assert `structured_log` JSON lines emitted to stdout/file for each `trace`, `hitl`, `deviation`, `fallback`, `hallucinated_tool` — at least `total_steps` lines.
   - Assert `deviation_log` appended only on deviation path (empty on happy, `len==1` on feeder conflict, entry has `previous_window`/`current_window`/`impact`).
   - Assert SSE `notification` events appear when `notify_parties` called (monitor deviation + escalation), panel data `{parties, message, timestamp}` correct.
   - If `LANGSMITH_API_KEY` set, assert LangSmith trace exported (A-19) — else structured JSON trace present.
   - Capture latency: wall time (`<30s` happy, `<90s` with deviation) + SSE p50/p95 via helper timestamps — satisfies D-08 early.
   - Assert cost math: `T4 total_transport_cost == 10400`, `cost_vs_baseline: {baseline:12000, optimised:10400, savings:1600}`, `roi.per_incident == 8000`, `roi.annual in [384000, 576000]` — from YAML `cost_params`.
   - Assert validation guardrails: after webhook bootstrap, `validation.py` `GUARDRAILS` (6 checks: weight 0-60000, block ≤4500, trucks≥1, feeder capacity, vessel margin 60 min, tidal window) all green on nominal, exactly one fails on each injected bad input.
2. Output `integration_coverage.md`: table of `Phase 5.13 S1-4 + HITL 5×5 + resilience 7 + switch 2` → all green.

**Verification:**
```bash
pytest app/tests/integration/test_observability_audit.py -v
pytest app/tests/integration/ -v --tb=short  # full suite gate
```

### 07.1.8: Pre-Deploy Gate (Go/No-Go)
**Duration:** ~30 min
**What:** The gate for Phase 8 — nothing deploys until this is green. Generates the artifact that 8.4 smoke test will re-validate remotely.
**Depends on:** 07.1.1..07.1.7 (all must pass)
**Steps:**
1. Add `app/tests/integration/test_gate.py` (or `make verify`):
   - Runs `pytest app/tests/integration/ -v --junitxml=reports/integration.xml` and asserts `exit_code == 0`.
   - Runs `docker build -t psa-agent .` + `docker run -p 8000:8000` smoke (fast) → `GET /health` + `POST /webhook` + SSE smoke — proves Phase 8.1/8.2 will work (optional local Docker, not required in CI).
   - Writes `reports/predeploy_gate.md`: `PASS/FAIL` per sub-phase, wall time, blocking issues.
2. Update `.planning/STATE.md` Accum Context: `Phase 07.1 gate: PASS — integrated verification complete, ready for deploy`.
3. Blocker rule: if any `07.1.x` fails, `ROADMAP.md` Phase 8 `Depends on: 07.1` prevents proceeding — fix in place, don't skip.

**Verification:**
```bash
pytest app/tests/integration/ -v
cat reports/predeploy_gate.md  # all PASS
```

## Verification Loop
After all 8 sub-phases:
1. `pytest app/tests/integration/ -v` — all 8 test modules green (harness, e2e, hitl matrix, resilience, robustness, switch, observability, gate)
2. `pytest app/tests/ -v` — existing unit tests still green (no regression)
3. `GET /agent/stream/{run_id}` replay: start run → wait 2s → connect SSE → buffered events replayed (race fix verified)
4. `pytest app/tests/ app/tests/integration/ --cov=app --cov-report=term-missing` — coverage report (target ≥80% on `app/agent/` + `app/tools/` + `app/hitl/`)
5. Manual smoke: `POST /webhook` → `GET /stream` → approve gates → see `notification` bell + `trace` sidebar + problem switcher

## Commit
After verification: `git add app/tests/integration/ reports/predeploy_gate.md && git commit -m "Phase 07.1: Integrated verification — system E2E, resilience, HITL matrix, cross-problem regression (INSERTED)"`

## Anti-Patterns
- Don't mock the graph in 07.1 — this is the only phase that must hit real `app/main.py` + real `broadcaster` + real `registry` + real `thread_id` (use mocks only for LLM and mock data)
- Don't bypass SSE — every test must assert SSE events, not just `result["state"]`
- Don't skip the stale-resume and concurrency cases — competition judges probe them
- Don't leave Phase 8 depending on Phase 7 alone — wire `Depends on: 07.1` after this plan lands
