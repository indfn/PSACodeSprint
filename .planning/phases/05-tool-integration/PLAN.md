# Phase 5: Tool Integration + Notification + Robustness (PSA Nexus)

## Goal
Build all PB-12 tools with consistent interface, add the notification primitive, stub sibling tools, and verify 4 robustness scenarios — making Nexus a real platform, not just a PB-12 demo.

## Depends on
Phase 4

## Requirements
T-01 through T-18

## Plan

### 5.1: ToolResult Interface & Registry (Canonical — Owner of All Registry Methods)
**Duration:** ~1.5 hours
**What:** Define the standard tool interface and the **single canonical** `ToolRegistry` that Phase 4.8 later extends (not overwrites). This is the owner of `clear`, `register_many`, `register_for_problem`.

> **Ownership rule:** Only this sub-phase defines `app/tools/registry.py`. Phase 4.8 is a *consumer* that calls `registry.register_for_problem()` — it must NOT redefine the file.

**Steps:**
1. Create `app/tools/__init__.py`
2. Create `app/tools/base.py`:
   ```python
   from dataclasses import dataclass, field
   import time
   from abc import ABC, abstractmethod

   @dataclass
   class ToolResult:
       output: dict
       confidence: float  # 0.0–1.0, per-tool data-quality confidence
       metadata: dict = field(default_factory=dict)  # auto-populated by wrapper

       # metadata always contains: tool_name, timestamp (ISO8601), duration_ms, run_id
       # Confidence vs LLM confidence: ToolResult.confidence = data quality;
       #   LLM confidence (state["confidence"]) = decision confidence (Trigger #1 checks LLM one).

   class BaseTool(ABC):
       name: str
       description: str
       parameters_schema: dict  # JSON Schema for LLM tool-calling
       post_approval: bool = False  # True for dispatch_road_itt, request_feeder_hold
       fallback_tool: str | None = None  # e.g. "cached_road_capacity" for T2 fallback

       @abstractmethod
       async def execute(self, **kwargs) -> ToolResult: ...

       async def call(self, **kwargs) -> ToolResult:
           # Wrapper: auto-populates metadata + enforces input validation + timeout
           t0 = time.monotonic()
           # 1. Validate kwargs against parameters_schema (Pydantic)
           # 2. Execute with timeout (asyncio.wait_for, per-tool timeout_seconds)
           # 3. Populate metadata: {tool_name: self.name, timestamp: now(), duration_ms, run_id: kwargs.get("_run_id","")}
           # 4. On hallucinated tool name / invalid args → return ToolResult(output={"error": "..."}, confidence=0)
           ...

       def get_schema(self) -> dict:
           return {"name": self.name, "description": self.description, "parameters": self.parameters_schema}
   ```
3. Create `app/tools/registry.py` — **canonical, complete** (Phase 4.8 must NOT overwrite):
   ```python
   from app.tools.base import BaseTool, ToolResult

   TOOLSETS: dict[str, list[str]] = {
       "pb-12-itt": ["get_itt_candidates","check_road_itt_capacity","check_sea_itt_capacity","compute_itt_split","update_tuas_loading_sequence","dispatch_road_itt","request_feeder_hold","notify_parties"],
       "pb-01-berth": ["query_vessel_arrival","check_berth_availability","check_qc_availability","compute_berth_reassignment","notify_vessel_operator"],
       # ... other problem tool lists from YAML tools[].name
   }

   class ToolRegistry:
       def __init__(self):
           self._tools: dict[str, BaseTool] = {}
           self._active_problem: str = "pb-12-itt"

       def register(self, tool: BaseTool): self._tools[tool.name] = tool
       def register_many(self, tools: list[BaseTool]): ...
       def clear(self): self._tools.clear()
       def list(self) -> list[str]: return list(self._tools.keys())
       def get_schemas(self) -> list[dict]: return [t.get_schema() for t in self._tools.values()]
       def get_tool(self, name: str) -> BaseTool | None: return self._tools.get(name)

       def register_for_problem(self, problem_id: str):
           """Clear and re-register tools for the given problem. Called by Phase 4.8 switch endpoint."""
           self.clear()
           for name in TOOLSETS.get(problem_id, []):
               tool = _create_tool_by_name(name)  # factory
               self.register(tool)
           self._active_problem = problem_id

       async def call(self, name: str, **kwargs) -> ToolResult:
           tool = self._tools.get(name)
           if not tool:
               return ToolResult(output={"error": f"Unknown tool: {name}. Available: {self.list()}"}, confidence=0.0, metadata={"tool_name": name, "error": "hallucinated"})
           # Check post-approval guard: dispatch/hold require prior HITL approve
           if tool.post_approval and not kwargs.pop("_hitl_approved", False):
               # Actual guard is in tool_node (Phase 6.4) — this is defense-in-depth
               pass
           return await tool.call(**kwargs)

   # Singleton — single source, imported as `from app.tools.registry import registry`
   registry = ToolRegistry()
   FALLBACKS: dict[str, str] = {"check_road_itt_capacity": "cached_road_capacity", "check_sea_itt_capacity": "cached_sea_capacity"}

   def load_tools_for_problem(problem_id: str) -> list[BaseTool]:
       """Factory used by registry.register_for_problem — kept here for single-ownership."""
       ...
   ```
4. Create `app/tests/test_registry.py` — test register, call, list, clear, register_many, register_for_problem (PB-12→PB-01→PB-12), hallucinated tool name, fallback mapping
5. Add `app/tools/fallbacks.py` — `cached_road_capacity`, `cached_sea_capacity` (return last-known-good or conservative defaults, flagged `metadata.fallback_used: true`)

**Verification:**
```bash
python -c "from app.tools.registry import ToolRegistry; r = ToolRegistry(); print(r.list())"
pytest app/tests/test_registry.py -v
```

### 5.2: Tool 1 — Container Readiness
**Duration:** ~1 hour
**What:** Port existing container_readiness logic. Charter T1: `get_itt_candidates(cit_ppt_endpoint, vessel_id)`.

> **Design decision (G-06):** Endpoint params (`cit_ppt_endpoint`, etc.) omitted — in-process calls to `app/mocks/data.py`. Charter params kept as comments for future HTTP mode.
> **Reuse:** `prototype/mocks/data.py:generate_containers()` (Random(42), 40×40ft+80×20ft=160TEU, 3 DG, blocks_affected, lta_truck_trip_requirement) is the **canonical test oracle** — don't re-derive. Promote `compute_itt_split_default()` (80/40=$10,400 + 2 alts) as expected value for T-06. `mocks/webhook.py` LRU (OrderedDict MAX_RUNS=100) + `GET /runs/{run_id}` + 400 on `containers_ready>container_count` already handled — reuse, don't rebuild.

**Steps:**
1. Create `app/tools/container_readiness.py`:
   - Class `ContainerReadinessTool(BaseTool)`
   - name = "get_itt_candidates" (matches charter T1)
   - description = "Query PPT CITOS for container readiness status"
   - parameters: vessel_id (string, required) — `cit_ppt_endpoint` omitted per G-06
   - execute(): calls `app/mocks/data.py:get_container_data()` — returns `total_containers, total_teu:160, container_breakdown, lta_truck_trip_requirement: {80 trips, $12K}, containers[], blocks_affected, dg_containers`
   - confidence from `metadata.data_age_minutes` (fresh <5 min → 0.95, stale >30 min → 0.6)
2. JSON schema for LLM tool-calling
3. Unit test: call with vessel_id, verify 120 / 160 TEU / 3 DG / blocks `["B-07","B-08","B-12","B-14"]` — assert against `data.py` fixture

**Verification:**
```bash
pytest app/tests/test_tools.py::TestContainerReadiness -v
```

### 5.3: Tool 2 — Road ITT Capacity
**Duration:** ~1 hour
**What:** Port `prototype/pre_approval/road_itt/optetruck_tools.py` (510L) — **reuse its domain logic, don't re-derive**. It already has: LTA trip math, peak-aware transit (07:30-09:30/17:30-19:30 + 30m pre-peak + 20m lingering, AYE 1.3×/WCH 1.2×), time-of-day fleet (06-09:18, 09-12:20...), esc_5 flag, RoadConditions/RoadITTCapacity classes.

**Steps:**
1. Create `app/tools/road_itt.py`:
   - Class `RoadITTCapacityTool(BaseTool)` — thin wrapper around `prototype` logic
   - name = "check_road_itt_capacity" (matches charter)
   - description = "Query OptETruck for available trucks, transit time, and road conditions for PPT→Tuas"
   - parameters: terminal (string, required), time_window_start (string, required), time_window_end (string, required) — explicit start/end per charter
   - execute(): delegates to ported `optetruck_tools._query_optetruck_fleet()` + congestion multiplier + LTA validation → returns `available_trucks, transit_time_minutes, road_conditions, cost_per_trip:150, lta_chassis_limits, round_trip, capacity_ratio, fleet_utilisation`
   - Reuse `RoadConditions.has_congestion` / `worst_segment` for escalation checks
   - Charter T2 sample: `available_trucks: 20, transit_time: 90 min` — assert against `TRUCK_DATA` fixture
2. JSON schema for LLM tool-calling
3. Unit test: verify time-of-day fleet varies, peak vs off-peak transit differs, esc_5 flag emitted when `available < required*0.6`

**Verification:**
```bash
pytest app/tests/test_tools.py::TestRoadITTCapacity -v
```

### 5.4: Tool 3 — Sea ITT Capacity
**Duration:** ~1 hour
**What:** Port `prototype/pre_approval/sea_itt/` — 580L tools + 152L data_access + 149L router = **6 endpoints** already built (`/capacity`, `/feeder/{id}`, `/feeder/hold`, `/feeders` with filters, `/downstream/{port}`, `/conflict`). Reuse, don't collapse to one query.

**Steps:**
1. Create `app/tools/sea_itt.py`:
   - Class `SeaITTCapacityTool(BaseTool)` — delegates to ported `sea_itt/data_access.py` + `sea_itt_tools.py`
   - name = "check_sea_itt_capacity" (matches charter)
   - description = "Query PORTNET for feeder vessel availability, berth status, departure window, and downstream port tidal constraints"
   - parameters: feeder_id (string, required), current_time (string, required)
   - execute(): calls `data_access.get_feeder_status()` + `get_downstream_port_info()` → returns `feeder_id, capacity_teu:800, available:180, berth_status, departure_window{earliest:14:00,latest:16:00}, downstream_constraints{Port Klang, tidal 23:00, must_depart_by 05:00, buffer 1h}, hold_cost_per_hour:800, missed_connection_cost:5000`
   - Reuse fleet filtering (`get_available_feeders` with berthed/capacity filters), hold-cost model (0-6h validated, `latest_safe_departure = tidal-transit-buffer`), tidal feasibility
2. JSON schema for LLM tool-calling
3. Unit test: verify ATLANTIC-03 returns 6-field window + downstream; test hold-cost safe/marginal/critical; test downstream port fallback

**Verification:**
```bash
pytest app/tests/test_tools.py::TestSeaITTCapacity -v
```

### 5.5: Tool 4 — Multi-Constraint Optimisation
**Duration:** ~2 hours
**What:** Port existing compute_itt_split.py, wire YAML config. Charter T4: `compute_itt_split(candidates, road_capacity, sea_capacity, tuas_vessel_departure, constraints)`.

**Steps:**
1. Create `app/tools/optimiser.py`:
   - Class `OptimiserTool(BaseTool)`
   - name = "compute_itt_split" (matches charter T4)
   - description = "Run multi-constraint optimisation for road/sea allocation. Minimises total cost subject to Tuas vessel departure deadline, feeder departure window, LTA chassis limits, and yard block capacity."
   - parameters: candidates (object, required — output of T1), road_capacity (object, required — output of T2), sea_capacity (object, required — output of T3), tuas_vessel_departure (string, required, ISO 8601), constraints (object, optional — overrides for LTA limits, yard capacity, deadlines) — `problem_id` removed, config loaded from `AgentState.problem_config` instead
   - execute(): calls compute_optimal_split, returns `optimal_split{road_containers, road_trips, road_cost, sea_containers, sea_marginal_charter_cost: 0, sea_terminal_handling_cost, total_transport_cost: 10400}, alternatives[], timeline{}, cost_vs_baseline{}`
   - Must enforce charter input validation guardrails: `containers_per_block ≤ max`, `sea_containers ≤ feeder_available_teu`, `itt_arrival < vessel_departure - 60min`, `feeder_departure < tidal_deadline`
   - Port logic from `prototype/pre_approval/ai_optimisation/compute_itt_split.py` (1148 lines)
   - Wire YAML config for cost params (ProblemConfig.cost_params)
2. JSON schema for LLM tool-calling
3. Unit test: verify 80/40 split = $10,400 for PB-12
   - Charter §3: 40×40ft (40 trips) + 40×20ft (20 trips) = 60 road trips × $150 = $9,000; 40×20ft sea = $1,400 handling → total $10,400
   - Wire YAML config for cost params (handle $35/lift, $150/trip, $800/hr feeder hold)

**Verification:**
```bash
pytest app/tests/test_tools.py::TestOptimiser -v
# Verify: output['optimal_split']['road_containers'] == 80
# Verify: output['optimal_split']['sea_containers'] == 40
# Verify: output['optimal_split']['total_transport_cost'] == 10400
```

### 5.6: Tool 5 — Tuas Loading Sequence
**Duration:** ~2 hours
**What:** NEW implementation. Charter T5: `update_tuas_loading_sequence(cit_tuas_endpoint, vessel_id, itt_eta_road, itt_eta_sea, container_ids_road, container_ids_sea)`.

**Steps:**
1. Create `app/tools/tuas_loading.py`:
   - Class `TuasLoadingTool(BaseTool)`
   - name = "update_tuas_loading_sequence" (matches charter)
   - description = "Update Tuas QC loading sequence based on ITT arrival predictions"
   - parameters: vessel_id (string, required), itt_eta_road (string, required, ISO 8601), itt_eta_sea (string, required, ISO 8601), container_ids_road (array[string], required), container_ids_sea (array[string], required) — `cit_tuas_endpoint` omitted per G-06; explicit ETAs + container lists per charter for bay→QC mapping
   - execute(): computes QC adjustments based on ETAs, returns `original_loading_sequence, updated_loading_sequence, qc_adjustments[{qc_id, original_bay, new_bay, eta}], estimated_loading_completion, margin_before_departure_minutes`
   - Logic: road containers (arriving ~14:30) loaded first, sea containers (arriving ~16:30) loaded second; adjusts bay assignment to match arrival order
2. JSON schema for LLM tool-calling
3. Add mock endpoint `POST /api/citos/tuas/loading-sequence` for testing
4. Unit test: verify QC adjustments map correctly for 80 road + 40 sea split

**Verification:**
```bash
pytest app/tests/test_tools.py::TestTuasLoading -v
```

### 5.7: Post-Approval Tools
**Duration:** ~2 hours (split into 5.7a + 5.7b, ~1hr each)
**What:** NEW implementations for dispatch and feeder hold. Only callable AFTER HITL approval — agent must not call these without a prior approve decision in `hitl_history`.

> **Charter:** `dispatch_road_itt(optetruck_endpoint, num_trucks, route)` and `request_feeder_hold(portnet_endpoint, feeder_id, hold_hours)` — feeder operator is an independent carrier (REQUEST, not command).

**Steps:**
1. Create `app/tools/dispatch_road_itt.py` (5.7a):
   - Class `DispatchRoadITTTool(BaseTool)`
   - name = "dispatch_road_itt" (matches charter — not `dispatch_trucks`)
   - description = "Dispatch prime movers via OptETruck for road ITT. Requires HITL Gate 2 approval. Route: PPT → West Coast Highway → AYE → Tuas Port Boulevard."
   - parameters: num_trucks (integer, required), route (string, required — e.g., "PPT → West Coast Highway → AYE → Tuas Port Boulevard"), container_ids (array[string], required) — `optetruck_endpoint` omitted per G-06; `approved` is NOT a tool param (HITL gate enforces approval before tool call)
   - execute(): returns dispatch confirmation with truck assignments + ETA
   - Must support delta dispatch: if re-computed split is 100 road vs original 80, tool dispatches additional 10 trips (4 trucks × 2–3 trips each)
2. Create `app/tools/request_feeder_hold.py` (5.7b):
   - Class `RequestFeederHoldTool(BaseTool)`
   - name = "request_feeder_hold" (matches charter)
   - description = "Request feeder vessel hold via PORTNET. Requires HITL Gate 3 approval. NOTE: This is a REQUEST — feeder operator may decline."
   - parameters: feeder_id (string, required), hold_hours (number, required) — `portnet_endpoint` omitted per G-06; `containers` removed (not in charter)
   - execute(): returns hold confirmation with cost (`hold_hours × $800/hr`) + operator response (accepted/declined)
3. JSON schemas for both
4. Unit tests — including test that feeder operator decline is handled

**Verification:**
```bash
pytest app/tests/test_tools.py::TestDispatchRoadITT -v
pytest app/tests/test_tools.py::TestRequestFeederHold -v
```

### 5.8: Edge Case Hooks
**Duration:** ~1 hour
**What:** Wire edge case simulation into agent-accessible hooks. These are NOT LLM-callable tools — they are demo injection hooks called via `POST /agent/inject-edge-case`.

> **Critical:** Hooks must mutate the **mock data layer** (`app/mocks/data.py` — feeder berth_status, departure_window, container timestamps) so the NEXT `check_sea_itt_capacity` / `get_itt_candidates` call sees the conflict/staleness. Mutating only `AgentState` is insufficient.

**Steps:**
1. Create `app/tools/edge_cases.py` (hooks, not BaseTool):
   - `inject_feeder_berth_conflict(feeder_id, new_departure: str)` — sets `berth_status="conflict"`, `departure_window.latest = "2026-08-19T16:00:00+08:00"` in mock data
   - `inject_stale_data(time_offset_minutes: int)` — backdates container readiness timestamps by offset
   - Both exposed via `POST /agent/inject-edge-case` endpoint in `app/main.py` (Phase 7.4) — NOT via tool registry
   - Charter: `simulate_feeder_conflict()` and `simulate_stale_data()` from `mocks/edge_cases.py` already exist; wire them to the mock data store
2. Unit tests: inject → query T3 → verify conflict is visible

**Verification:**
```bash
pytest app/tests/test_tools.py::TestEdgeCases -v
```

### 5.9: Integration Test (PB-12 Tools)
**Duration:** ~2 hours
**What:** Test all PB-12 tools end-to-end against mock server.

**Steps:**
1. Create `app/tests/test_tools.py`:
   - Test each tool individually against live mock server
   - Test tool registry: register all tools, list them, call each
   - Test ToolResult format consistency
   - Test confidence scores are within valid range
2. Test edge cases: missing parameters, invalid inputs, server errors

**Verification:**
```bash
pytest app/tests/test_tools.py -v  # all tools pass
```

### 5.10: Notification Tool (Primitive #5)
**Duration:** ~1 hour
**What:** Implement the missing multi-party notification primitive (charter §6, primitive #5).

**Steps:**
1. Create `app/tools/notify.py`:
   ```python
   class NotifyPartiesTool(BaseTool):
       name = "notify_parties"
       description = "Send alerts to affected stakeholders (PPT yard, Tuas yard, feeder operator, etc.)"
       parameters: message (string, required), parties (array[string], required — e.g. ["PPT_Yard", "Tuas_Yard", "Feeder_Operator"])

       async def execute(self, message: str, parties: list[str]) -> ToolResult:
           # Validate parties against known stakeholders in ProblemConfig
           # Mock: append to app/mocks/data.py notification_log
           # Publish SSE 'notification' event
           # Log to trace: {event: "notification", parties, message}
           return ToolResult(output={"notified": parties, "message": message, "timestamp": now()}, confidence=1.0, metadata={...})
   ```
2. Add `POST /api/notify` mock endpoint in `app/mocks/routers/notify.py`
3. Wire SSE: `broadcaster.publish(run_id, 'notification', {parties, message})`
4. UI panel: notification bell + list (Phase 7.8)

**Verification:**
```bash
pytest app/tests/test_notify.py -v
# verify: notify_parties("Feeder delayed to 1600", ["PPT_Yard","Tuas_Yard"]) → trace entry + SSE event
```

### 5.11: Sibling Tool Stubs (PB-01 — Proves Platform Generalisability)
**Duration:** ~2 hours
**What:** Stub PB-01 tools so Nexus can run a second problem end-to-end.

**Steps:**
1. Create `app/tools/pb01/`:
   - `query_vessel_arrival(vessel_id)` → VTIS mock: ETA, pilot/tug availability
   - `check_berth_availability(vessel_id, berth_id)` → OptEVoyage mock: berth windows, draft limits, tidal windows
   - `check_qc_availability(berth_id)` → CITOS mock: QC count, crane status
   - `compute_berth_reassignment(vessel_id, constraints)` → mock optimiser: new berth + QC allocation
   - `notify_vessel_operator(vessel_id, message)` → VTIS mock
2. Create `app/mocks/routers/vtis.py`, `optevoyage.py`, `berth.py` — mock endpoints with PB-01 fixture data
3. Enhance `app/tools/registry.py`: `register_for_problem(problem_id)` loads correct tool set per YAML `tools:` list

**Verification:**
```bash
curl -X POST localhost:8000/agent/switch-problem/pb-01-berth
python -c "from app.tools.registry import registry; print(registry.get_tool_names())"  # → 5 PB-01 tools
pytest app/tests/test_pb01_tools.py -v
```

### 5.12: Cost/ROI Equation
**Duration:** ~1 hour
**What:** Implement the charter §5 cost/ROI math that was never coded.

**Steps:**
1. Extend `app/tools/optimiser.py` T4 output:
   ```python
   cost_vs_baseline = {
       "baseline_all_road": 80 * 150,          # $12,000
       "optimised": 60 * 150 + 40 * 35,        # $10,400
       "transport_savings": 12000 - 10400,      # $1,600
   }
   roi = {
       "per_incident": 8450 - 450,              # $8,000 (charter §5 equation)
       "monthly": f"${4*8000}-${6*8000}",       # $32K-$48K
       "annual": f"${384000}-${576000}",
       "cluster_annual": "$1.26M-$2.08M",
   }
   ```
   Sources: YAML `cost_params` (vessel_demurrage $2500/hr, feeder $800/hr, $150/trip, $35 handling, $35 re-handle, $150 missed, 4500 TEU block)
2. Create `app/tests/test_roi.py` — verify every number against charter §5

**Verification:**
```bash
pytest app/tests/test_roi.py -v  # baseline $12K, optimised $10.4K, savings $1.6K, incident $8K
```

### 5.13: 4 Robustness Scenarios (CodeSprint Phase 5.3)
**Duration:** ~2 hours
**What:** Verify the 4 required robustness scenarios per competition brief Phase 5.3.

> **Depends note:** S1–S3 run standalone (tools + guards only, no agent graph). S4 requires HITL-5 (Phase 6.5) + escalation (Phase 6.6) — run after Phase 6. Mark S4 as `pytest.mark.depends_on_phase6` so `pytest app/tests/ -v` doesn't fail before Phase 6 ships.

**Steps:**
1. Create `app/tests/test_robustness.py`:

   **S1 — Nominal (happy path):**
   120 containers, all systems healthy → agent calls T1→T3→T4→HITL-1→HITL-2→HITL-3→dispatch→T5→HITL-4→done → trace clean with `risk_score` on every entry, SSE `trace_entry` per step

   **S2 — Incomplete Data:**
   Container `weight_kg` missing → input guardrail fires (`weight_bounds`) → trace `guardrail_failed` → agent detects gap, queries `yard_status` (T1's `GET /yard-status`) as secondary source or asks operator "weight unknown for MSKU7654321, verify?" → HITL card with gap info → trace shows `guardrail_failed` + `hitl_card` + SSE `confidence_update` → resolves

   **S3 — API Failure (503/timeout):**
   Mock T2 returns HTTP 503 (or `asyncio.TimeoutError` for latency variant) → agent detects `tool_error`/`tool_timeout` distinctly → logs `tool_error_fallback` or `tool_timeout_fallback` to trace → retries once (exponential backoff 1s→2s) → uses `FALLBACKS["check_road_itt_capacity"]` → `cached_road_capacity` with `metadata.fallback_used: true` → alerts operator via `notify_parties` → trace shows `tool_error` + `fallback_used` + `notification` SSE event

   **S4 — Safety Escalation (requires Phase 6):**
   T4 result triggers Trigger #3 (`action_cost > $10K`) or simulated vessel departure shift >2h → agent halts normal flow, produces structured HITL-5 review card: "High-risk action requires sign-off — vessel departure shift 2.5h", awaits Duty Manager → trace shows `escalation` + `hitl_card` (HITL-5) + SSE `escalation` event

2. Each scenario: trace shows correct handling with `risk_score`, SSE streams all event types, `notification` sent where applicable

**Verification:**
```bash
pytest app/tests/test_robustness.py -v       # all 4 (S4 skipped before Phase 6)
pytest app/tests/test_robustness.py::TestS1  # nominal → trace clean + risk_score
pytest app/tests/test_robustness.py::TestS2  # incomplete → guardrail + HITL
pytest app/tests/test_robustness.py::TestS3  # 503/timeout → fallback + trace + notification SSE
pytest app/tests/test_robustness.py::TestS4  # safety → HITL-5 (pass after Phase 6)
```

## Verification Loop

After all sub-phases complete:
1. `pytest app/tests/test_tools.py -v` — all PB-12 tool tests pass
2. `pytest app/tests/test_registry.py -v` — registry tests pass (including `clear()` + `register_many()` for problem switching)
3. Each tool returns valid ToolResult; `confidence` is per-tool (ToolResult field), propagated separately from LLM confidence
4. Tool 4 returns correct PB-12 split (80/40 = $10,400) + `cost_vs_baseline` + `roi`: `pytest app/tests/test_roi.py -v`
5. All tools have JSON schemas matching charter tool names (`get_itt_candidates`, `check_road_itt_capacity`, `check_sea_itt_capacity`, `compute_itt_split`, `update_tuas_loading_sequence`, `dispatch_road_itt`, `request_feeder_hold`, `notify_parties`)
6. Edge case hooks mutate mock data → next T3 query sees conflict: `pytest app/tests/test_edge_cases.py -v`
7. Post-approval tools reject calls without prior HITL approval in state (guard test)
8. Input validation guardrails: test weight bounds, vessel margin, tidal window rejection
9. Notification tool: `pytest app/tests/test_notify.py -v` — SSE `notification` event + trace entry
10. Sibling stubs: `pytest app/tests/test_pb01_tools.py -v` — PB-01 tool set switches correctly
11. 4 robustness scenarios: `pytest app/tests/test_robustness.py -v` — nominal, incomplete data, 503 fallback, safety escalation
12. Problem switching: `POST /agent/switch-problem/pb-01-berth` → PB-01 tools; `pb-12-itt` → back to ITT

## Commit
After verification: `git commit -m "Phase 5: Nexus tools — PB-12 + notification + PB-01 stubs + ROI + robustness"`
