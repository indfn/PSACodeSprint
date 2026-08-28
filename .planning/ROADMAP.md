# Roadmap: PSA Nexus — Agentic Multi-Party Coordination Platform

## Overview

Full pipeline for the PSA Code Sprint: Agentic AI in Action competition. Phases 1–3 mapped PSA Singapore's operations, mined disruptions, and selected the flagship problem. Phases 4–8 build **PSA Nexus** — a generalizable, provider-agnostic agentic platform (Cluster C2, 7 problems) demonstrated via PB-12 cross-terminal ITT, addressing all 23 gaps in the master charter gap inventory + CodeSprint Phase 5 robustness criteria + platform generalisability.

## Timeline

| Phase | Name | Days | Dependencies |
|-------|------|------|-------------|
| 1–3 | Research & Selection | Done | — |
| 4 | Foundation Reformation | 1 day | Phase 3 |
| 5 | Tool Integration | 1–2 days | Phase 4 |
| 6 | Agent Core (LangGraph) | 2–3 days | Phase 5 |
| 7 | Web UI & Integration | 1–2 days | Phase 6 |
| 07.1 | Integrated Verification (INSERTED) | 0.5–1 day | Phase 7 |
| 8 | Polish & Deploy | 1–2 days | 07.1 |

**Critical path:** 4 → 5 → 6 → 7 → 07.1 → 8

---

## Phases

### Phase 1: Broad PSA Singapore Operations & Systems Mapping ✅
**Status:** COMPLETE (2026-08-17)

### Phase 2: Disruption Mining & Problem Bank Creation ✅
**Status:** COMPLETE (2026-08-17)

### Phase 3: Problem Evaluation, Litmus Testing & Final Selection ✅
**Status:** COMPLETE (2026-08-19)

---

### Phase 4: Foundation Reformation
**Goal:** Clean up the fragmented prototype into a unified, working foundation. Directory restructure, deduplication, provider validation, YAML config wiring.
**Depends on:** Phase 3
**Requirements:** F-01 through F-07
**Success Criteria** (what must be TRUE):
  1. Unified FastAPI app starts on port 8000 with `/health`, `/agent/*`, `/mocks/*`, `/ui/*`
  2. Directory restructured: `app/agent/`, `app/tools/`, `app/mocks/`, `app/hitl/`, `app/ui/`, `app/shared/`, `app/configs/`
  3. provider.py tested end-to-end with real API key
  4. pb-12-itt.yaml loads correctly into ProblemConfig dataclass
  5. Duplicate files consolidated (two webhooks → one, two schema sets → one)
  6. `pytest app/tests/` passes (config loading, provider creation, health endpoint)
**Status:** ✅ COMPLETE (2026-08-27) — commit 0416b67, 04-REVIEW-FIX 6 fixes, 57 tests pass

#### Sub-phases

##### 4.1: Directory Restructure
**What:** Create `app/` directory structure, move/salvage code from `prototype/`
**Duration:** ~2 hours
**Deliverables:**
- `app/__init__.py`
- `app/main.py` — unified FastAPI app
- `app/agent/` — LangGraph agent (Phase 6 fills this)
- `app/tools/` — tool implementations (Phase 5 fills this)
- `app/mocks/` — mock servers (consolidated from prototype/mocks/ + pre_approval/)
- `app/hitl/` — HITL gates (Phase 6 fills this)
- `app/ui/` — web frontend (Phase 7 fills this)
- `app/shared/` — provider.py, yaml_reader.py, shared models
- `app/configs/` — pb-12-itt.yaml and other YAML configs
- `app/tests/` — test suite
**Depends on:** Nothing
**Verification:** `ls -la app/` shows all directories; `python -c "from app.main import app"` succeeds

##### 4.2: Consolidate Mock Servers
**What:** Merge the two parallel mock implementations into one canonical set.
**Duration:** ~3 hours
**Deliverables:**
- `app/shared/models.py` — single canonical Pydantic schema set (merged from mocks/schemas.py + pre_approval/*/models.py — NOT `app/mocks/schemas.py`)
- `app/mocks/data.py` — mock data (from prototype/mocks/data.py)
- `app/mocks/routers/citos_ppt.py` — PPT CITOS endpoints
- `app/mocks/routers/citos_tuas.py` — Tuas CITOS endpoints
- `app/mocks/routers/optetruck.py` — OptETruck endpoints
- `app/mocks/routers/feeder.py` — Feeder endpoints
- `app/mocks/routers/portnet.py` — PORTNET endpoints
- Webhook: scaffold `POST /webhook/itt-coordination` in `app/main.py` (validates `ITTCoordinationEvent`, bootstraps 11-field initial_state; full wiring in Phase 6.9) — NOT in `app/mocks/`
- `app/mocks/edge_cases.py` — edge case simulation (from prototype/mocks/edge_cases.py)
- `app/shared/tool_adapter.py` — provider ↔ tool schema adapter covering all 8 names / 4 families (anthropic, gemini, openai-compatible×5) (for Phase 4.3)
- Delete: prototype/pre_approval/ppt_citos/, prototype/pre_approval/sea_itt/app.py+router.py+models.py, prototype/pre_approval/container_readiness/webhook.py
**Depends on:** 4.1
**Verification:** All mock endpoints respond + `python -c "from app.shared.models import ITTCoordinationEvent; print('OK')"`

##### 4.3: Validate provider.py + Tool-Calling Adapter
**What:** Test provider.py end-to-end for all 8 provider names. Build adapter so any provider family can call tools.
**Duration:** ~1.5 hours
**Deliverables:**
- `app/shared/provider.py` — 8 providers: anthropic, openai, gemini, deepseek, ollama, vllm, lmstudio, custom (any `base_url` — OpenRouter, Together, Groq, local)
- `app/shared/yaml_reader.py` — yaml_reader.py moved
- `app/shared/tool_adapter.py` — 4 families: OpenAI-compatible (openai/deepseek/ollama/vllm/lmstudio/custom = direct), Anthropic (`input_schema`), Gemini (`functionDeclarations`)
- Test script or pytest that creates a provider, calls chat() with tool schemas, verifies tool_calls in response
- Documented: which providers work, which have issues
**Depends on:** 4.1
**Verification:** `python -c "from app.shared.provider import create_provider; p = create_provider({'provider': 'anthropic', 'model': 'claude-sonnet-4-20250514', 'api_key': '...'}); print(p.chat('Say hello'))"` returns a response

##### 4.4: Validate YAML Config System
**What:** Load pb-12-itt.yaml, verify all fields parse correctly. Wire config into ProblemConfig dataclass.
**Duration:** ~2 hours
**Deliverables:**
- `app/configs/pb-12-itt.yaml` — flagship config (from prototype/configs/)
- `app/configs/problem_config.py` — ProblemConfig dataclass that loads from YAML
- Test: load config, verify systems, tools, HITL gates, escalation triggers, constraints, LLM settings
**Depends on:** 4.1
**Verification:** `python -c "from app.configs.problem_config import load_problem_config; c = load_problem_config('pb-12-itt'); print(c.tools)"` returns 6 tools

##### 4.5: Consolidate Schemas (Second Pass — Extend & Verify)
**What:** Second pass on `app/shared/models.py` — extend with Phase 6 placeholder models. Depends on 4.2.
**Duration:** ~1 hour
**Deliverables:**
- Verify `app/shared/models.py` (created in 4.2) — no separate `app/mocks/schemas.py`
- Add placeholder models for Phase 6: `AgentState` (TypedDict stub), `HITLGate`, `HITLDecision`, `TraceEntry` (TYPE_CHECKING guarded)
- Remove duplicate definitions from mocks/ and pre_approval/
**Depends on:** 4.2
**Verification:** `python -c "from app.shared.models import ITTCoordinationEvent, ITTSplitResponse, SeaITTCapacityResponse"` succeeds

##### 4.6: Base Tests
**What:** Write foundational tests: config loading, provider creation + adapter, health endpoint, schema validation.
**Duration:** ~2 hours
**Deliverables:**
- `app/tests/test_config.py` — test YAML config loading (all 7 problems)
- `app/tests/test_provider.py` — test provider creation (mocked) + tool adapter
- `app/tests/test_health.py` — test health endpoint
- `app/tests/test_schemas.py` — test schema serialization
**Depends on:** 4.2, 4.3, 4.4, 4.5
**Verification:** `pytest app/tests/ -v` — all tests pass

##### 4.7: Complete Sibling YAML Configs
**What:** Fill in the 6 incomplete sibling configs so all 7 C2 problems are fully specified.
**Duration:** ~2 hours
**Deliverables:**
- `app/configs/pb-01-berth.yaml` — add: 7 escalation triggers, confidence, cost params (berth/demurrage/QC), constraints, edge cases (berth conflict, tidal miss)
- `app/configs/pb-02-dtqc.yaml` — add: 7 triggers, confidence, cost params, constraints, edge cases
- `app/configs/pb-04-feeder.yaml` — same
- `app/configs/pb-09-expressway.yaml` — same
- `app/configs/pb-10-sea-air.yaml` — same
- `app/configs/pb-11-customs.yaml` — same
- Each sibling verified: at least 1 HITL gate → 2 gates, all 7 esc triggers, cost_params (10 rows where applicable), edge_cases
**Depends on:** 4.4 (need ProblemConfig schema)
**Verification:** `for id in pb-01 pb-02 pb-04 pb-09 pb-10 pb-11 pb-12; do python -c "from app.configs.problem_config import load_problem_config; c=load_problem_config('$id'); print(f'{id}: {len(c.systems)} systems, {len(c.tools)} tools, {len(c.hitl_gates)} gates')" ; done`

##### 4.8: Problem Switching Mechanism
**What:** Build the runtime switch that makes Nexus a platform, not a single-problem agent.
**Duration:** ~2 hours
**Deliverables:**
- `app/agent/problem_switcher.py` — `switch_problem(problem_id: str) -> ProblemConfig`: loads new YAML, validates, returns config
- `app/main.py` — `POST /agent/switch-problem/{problem_id}`: calls switcher, re-registers tool set via `registry.clear() + registry.register(new_tools)`, updates `AgentState.problem_config`, returns `{problem_id, systems, tools, hitl_gates}`
- `app/tools/registry.py` — add `clear()`, `register_many(tools)`, `get_tool_names()` for dynamic switching
- Prompt templating: `app/agent/prompts.py` builds system prompt from `ProblemConfig` (problem name, sector, systems, tools, cost params) — not hardcoded to PB-12 ITT
**Depends on:** 4.4, 4.7
**Verification:** `curl -X POST localhost:8000/agent/switch-problem/pb-01-berth` → returns PB-01 systems/tools; `curl -X POST localhost:8000/agent/switch-problem/pb-12-itt` → back to PB-12

##### 4.9: Cross-Check + Cost Params Completion
**What:** Verify all 10 cost param rows + platform generalisability wiring.
**Duration:** ~1 hour
**Deliverables:**
- `app/configs/problem_config.py` — `CostParams` dataclass includes all 10 charter rows; validates on load
- `app/tests/test_platform.py` — tests: load all 7 configs, switch PB-12→PB-01→PB-12, verify tool set changes, prompt contains correct problem name, cost params parsed
**Depends on:** 4.7, 4.8
**Verification:** `pytest app/tests/test_platform.py -v`

---

### Phase 5: Tool Integration + Notification + Robustness
**Goal:** Build all PB-12 tools with consistent interface, add notification primitive, stub sibling tools, and verify 4 robustness scenarios.
**Depends on:** Phase 4
**Requirements:** T-01 through T-18
**Success Criteria** (what must be TRUE):
  1. All 6 PB-12 tools + 2 post-approval tools callable via tool registry with JSON schemas
  2. Each tool returns `ToolResult(output, confidence, metadata)`
  3. Tool 4 returns 80 road / 40 sea = $10,400 for PB-12 (60×$150 + 40×$35)
  4. Post-approval tools (dispatch_road_itt, request_feeder_hold) implemented, HITL-gated
  5. Notification tool `notify_parties()` dispatches to stakeholders, visible in SSE + trace
  6. PB-01 sibling tool stubs work with mock data (proves platform generalisability)
  7. Cost/ROI equation computed: $8,000/incident savings verified
  8. 4 robustness scenarios pass: nominal, incomplete data, API 503 failure, safety escalation
  9. Each tool tested against mock server
**Status:** ✅ COMPLETE (2026-08-27) — 127 tests pass, 3 skipped (S4 pending HITL-5), 05-REVIEW 15 issues fixed (C1 YAML drift → charter names, H1 guard `hitl_required`, H2 weight_bounds, 24 stub warnings benign)

#### Sub-phases

##### 5.1: ToolResult Interface & Registry
**What:** Define the standard tool interface and a registry that maps tool names to functions + schemas.
**Duration:** ~1 hour
**Deliverables:**
- `app/tools/__init__.py`
- `app/tools/base.py` — `ToolResult` dataclass, `BaseTool` ABC
- `app/tools/registry.py` — `ToolRegistry` class with `register()`, `call()`, `get_schemas()`
- Test: register a mock tool, call it, verify ToolResult
**Depends on:** Phase 4
**Verification:** `python -c "from app.tools.registry import ToolRegistry; r = ToolRegistry(); print(r.list())"` returns empty list

##### 5.2: Tool 1 — Container Readiness
**What:** Port existing container_readiness logic into new ToolResult interface.
**Duration:** ~1 hour
**Deliverables:**
- `app/tools/container_readiness.py` — Tool 1 implementation
- JSON schema for LLM tool-calling
- Unit test: call with vessel_id, verify container count + breakdown
**Depends on:** 5.1
**Verification:** Tool returns 120 containers (40×40ft + 80×20ft) for PB-12

##### 5.3: Tool 2 — Road ITT Capacity
**What:** Port existing optetruck_tools.py into new ToolResult interface.
**Duration:** ~1 hour
**Deliverables:**
- `app/tools/road_itt.py` — Tool 2 implementation
- JSON schema for LLM tool-calling
- Unit test: call with terminal + time_window, verify truck count + transit time
**Depends on:** 5.1
**Verification:** Tool returns truck availability and transit time for PPT→Tuas route

##### 5.4: Tool 3 — Sea ITT Capacity
**What:** Port existing sea_itt_tools.py into new ToolResult interface.
**Duration:** ~1 hour
**Deliverables:**
- `app/tools/sea_itt.py` — Tool 3 implementation
- JSON schema for LLM tool-calling
- Unit test: call with feeder_id, verify capacity + tidal feasibility
**Depends on:** 5.1
**Verification:** Tool returns feeder capacity and departure window for PB-12

##### 5.5: Tool 4 — Multi-Constraint Optimisation
**What:** Port existing compute_itt_split.py, wire YAML config. Charter: `compute_itt_split(candidates, road_capacity, sea_capacity, tuas_vessel_departure, constraints)` → $10,400.
**Duration:** ~2 hours
**Deliverables:**
- `app/tools/optimiser.py` — Tool 4 as `compute_itt_split` (charter name) with `tuas_vessel_departure` + `constraints` + guardrails
- JSON schema for LLM tool-calling
- Unit test: call with candidates + road/sea capacity + tuas_vessel_departure, verify 80/40 split = $10,400 (60 trips × $150 + 40 × $35 handling)
**Depends on:** 5.1, 4.4
**Verification:** Tool returns optimal split with total_transport_cost $10,400 for PB-12

##### 5.6: Tool 5 — Tuas Loading Sequence
**What:** NEW implementation. Charter: `update_tuas_loading_sequence(cit_tuas_endpoint, vessel_id, itt_eta_road, itt_eta_sea, container_ids_road, container_ids_sea)`.
**Duration:** ~2 hours
**Deliverables:**
- `app/tools/tuas_loading.py` — Tool 5 with explicit `vessel_id + itt_eta_road + itt_eta_sea + container_ids_road + container_ids_sea` per charter
- JSON schema for LLM tool-calling
- Mock endpoint in mocks/routers/citos_tuas.py for testing
- Unit test: call with ETAs + container lists, verify QC adjustments
**Depends on:** 5.1
**Verification:** Tool returns updated loading sequence with QC assignments

##### 5.7: Post-Approval Tools (5.7a + 5.7b)
**What:** NEW implementations for dispatch and feeder hold. Only callable after HITL approval; support delta dispatch.
**Duration:** ~2 hours
**Deliverables:**
- `app/tools/dispatch_road_itt.py` (5.7a) — `dispatch_road_itt(num_trucks, route, container_ids)` — charter route param + delta dispatch support
- `app/tools/request_feeder_hold.py` (5.7b) — `request_feeder_hold(feeder_id, hold_hours)` — operator may decline
- JSON schemas for both + guard: reject if no prior HITL approve in state
- Unit tests
**Depends on:** 5.1
**Verification:** Tools return dispatch/hold confirmation; feeder decline handled; HITL guard enforced

##### 5.8: Edge Case Hooks (NOT LLM Tools)
**What:** Wire edge case simulation as demo injection hooks — mutate mock data layer so next T3 query sees conflict.
**Duration:** ~1 hour
**Deliverables:**
- `app/tools/edge_cases.py` — hooks (not BaseTool): `inject_feeder_berth_conflict()`, `inject_stale_data()` → mutate `app/mocks/data.py`
- Exposed via `POST /agent/inject-edge-case` (Phase 7.4), NOT tool registry
**Depends on:** 5.1
**Verification:** inject → query T3 → conflict visible in berth_status / departure_window

##### 5.9: Integration Test
**What:** Test all PB-12 tools end-to-end against mock server.
**Duration:** ~2 hours
**Deliverables:**
- `app/tests/test_tools.py` — tests for all 6 PB-12 tools + post-approval tools
- Each tool tested against live mock server
**Depends on:** 5.2–5.8
**Verification:** `pytest app/tests/test_tools.py -v` — all tools return valid ToolResult

##### 5.10: Notification Tool (Primitive #5)
**What:** Implement the multi-party notification primitive that was missing.
**Duration:** ~1 hour
**Deliverables:**
- `app/tools/notify.py` — `notify_parties(message: str, parties: list[str]) -> ToolResult`: logs to trace, publishes SSE `notification` event. Mock: stores in `app/mocks/data.py` notification log. Charter primitive #5: Event Ingestion, Reasoning Planner, Orchestrator, HITL Gate, **Notification**, Deviation Logger.
- Mock endpoint: `POST /api/notify` → stores notification
- `app/ui` — notification panel (Phase 7.6 enhancement)
**Depends on:** 5.1
**Verification:** `notify_parties("Feeder delayed", ["PPT_Yard", "Tuas_Yard", "Feeder_Operator"])` → trace entry + SSE event

##### 5.11: Sibling Tool Stubs (PB-01)
**What:** Stub PB-01 tools to prove the platform generalises beyond PB-12.
**Duration:** ~2 hours
**Deliverables:**
- `app/tools/pb01_berth/` — `query_vessel_arrival(vtis)`, `check_berth_availability(optevoyage)`, `check_qc_availability(citos)`, `compute_berth_reassignment()`, `notify_vessel_operator()` — all return mock ToolResults with PB-01-style data (vessel ETA, berth windows, QC counts)
- `app/mocks/routers/vtis.py` + `optevoyage.py` + `berth.py` — mock endpoints for PB-01 systems
- `app/tools/registry.py` — `register_for_problem(problem_id)` loads correct tool set per YAML
**Depends on:** 5.1, 4.8
**Verification:** `switch-problem/pb-01-berth` → registry lists 5 PB-01 tools → call each → valid ToolResult

##### 5.12: Cost/ROI Equation
**What:** Implement the charter §5 cost/ROI math that was missing.
**Duration:** ~1 hour
**Deliverables:**
- `app/tools/optimiser.py` — extend T4 output: `cost_vs_baseline: {baseline_all_road: $12K, optimised: $10.4K, savings: $1.6K}` and `roi: {per_incident: $8000, monthly: $32K-48K, annual: $384K-576K}` computed from YAML cost_params × incident frequency
- `app/tests/test_roi.py` — verify: baseline 80 trips × $150 = $12K, optimised 60 trips × $150 + 40×$35 = $10.4K, savings = $1.6K transport; full incident savings $8K (charter §5 equation)
**Depends on:** 5.5
**Verification:** `pytest app/tests/test_roi.py -v` — all cost assertions pass

##### 5.13: 4 Robustness Scenarios (CodeSprint 5.3)
**What:** Verify the 4 required robustness scenarios per competition brief Phase 5.3.
**Duration:** ~2 hours
**Deliverables:**
- `app/tests/test_robustness.py` — 4 scenarios:
  - **S1 Nominal:** 120 containers, all systems healthy → agent resolves, HITL-1..4 approve, dispatch succeeds
  - **S2 Incomplete Data:** container `weight_kg` missing → guardrail fires → agent queries secondary source or asks operator ("weight unknown, verify?") → resolves
  - **S3 API Failure:** mock returns 503 on T2 → agent detects, logs `tool_error` to trace, retries or uses fallback (cached data / re-query), alerts operator via notification
  - **S4 Safety Escalation:** T4 result triggers Trigger #3 (cost >$10K) or vessel departure shift >2h → agent halts, produces HITL-5 card
- Each scenario: trace shows correct handling, SSE streams events, notification sent where applicable
> S4 (`safety escalation` → HITL-5) requires Phase 6 (6.5/6.6) — mark skipped before Phase 6, runs after.
**Depends on:** 5.2–5.11 (S1–S3 standalone; S4 gated on Phase 6.5+6.6 — skips if not yet built)
**Verification:** `pytest app/tests/test_robustness.py -v` — S1–S3 pass pre-Phase 6, S4 passes after 6.6; `test_robustness.py::TestS4` marked `skipIf no HITL-5`

---

### Phase 6: Agent Core (LangGraph) — PSA Nexus Brain
**Goal:** Build the LangGraph agent graph with tool-calling loop, 5 HITL gates, 7 escalation triggers, confidence scoring, and platform-agnostic prompt templating — the brain of Nexus.
**Depends on:** Phase 5
**Requirements:** A-01 through A-23
**Success Criteria** (what must be TRUE):
  1. LangGraph StateGraph defined with all nodes and edges
  2. Agent reasons via LLM, selects tools, processes results
  3. All 5 HITL gates pause for approval and resume on callback
  4. All 7 escalation triggers detect threshold breaches
  5. Confidence score propagated through state
  6. Execution trace logged at every step
  7. End-to-end: webhook → agent → tools → HITL → result works
 **Status:** ✅ COMPLETE (2026-08-28) — 5 e2e tests green (happy 80/40=$10,400 + deviation 100/20=$11,200 + HITL-5 pending), 4 nodes (agent/tools/hitl/monitor) + MemorySaver(thread_id) + deterministic mock, truncation fix 120→5 containers, e2e time 37-43s isolated

#### Sub-phases

##### 6.1: State Schema Design
**What:** Define the LangGraph state schema that carries all agent state through the graph.
**Duration:** ~1 hour
**Deliverables:**
- `app/agent/state.py` — TypedDict or Pydantic model with:
  - `messages: list[BaseMessage]` — conversation history
  - `tool_results: dict` — results from tool calls
  - `hitl_pending: Optional[HITLGate]` — current HITL gate awaiting approval
  - `hitl_history: list[HITLDecision]` — past HITL decisions
  - `confidence: float` — current confidence score
  - `escalation: Optional[Escalation]` — active escalation
  - `trace: list[TraceEntry]` — execution trace
  - `problem_config: ProblemConfig` — loaded YAML config
  - `run_id: str` — unique run identifier
  - `status: str` — current status (running, waiting_hitl, escalated, completed, failed)
**Depends on:** Phase 5
**Verification:** `python -c "from app.agent.state import AgentState; print(AgentState.__annotations__)"` shows all fields

##### 6.2: System Prompt & Tool Definitions
**What:** Write the system prompt for the agent and define tool schemas for LLM tool-calling.
**Duration:** ~2 hours
**Deliverables:**
- `app/agent/prompts.py` — system prompt that instructs the LLM about:
  - Its role (ITT coordination planner)
  - Available tools and when to use them
  - HITL process (generate approval cards, handle reject/modify)
  - Escalation rules
  - Confidence scoring instructions
  - Output format (structured JSON for tool calls and HITL cards)
- `app/agent/tool_schemas.py` — LLM-compatible tool definitions (OpenAI function-calling format)
**Depends on:** 6.1, Phase 5
**Verification:** Prompt loads, tool schemas are valid JSON Schema

##### 6.3: Agent Node (LLM Reasoning)
**What:** Build the core agent node that sends messages to LLM, processes tool calls, and manages conversation state.
**Duration:** ~3 hours
**Deliverables:**
- `app/agent/nodes.py` — `agent_node(state) -> state` function:
  1. Builds messages from state (system prompt + conversation + context)
  2. Calls LLM with tool schemas
  3. If LLM returns tool calls → dispatch to tool registry
  4. If LLM returns HITL card → set hitl_pending
  5. If LLM returns escalation → set escalation
  6. Updates trace
  7. Returns updated state
- Uses `provider.py` for LLM calls
**Depends on:** 6.1, 6.2, Phase 5
**Verification:** Agent node processes a simple prompt, returns updated state with tool calls

##### 6.4: Tool Execution Node
**What:** Build the node that executes tool calls and returns results to the agent.
**Duration:** ~1 hour
**Deliverables:**
- `app/agent/nodes.py` — `tool_node(state) -> state` function:
  1. Reads tool calls from state
  2. Dispatches to tool registry
  3. Adds tool results to messages
  4. Updates trace
  5. Returns updated state
**Depends on:** 6.1, 6.3, Phase 5
**Verification:** Tool node executes a tool call, returns result in state

##### 6.5: HITL Gate Implementation (Single `hitl` Node with `interrupt()`)
**What:** Implement 5 HITL gates as a single `hitl_node` using correct `interrupt()` + `Command(resume=)` pattern.
**Duration:** ~4 hours
**Deliverables:**
- `app/hitl/models.py` — `HITLGate` (gate_id, gate_name, trigger, approval_card, timeout_seconds, timeout_action), `HITLDecision`, `HITL_GATES` dict with charter timeouts (30/15/15/10/30 min) + timeout_actions (escalate/cancel_dispatch/hold_sequence/halt)
- `app/hitl/gates.py` — single `hitl_node(state) -> Command` using `interrupt({gate_id, approval_card, timeout})` + `build_approval_card()` per charter §4 template
- `app/hitl/handler.py` — `handle_hitl_response()`: REJECT (log + alternatives[] or escalate to HITL-5), MODIFY (validate LTA/feeder/timeline + re-run T4 + re-present), TIMEOUT (per-gate action + second-level 30 min halt), APPROVE (clear pending, continue)
**Depends on:** 6.1, 6.3
**Verification:** Gate generates approval card with correct timeout; `interrupt()` pauses; `Command(resume=)` resumes; REJECT/MODIFY/TIMEOUT all tested

##### 6.6: Escalation Trigger Implementation (Charter Thresholds)
**What:** Implement 7 escalation triggers with exact charter thresholds.
**Duration:** ~3 hours
**Deliverables:**
- `app/agent/escalation.py` — 7 triggers: `low_confidence (<0.85)`, `feeder_hold >1.5h`, `cost >$10k`, `data_age >30m`, `trucks <60%`, `feeder_unresponsive >15m`, `planner_conflict` — called inside `agent_node` after each tool batch; fires → `hitl_pending = HITL-5`
**Depends on:** 6.1, 6.3
**Verification:** Each trigger tested with charter threshold; data_stale + feeder_unresponsive + planner_conflict all fire correctly

##### 6.7: Confidence Scoring
**What:** Implement confidence scoring via LLM self-assessment with deterministic backup.
**Duration:** ~2 hours
**Deliverables:**
- `app/agent/confidence.py` — confidence scoring:
  1. LLM outputs structured JSON with `confidence` field (0.0–1.0)
  2. Deterministic backup: compute from tool result quality metrics
  3. Threshold: 0.85 for auto-approve, below triggers HITL
  4. Propagated through state at each step
**Depends on:** 6.1, 6.3
**Verification:** Confidence score computed and stored in state

##### 6.8: Execution Trace + Structured Logging + Input Validation
**What:** Implement trace + structured JSON logging (G-23) + 6 input validation guardrails.
**Duration:** ~2.5 hours
**Deliverables:**
- `app/agent/trace.py` — TraceEntry with deviation_log, SSE publishing, `export_trace()` including deviations + confidence trajectory
- `app/shared/logging.py` — structured JSON lines to stdout + file: `timestamp, run_id, step, event_type, payload`
- `app/agent/validation.py` — 6 guardrails: weight bounds, block capacity, truck availability, feeder capacity, vessel margin, tidal window
- LangSmith wiring via `LANGSMITH_API_KEY` env var
**Depends on:** 6.1
**Verification:** Trace entries + deviation_log + structured logs all populated

##### 6.9: Graph Assembly (interrupt + thread_id + monitor)
**What:** Assemble full graph with correct `interrupt()` + `Command` + `MemorySaver(thread_id)` + monitor node.
**Duration:** ~3 hours
**Deliverables:**
- `app/agent/graph.py` — 4 nodes: `agent, tools, hitl (interrupt), monitor`; `route_after_agent` handles tool/hitl/escalation/monitor/END; `route_after_monitor` handles deviation
- `app/agent/run.py` — `run_agent(event, broadcaster) -> {run_id, state, trace}` with `config={"configurable": {"thread_id": run_id}}`; `resume_agent(run_id, decision)` with `Command(resume=)`; `create_initial_state()` with charter 11-field bootstrap
- Webhook `POST /webhook/itt-coordination` + HITL `POST /agent/hitl/respond` in `app/main.py`
**Depends on:** 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.10
**Verification:** Graph compiles; `ainvoke` pauses on interrupt; `Command(resume=)` resumes

##### 6.10: Monitoring / Re-computation Loop (Steps 12–17)
**What:** Implement post-dispatch monitoring that detects feeder berth conflicts and triggers re-planning.
**Duration:** ~3 hours
**Deliverables:**
- `app/agent/monitor.py` — `monitor_node`: re-queries T3, detects berth conflict deviation, re-computes T4 (80/40→100/20), sets HITL-5 emergency card, logs deviation
- Wired as `monitor` node in graph (see 6.9)
**Depends on:** 6.1, 6.5
**Verification:** `pytest app/tests/test_monitor.py -v` — inject conflict → monitor detects → re-compute → HITL-5 → delta dispatch

##### 6.11: End-to-End Integration Test
**What:** Test full pipeline including monitoring loop + deviation recovery (charter 17-step to-be workflow).
**Duration:** ~3 hours
**Deliverables:**
- `app/tests/test_agent_e2e.py` — happy path (10 steps: T1→T3→T4→HITL1→HITL2→HITL3→dispatch→T5→HITL4→complete) + deviation path (7 more: inject→monitor→re-compute→HITL5→delta dispatch→T5 again→complete)
- Verified: charter cost $10,400, all 5 HITL gates with correct timeout_actions, escalation #1+#2 on deviation, confidence 0.95→0.78→0.90, deviation_log populated
**Depends on:** 6.9 (graph must include monitor)
**Verification:** `pytest app/tests/test_agent_e2e.py -v` — both paths complete

---

### Phase 6.5: Integration Wiring & Cleanup
**Goal:** Fix all missing connections — requirements, startup validation, HITL timeouts, SSE events, config consistency, dead code cleanup — so the system actually runs end-to-end without silent failures.
**Depends on:** Phase 6
**Requirements:** T-18, A-17, D-08 + startup validation, timeout scheduler, config consistency
**Success Criteria** (what must be TRUE):
  1. `pip install -r requirements.txt` installs all deps (including `langgraph`) without encoding errors
  2. `.env.example` documents all env vars; `load_dotenv()` wires them at startup
  3. App fails fast with clear error if required env vars missing
  4. `lifespan` handler validates env vars, YAML configs, registry, graph at startup
  5. HITL timeout scheduler auto-fires `timeout_action` after `timeout_seconds`
  6. SSE events `confidence_update` and `notification` published
  7. All 7 YAML configs have consistent `fallback_api_key_env`
  8. `prototype/` deleted, `__init__.py` re-exports, `tool_adapter.py` relocated
  9. LangSmith tracing wired (optional, activates if `LANGSMITH_API_KEY` set)
  10. All existing tests pass + new tests for startup, timeout, SSE coverage
**Status:** ○ NOT STARTED

#### Sub-phases

##### 6.5.1: Fix Dependencies & Environment
**What:** Fix broken requirements file (UTF-16→UTF-8), add missing packages, create `.env.example`, wire `load_dotenv()`.
**Duration:** ~30 minutes
**Deliverables:**
- `requirements.txt` — UTF-8, adds `langgraph`, `langsmith`, `langchain-core`, `python-dotenv`
- `.env.example` — documented template with all env vars
- `app/main.py` — `load_dotenv()` called at module level before FastAPI init
**Depends on:** Phase 6
**Verification:** `file requirements.txt` says UTF-8; `pip install -r requirements.txt` installs cleanly

##### 6.5.2: Startup Lifespan & Validation
**What:** Add FastAPI `lifespan` that validates env vars, YAML configs, registry, graph compilation at startup — fail fast with clear errors.
**Duration:** ~1 hour
**Deliverables:**
- `app/main.py` — `lifespan` async context manager with 5-point validation: API key check, YAML load, registry init, graph compile, LangSmith status
- Clear ✓/✗ per check in startup logs; `sys.exit(1)` on failure
**Depends on:** 6.5.1
**Verification:** `unset ANTHROPIC_API_KEY && python -m uvicorn app.main:app` → clear error, exits

##### 6.5.3: HITL Timeout Scheduler
**What:** Build background task that auto-fires timeout decisions when HITL gates exceed their timeout.
**Duration:** ~1.5 hours
**Deliverables:**
- `app/hitl/timeout_scheduler.py` — `schedule_timeout()`, `cancel_timeout()`, `cancel_all_timeouts()`
- Wired into `hitl_node` (schedules on interrupt) and `POST /agent/hitl/respond` (cancels on manual decision)
- Cleanup on run completion/reset
**Depends on:** 6.5.1
**Verification:** HITL gate fires → wait timeout_seconds → auto-timeout; manual approve before timeout → cancelled

##### 6.5.4: SSE Events & Config Consistency
**What:** Publish missing SSE events, fix YAML config inconsistency, fix unreachable exception handler.
**Duration:** ~1 hour
**Deliverables:**
- `app/agent/nodes.py` — `confidence_update` events published after confidence computation
- `app/tools/notify.py` — `notification` events published when `notify_parties()` called
- 6 YAML configs — add `fallback_api_key_env: OPENAI_API_KEY`
- `app/main.py` — remove unreachable exception handler (lines 218-227)
**Depends on:** 6.5.1
**Verification:** SSE stream shows `confidence_update` and `notification` events; all 7 configs consistent

##### 6.5.5: Cleanup & Relocation
**What:** Delete dead code, re-export modules, relocate mispathed files, wire optional LangSmith.
**Duration:** ~1.5 hours
**Deliverables:**
- `prototype/` — deleted
- `app/agent/__init__.py` — re-exports `build_graph`, `AgentState`, `run_agent`, `resume_agent`, `switch_problem`, `get_active_problem_id`
- `app/hitl/__init__.py` — re-exports `hitl_node`, `handle_hitl_response`, `HITL_GATES`, `schedule_timeout`, `cancel_timeout`
- `app/shared/tool_adapter.py` → `app/tools/tool_adapter.py` (relocated, all imports updated)
- `app/agent/graph.py` — LangSmith wiring (optional, no-op if no API key)
**Depends on:** 6.5.1
**Verification:** `ls prototype/` → not exists; re-exports work; tool_adapter importable from new path

##### 6.5.6: Integration Tests
**What:** Add tests verifying all wiring works together.
**Duration:** ~30 minutes
**Deliverables:**
- `app/tests/test_startup.py` — lifespan validation (4 tests)
- `app/tests/test_timeout.py` — timeout scheduler (3 tests)
- `app/tests/test_sse_events.py` — SSE event coverage (2 tests)
- `app/tests/test_configs.py` — YAML config consistency (3 tests)
**Depends on:** 6.5.2, 6.5.3, 6.5.4, 6.5.5
**Verification:** `pytest app/tests/test_startup.py test_timeout.py test_sse_events.py test_configs.py -v` — 12 new tests pass

---

### Phase 7: Web UI & Integration — PSA Nexus Dashboard
**Goal:** Build the PSA Nexus dashboard with real-time SSE streaming, problem switcher, approval cards, and demo scenario controls.
**Depends on:** Phase 6.5
**Requirements:** U-01 through U-12
**Success Criteria** (what must be TRUE):
  1. Web UI loads in browser with clean, professional design
  2. SSE endpoint streams agent thoughts, tool calls, and HITL cards in real time
  3. HITL approval buttons work (approve/reject/modify)
  4. Edge case injection controls work (feeder conflict, stale data)
  5. Demo scenario can be triggered from UI
**Status:** ○ NOT STARTED

#### Sub-phases

##### 7.1: SSE Endpoint (with Replay Buffer for Race Condition)
**What:** Build SSE endpoint that buffers events before subscriber connects.
**Duration:** ~2 hours
**Deliverables:**
- `app/agent/sse.py` — `SSEBroadcaster` with `queues + buffers(deque maxlen=100) + cleanup`; `publish()` buffers even before `stream()` connects; `stream()` replays buffered events then live streams
- `app/main.py` — `GET /agent/stream/{run_id}`; broadcaster singleton passed to `run_agent(broadcaster=)` via `AgentState["_broadcaster"]`
- 8 event types: `agent_thinking, tool_call, tool_result, hitl_card, escalation, trace_entry, confidence_update, deviation, heartbeat`
**Depends on:** Phase 6
**Verification:** `curl -N localhost:8000/agent/stream/{run_id}` shows buffered + live events

##### 7.2: HTML/CSS/JS Frontend
**What:** Build the web UI with professional design.
**Duration:** ~4 hours
**Deliverables:**
- `app/ui/index.html` — main page with:
  - Agent status panel (current step, confidence score)
  - Agent reasoning display (streaming text)
  - Tool call log (collapsible per tool)
  - HITL approval card area
  - Execution trace sidebar
  - Edge case injection controls
  - Demo scenario trigger button
- `app/ui/style.css` — professional CSS (dark theme, clean typography, responsive)
- `app/ui/app.js` — SSE client, DOM manipulation, event handling
**Depends on:** 7.1
**Verification:** Open `http://localhost:8000/ui/` in browser, UI loads

##### 7.3: HITL Approval Cards
**What:** Build the HITL approval card component with approve/reject/modify buttons.
**Duration:** ~3 hours
**Deliverables:**
- `app/ui/app.js` — HITL card rendering:
  - Card shows: gate name, cost summary, recommendation, confidence score
  - Approve button → POST `/agent/hitl/respond` with decision
  - Reject button → opens text input for rejection reason
  - Modify button → opens text input for modifications
  - Visual feedback (loading, success, error)
- `app/main.py` — HITL response endpoint: `POST /agent/hitl/respond`
**Depends on:** 7.2, Phase 6
**Verification:** HITL card appears when gate fires, buttons send correct responses

##### 7.4: Edge Case Injection Controls (Mutates Mock Data Layer)
**What:** Build UI controls that mutate mock data so monitor re-query sees conflict.
**Duration:** ~2 hours
**Deliverables:**
- `app/ui/app.js` — buttons pass `run_id`; hint "Inject AFTER dispatch, BEFORE monitor check"
- `app/main.py` — `POST /agent/inject-edge-case` mutates `app/mocks/data.py` (not just AgentState); next `monitor_node` T3 re-query sees conflict → escalation #2 + deviation
- Reset: `POST /agent/reset-mocks` restores clean mock data
**Depends on:** 7.2, 6.10 (monitor must exist)
**Verification:** inject → monitor re-query → berth_status="conflict" → deviation detected → HITL-5 fires

##### 7.5: Demo Scenario Runner (SSE-First, with Reset)
**What:** Build demo trigger that connects SSE before starting agent (race fix).
**Duration:** ~2 hours
**Deliverables:**
- `app/ui/app.js` — `run-demo` connects SSE immediately after receiving run_id; `connectSSE()` handles 8 event types; `reset` calls `POST /agent/reset/{run_id}` + `POST /agent/reset-mocks`
- `app/main.py` — `POST /agent/run-demo` returns `{run_id, status, hitl_card?}`; `POST /agent/reset/{run_id}` + `POST /agent/reset-mocks`
- Progress indicator: "Step 6/17: Computing optimal split..."
**Depends on:** 7.2, 7.3
**Verification:** Click "Run Demo" → SSE streams immediately → HITL cards appear → full 17-step scenario plays out

##### 7.6: Execution Trace Display
**What:** Build the execution trace sidebar showing full graph execution.
**Duration:** ~1 hour
**Deliverables:**
- `app/ui/app.js` — trace panel:
  - Collapsible sidebar showing trace entries
  - Each entry: timestamp, node name, action, result
  - Color-coded by type (tool=blue, HITL=yellow, escalation=red, notification=purple, deviation=orange)
**Depends on:** 7.2
**Verification:** Trace entries appear in sidebar as agent runs

##### 7.7: Problem Switcher
**What:** Build the PSA Nexus platform switcher — the proof of generalisability.
**Duration:** ~2 hours
**Deliverables:**
- `app/ui/index.html` — dropdown with 7 problems (PB-01..PB-12), "Switch" button
- `app/ui/app.js` — `switchProblem(id)`: `POST /agent/switch-problem/{id}` → update displayed systems/tools/gates, show "Now running: PB-01 Berth Delay" banner
- `app/main.py` — endpoint already in Phase 4.8; UI just calls it
- Visual: tool list + HITL gate list update when problem switches (e.g. PB-12 shows 5 gates, PB-01 shows 2 gates)
**Depends on:** 7.2, 4.8
**Verification:** Select PB-01 → switch → tool list changes to VTIS/OptEVoyage/CITOS berth; select PB-12 → back to CITOS/OptETruck/PORTNET

##### 7.8: Notification Display
**What:** Show multi-party notifications live.
**Duration:** ~1 hour
**Deliverables:**
- `app/ui/index.html` — notification panel (bell icon + list)
- `app/ui/app.js` — listens for SSE `notification` events → appends `{parties, message, timestamp}` to panel
**Depends on:** 7.2, 5.10
**Verification:** Agent calls `notify_parties` → notification appears in panel + SSE `notification` event

---

### Phase 07.1: Integrated Verification — System-Level E2E, Resilience, and Cross-Problem Regression (INSERTED)

**Goal:** Prove the entire PSA Nexus platform works as one system before deploy — aggregate every seam (webhook → agent → tools → HITL → monitor → SSE → problem-switch) into a single local gate.
**Requirements**: Verifies F-01..F-13, T-01..T-18, A-01..A-23, U-01..U-12, D-05 (no new reqs — system-level gate)
**Depends on:** Phase 7
**Success Criteria** (what must be TRUE):
  1. Full 17-step E2E (happy + deviation) passes via HTTP + SSE with real `thread_id`/`interrupt()`/`Command(resume=)`
  2. HITL matrix 5×5 (approve/reject/modify/timeout/stale) green with per-gate timeout_action + 30-min halt
  3. Resilience chaos green: 429→retry→fallback, 503/timeout→fallback, partial batch, hallucinated tool, concurrency, webhook 422
  4. Robustness S1–S4 re-run in integrated context (nominal/incomplete/503/safety)
  5. Cross-problem PB-12↔PB-01 regression: tool set, prompt, SSE, mock isolation
  6. Trace completeness: `risk_score` in every entry, 10 SSE types, `deviation_log`, structured logs, cost/ROI `$10.4K`/`$8K`
  7. `pytest app/tests/integration/ -v` is the gate — Phase 8 blocked until green
**Status:** ○ NOT STARTED

#### Sub-phases

##### 07.1.1: Integration Harness & Fixtures
**What:** Reusable `TestClient` + SSE harness with per-run `run_id` isolation and mock reset between tests.
**Duration:** ~1 hour
**Deliverables:** `app/tests/integration/conftest.py` (client, clean_mocks, charter_event, mock_llm), `helpers.py` (start_run, hitl_respond, inject_edge, switch_problem, trace/sse asserts)
**Depends on:** Phase 7
**Verification:** Two concurrent `start_run` produce isolated `run_id` + `broadcaster.buffers`

##### 07.1.2: Full E2E — 17-Step Happy + Deviation via HTTP + SSE
**What:** Charter 17-step workflow through real endpoints + SSE replay (race fix), not mocked `run_agent()` alone.
**Duration:** ~1.5 hours
**Deliverables:** `app/tests/integration/test_e2e_system.py` — happy (T1→T4→HITL-1..4→dispatch→T5→complete, `$10.4K`, `deviation_log==[]`) + deviation (inject feeder conflict → monitor detects → `0.78` + esc #1/#2 → re-compute `100/20` → HITL-5 → delta `+4 trucks` → second T5)
**Depends on:** 07.1.1, 6.11
**Verification:** Both paths green + 10 SSE event types observed + webhook `422` on bad inputs

##### 07.1.3: HITL Lifecycle Matrix (5 Gates × 5 Outcomes)
**What:** Every gate × approve/reject/modify/timeout/stale via `POST /agent/hitl/respond` + `thread_id`.
**Duration:** ~1 hour
**Deliverables:** `app/tests/integration/test_hitl_matrix.py` — parametrized 25 cases: approve clears `hitl_pending`, reject shows alternatives or escalates to HITL-5, modify re-validates LTA/feeder/timeline + re-runs T4 + re-presents, timeout per-gate (escalate/cancel/hold/halt + 30-min halt), stale late resume → `422`
**Depends on:** 07.1.1, 6.5
**Verification:** 25 cases green + `Last-Event-ID` SSE replay

##### 07.1.4: Resilience & Fault Injection (Chaos Matrix)
**What:** Competition-probed failures in integrated context (real registry/broadcaster).
**Duration:** ~1.5 hours
**Deliverables:** `app/tests/integration/test_resilience_system.py` — LLM 429→retry→fallback_provider, tool 503 vs timeout distinct + `fallback_used`, partial batch continues, hallucinated tool→error ToolResult, webhook `422`, concurrency 3× runs isolated, per-run edge injection isolated
**Depends on:** 07.1.1, 6.12, 5.1
**Verification:** Chaos matrix all green

##### 07.1.5: Robustness Scenarios (S1–S4) — Integrated Re-Run
**What:** Re-exercise CodeSprint 5.3 robustness now on full stack (5.13 stubs were isolated).
**Duration:** ~1 hour
**Deliverables:** `app/tests/integration/test_robustness_system.py` — S1 nominal, S2 incomplete (weight missing → guardrail → operator input), S3 503 → fallback + notify, S4 safety (cost>$10K → HITL-5 halt)
**Depends on:** 07.1.1, 5.13, 6.5/6.6
**Verification:** All 4 pass post-Phase 6

##### 07.1.6: Cross-Problem Regression (PB-12 ↔ PB-01)
**What:** Prove Nexus is a platform — switching doesn't leak tools/prompt/mocks/SSE.
**Duration:** ~1 hour
**Deliverables:** `app/tests/integration/test_switch_regression.py` — switch PB-12→PB-01 (tool set flips, prompt changes) → E2E PB-12 → switch → E2E PB-01 (2 gates, VTIS/OptEVoyage) → switch back → re-run PB-12; mock isolation + concurrent SSE streams
**Depends on:** 07.1.1, 4.8, 5.11
**Verification:** Back-to-back E2Es green, no leak

##### 07.1.7: Trace, Streaming & Observability Audit
**What:** Judge-scored observability completeness audit.
**Duration:** ~45 min
**Deliverables:** `app/tests/integration/test_observability_audit.py` — every `TraceEntry` has `risk_score = 1 - confidence + 0.15*esc`, structured JSON logs per trace, `deviation_log` on deviation only, `notification` SSE on `notify_parties`, cost math `$10.4K`/`$1.6K`/`$8K`, 6 guardrails (weight/block/trucks/feeder/margin/tidal)
**Depends on:** 07.1.1..07.1.6
**Verification:** Audit green + `integration_coverage.md` table

##### 07.1.8: Pre-Deploy Gate (Go/No-Go)
**What:** The gate that blocks Phase 8 until all 07.1.x green.
**Duration:** ~30 min
**Deliverables:** `app/tests/integration/test_gate.py` + `reports/predeploy_gate.md` (PASS/FAIL per sub-phase), optional `docker build` smoke; blocks `Phase 8` via `Depends on: 07.1`
**Depends on:** 07.1.1..07.1.7
**Verification:** `pytest app/tests/integration/ -v` green → `STATE.md` `07.1 gate: PASS`

**Plans:** 1 plan (this file)

### Phase 8: Polish & Deploy — PSA Nexus Launch
**Goal:** Dockerise PSA Nexus locally, instrument latency, prepare submission assets showcasing it as a generalizable platform. **Railway/Render deployment intentionally skipped — local-only demo.**
**Depends on:** Phase 07.1
**Requirements:** D-01 through D-08
**Success Criteria** (what must be TRUE):
  1. Docker image builds and runs locally via `docker compose up` (localhost:8000) — ~~Railway/Render free tier~~ DISABLED
  2. 10-minute demo video recorded showing PB-12 full flow + sibling switch + edge cases + robustness
  3. 10-slide deck covers problem, disruption gap, solution, autonomy/HITL, architecture, trace/orchestration, guardrails, scalability (PB-12 vs PB-01, $1.26M cluster), ROI, roadmap
  4. All submission assets uploaded before 2026-09-04
  5. Problem switching works locally (PB-12 ↔ PB-01)
  6. Latency metrics captured: SSE p50/p95, wall time
**Status:** ○ NOT STARTED

#### Sub-phases

##### 8.1: Dockerfile
**What:** Create Dockerfile for the application.
**Duration:** ~1 hour
**Deliverables:**
- `Dockerfile` — multi-stage build:
  - Stage 1: Python 3.11-slim, install deps
  - Stage 2: Copy app, expose 8000, run uvicorn
- `.dockerignore` — exclude .planning/, prototype/, .git/, __pycache__/
- `requirements.txt` or `pyproject.toml` — all dependencies
**Depends on:** Phase 7
**Verification:** `docker build -t psa-agent .` succeeds, `docker run -p 8000:8000 psa-agent` starts

##### 8.2: docker-compose.yml
**What:** Create docker-compose for local development.
**Duration:** ~30 min
**Deliverables:**
- `docker-compose.yml` — single service, port 8000, env vars for API keys
**Depends on:** 8.1
**Verification:** `docker compose up` starts app, accessible at localhost:8000

##### ~~8.3: Deploy to Free Tier~~
> **DISABLED — LOCAL-ONLY DEMO.** This sub-phase is intentionally skipped. The demo runs on local Docker (`docker compose up` + `localhost:8000`). Railway/Render deployment not required for competition. Do not execute.
>
> ~~Deployed app accessible via public URL~~ | ~~Environment variables configured~~ | ~~Health check passing~~

##### 8.4: End-to-End Smoke Test
**What:** Test the full demo flow on the **local docker instance** (localhost:8000).
**Duration:** ~2 hours
**Deliverables:**
- Webhook → agent → tools → HITL → approval → dispatch → monitoring
- Edge case injection works
- SSE streaming works
- All gates fire correctly
**Depends on:** 8.2
**Verification:** Full demo scenario completes on localhost:8000

##### 8.5: Presentation Deck
**What:** Create 10-slide presentation deck.
**Duration:** ~4 hours
**Deliverables:**
- `submission/deck.pdf` — 10 slides:
  1. Title slide (team, problem, competition)
  2. Problem: PB-12 ITT Coordination Failure
  3. Baseline: current manual process (5 systems, 45 min)
  4. Agentic Delta: what changes with AI
  5. Architecture: LangGraph + tools + HITL
  6. Decision Logic: LLM reasoning + tool orchestration
  7. Guardrails: HITL gates, escalation triggers, confidence scoring
  8. ROI: $8,000/incident savings, $384K–$576K annual
  9. Demo screenshots (normal + edge case)
  10. Scalability: 7 sibling problems, $1.26M–$2.08M cluster
**Depends on:** 8.4
**Verification:** Deck has 10 slides, covers all required topics

##### 8.6: Demo Video
**What:** Record 10-minute demo video.
**Duration:** ~4 hours
**Deliverables:**
- `submission/demo.mp4` — 10-minute video:
  - 0:00–1:00: Problem introduction
  - 1:00–3:00: Architecture overview
  - 3:00–7:00: Live demo (normal flow)
  - 7:00–9:00: Edge case injection + HITL rejection
  - 9:00–10:00: ROI summary + closing
**Depends on:** 8.4
**Verification:** Video is 10 minutes, shows full demo flow

##### 8.7: Submission Package
**What:** Prepare all submission assets for upload.
**Duration:** ~1 hour
**Deliverables:**
- `submission/` directory with:
  - `deck.pdf` — presentation
  - `demo.mp4` — video
  - `README.md` — project summary
  - `source.zip` — source code archive
  - Any other required assets per competition rules
**Depends on:** 8.5, 8.6
**Verification:** All assets present, README covers required topics

---

## Plan Summary

| Phase | Sub-phases | Est. Time |
|-------|-----------|-----------|
| 4. Foundation Reformation + Platform | 9 (4.1–4.9) | ~1.5 days |
| 5. Tool Integration + Notification + Robustness | 13 (5.1–5.13) | ~2 days |
| 6. Agent Core (LangGraph) — Nexus Brain | 12 (6.1–6.12) | ~2–3 days |
| 6.5. Integration Wiring & Cleanup | 6 (6.5.1–6.5.6) | ~1 day |
| 7. Web UI — Nexus Dashboard | 8 (7.1–7.8) | ~2 days |
| 07.1 Integrated Verification (INSERTED) | 8 (07.1.1–07.1.8) | ~0.5–1 day |
| 8. Polish & Deploy — Nexus Launch | 7 (8.1–8.7, **8.3 DISABLED local-only demo**) | ~1–2 days |
| **Total** | **63** | **~8.5–13 days** |

## Progress

**Execution Order:**
Phases execute in order: 1 → 2 → 3 → 4 → 5 → 6 → 6.5 → 7 → 07.1 → 8

| Phase | Status | Completed |
|-------|--------|-----------|
| 1. Operations Mapping | ✅ Complete | 2026-08-17 |
| 2. Disruption Mining | ✅ Complete | 2026-08-17 |
| 3. Problem Evaluation | ✅ Complete | 2026-08-19 |
| 4. Foundation Reformation | ✅ Complete | 2026-08-27 |
| 5. Tool Integration | ✅ Complete | 2026-08-27 |
| 6. Agent Core (LangGraph) | ✅ Complete | 2026-08-28 |
| 6.5. Integration Wiring & Cleanup | ○ Not Started | — |
| 7. Web UI & Integration | ○ Not Started | — |
| 07.1 Integrated Verification (INSERTED) | ○ Not Started | — |
| 8. Polish & Deploy | ○ Not Started | — |
