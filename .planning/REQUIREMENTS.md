# Requirements: PSA Nexus — Agentic Multi-Party Coordination Platform

**Defined:** 2026-08-17
**Updated:** 2026-08-27
**Product:** PSA Nexus — Agentic Multi-Party Coordination Platform (Cluster C2, 7 problems)
**Core Value:** Build PSA Nexus, a working provider-agnostic agentic platform demonstrated via PB-12 (ITT Coordination, $8K/incident) and proven generalizable to a sibling problem (e.g. PB-01 Berth Delay) on the same LangGraph core, ready for competition submission by 2026-09-04.

---

## Competition Requirements

| ID | Requirement | Status | Phase |
|----|-------------|--------|-------|
| COMP-01 | Problem is identified within PSA Singapore's operational or supply chain ecosystem | ✅ Done | 3 |
| COMP-02 | Solution addresses all 6 mandatory agentic capabilities | ○ Rebuilding | 4–7 |
| COMP-03 | 10-slide presentation deck | ○ Not started | 8 |
| COMP-04 | 10-minute demo video showing running agent handling normal and edge-case inputs | ○ Not started | 8 |
| COMP-05 | All submission assets complete by 2026-09-04 | ○ Not started | 8 |

### COMP-02 Breakdown: 6 Mandatory Agentic Capabilities

| Capability | How It's Demonstrated | Phase |
|------------|----------------------|-------|
| Event Ingestion & Perception | Webhook receives ITT_COORDINATION_REQUEST event, parses payload, extracts context | 5, 6 |
| Reasoning & Dynamic Planning | LLM reasons about tools to call, sequences actions, handles deviations | 6 |
| Tool & System Orchestration | Agent calls 5 tools (CITOS, OptETruck, PORTNET, optimiser, Tuas) via tool registry | 5, 6 |
| State Tracking & Observable Execution Trace | LangGraph state checkpointing + LangSmith trace output | 6 |
| Human-in-the-Loop Controls | 5 HITL gates with approve/reject/modify + timeout + escalation | 6 |
| Uncertainty & Error Recovery | Confidence scoring, escalation triggers, re-planning on failure | 6, 7 |

---

## Research Requirements (Phases 1–3) — COMPLETE

| ID | Requirement | Status |
|----|-------------|--------|
| P1-01 | All 4 operational sectors researched with sector-specific topic depth | ✅ |
| P1-02 | All 7 baseline digital systems mapped with capabilities, integrations, and data flows | ✅ |
| P1-03 | Physical, Information, and Decision flows mapped for each of the 4 sectors | ✅ |
| P2-01 | 16 candidate problems identified spanning all 4 sectors | ✅ |
| P2-02 | Each problem documented with Trigger Event, Current Workaround, and Business Consequence | ✅ |
| P2-03 | Focus on dynamic "something changed" scenarios where static rules fail | ✅ |
| P3-01 | Every candidate problem scored against all 5 litmus-test criteria | ✅ |
| P3-02 | Target autonomy level defined and justified (HITL Exception Solver) | ✅ |
| P3-03 | Single Master Problem Charter locked with persona, autonomy level, and impact equation | ✅ |

---

## Build Requirements — Detailed

### Phase 4: Foundation Reformation + Platform Generalisation

| ID | Requirement | Acceptance Criteria | Priority |
|----|-------------|---------------------|----------|
| F-01 | Unified FastAPI app entry point | `app/main.py` starts on port 8000, serves `/health`, `/agent/*`, `/mocks/*`, `/ui/*` | CRITICAL |
| F-02 | Directory restructure | Old `prototype/` contents moved to `app/agent/`, `app/tools/`, `app/mocks/`, `app/hitl/`, `app/ui/`, `app/shared/`, `app/configs/` | CRITICAL |
| F-03 | provider.py tested end-to-end (8 providers) | Create provider from config (`provider: anthropic|openai|gemini|deepseek|ollama|vllm|lmstudio|custom`), call `chat()` with tool schemas, verify `tool_calls` in response. Test with ≥2 provider families (e.g. anthropic/AnthropicProvider + custom/CustomProvider pointing at Ollama or mock). Must verify `custom` with `base_url` (any OpenAI-compatible API: OpenRouter, Together, Groq, etc.) | CRITICAL |
| F-04 | YAML config system validated (PB-12) | Load `pb-12-itt.yaml`, verify all fields (5 systems, 8 tools, 5 HITL gates, 7 escalation triggers, cost params, constraints, LLM settings) parse correctly into `ProblemConfig` | CRITICAL |
| F-05 | Duplicate consolidation | One webhook handler (not two), one set of Pydantic schemas (not three) at `app/shared/models.py`, one mock data source | HIGH |
| F-06 | Old orchestrator removed | `pre_approval/orchestrator.py` explicitly deleted, replaced by LangGraph agent in Phase 6 | MEDIUM |
| F-07 | Tests pass | `pytest app/tests/` — at minimum: config loading (all 7 problems), provider creation + adapter, health endpoint | HIGH |
| F-08 | Provider adapter for tool-calling format (all families) | Adapter translates tool schemas across all provider families: OpenAI-compatible (`openai`, `deepseek`, `ollama`, `vllm`, `lmstudio`, `custom`) uses OpenAI `tools` format directly; Anthropic uses `input_schema`; Gemini uses `functionDeclarations`. Must handle `base_url` / `api_key` for custom. | HIGH |
| F-09 | All 7 sibling YAML configs complete | `pb-01`, `pb-02`, `pb-04`, `pb-09`, `pb-10`, `pb-11`, `pb-12` all have: systems, tools, ≥1 HITL gate, 7 escalation triggers, confidence, cost params, constraints, edge cases. Only PB-12 was complete — siblings must be filled in. | CRITICAL |
| F-10 | All 7 configs load correctly | `for id in [pb-01..pb-12]: load_problem_config(id)` — all parse without error, correct system/tool counts | HIGH |
| F-11 | Cost params complete (10 rows) | YAML `cost_params` includes all charter §5 rows: vessel demurrage $2500/hr, feeder charter $800/hr, road trip $150, LTA chassis, $0 sea charter, $35 handling, $800 hold, $35 re-handle, $150 missed connection, 4500 TEU block max | HIGH |
| F-12 | Problem switching mechanism | `POST /agent/switch-problem/{problem_id}` — loads new `ProblemConfig`, re-registers tool set, returns new system/tool/gate list. Same LangGraph core, different config. | CRITICAL |
| F-13 | Platform generalisability proven | Switch PB-12 ↔ PB-01: prompt is templated from `ProblemConfig` (not hardcoded to ITT), agent adapts tool selection. Verified by loading PB-01 config + calling its tools. | CRITICAL |

### Phase 5: Tool Integration + Notification + Robustness

| ID | Requirement | Acceptance Criteria | Priority |
|----|-------------|---------------------|----------|
| T-01 | ToolResult interface | All tools return `ToolResult(output: dict, confidence: float, metadata: dict)` | CRITICAL |
| T-02 | Tool registry | `tools/registry.py` maps tool names to functions + JSON schemas; supports dynamic re-registration per problem (F-12) | CRITICAL |
| T-03 | Tool 1: Container readiness (PB-12 T1) | `get_itt_candidates(vessel_id)` → 120 containers, 160 TEU, breakdown, blocks. Charter spec. | CRITICAL |
| T-04 | Tool 2: Road ITT capacity (PB-12 T2) | `check_road_itt_capacity(terminal, time_window_start, time_window_end)` → 20 trucks, 90 min transit, road conditions | CRITICAL |
| T-05 | Tool 3: Sea ITT capacity (PB-12 T3) | `check_sea_itt_capacity(feeder_id, current_time)` → feeder capacity + departure window + downstream tidal constraints | CRITICAL |
| T-06 | Tool 4: Multi-constraint optimisation (PB-12 T4) | `compute_itt_split(candidates, road_capacity, sea_capacity, tuas_vessel_departure, constraints)` → 80/40 = $10,400 (60×$150 + 40×$35). Charter spec. | CRITICAL |
| T-07 | Tool 5: Tuas loading sequence (PB-12 T5) | `update_tuas_loading_sequence(vessel_id, itt_eta_road, itt_eta_sea, container_ids_road, container_ids_sea)` → QC adjustments. NEW. | HIGH |
| T-08 | Post-approval: dispatch_road_itt | `dispatch_road_itt(num_trucks, route, container_ids)` — route: PPT→West Coast Hwy→AYE→Tuas. Supports delta dispatch. HITL-gated. | HIGH |
| T-09 | Post-approval: request_feeder_hold | `request_feeder_hold(feeder_id, hold_hours)` — operator may decline. HITL-gated. | HIGH |
| T-10 | Tool JSON schemas | Each tool has a JSON schema for LLM tool-calling (name, description, parameters, returns) — names match charter | CRITICAL |
| T-11 | Edge case hooks (NOT LLM tools) | `inject_feeder_berth_conflict()` + `inject_stale_data()` mutate `app/mocks/data.py` so next T3/T1 query sees the issue. Via `POST /agent/inject-edge-case`. | MEDIUM |
| T-12 | Notification tool (primitive #5) | `notify_parties(message, parties: list[str])` — sends alerts to affected stakeholders. Mock: logs to trace + SSE `notification` event. Charter shared primitive #5. | HIGH |
| T-13 | Sibling tool stubs (PB-01) | At least PB-01 tools stubbed: `query_vessel_arrival`, `check_berth_availability`, `check_qc_availability`, `compute_berth_reassignment`, `notify_vessel_operator` — with mock data at `app/mocks/routers/vtis.py` etc. | HIGH |
| T-14 | Cost/ROI equation | Tool T4 output includes `cost_vs_baseline: {baseline $12K, optimised $10.4K, savings $1.6K}` and per-incident math `Savings = $8450 - $450 = $8000` (charter §5). Computed from YAML cost params. | HIGH |
| T-15 | Robustness: nominal path | Scenario 1 (CodeSprint 5.3): standard 120-container event → agent resolves cleanly, all tools called, HITL-approved | CRITICAL |
| T-16 | Robustness: incomplete data | Scenario 2 (CodeSprint 5.3): required field missing (e.g. container weight) → agent detects gap (guardrail), queries secondary tool or asks operator | CRITICAL |
| T-17 | Robustness: API failure | Scenario 3 (CodeSprint 5.3): downstream API returns 503/timeout → agent detects, logs to trace, uses fallback (e.g. cached data or alternative tool), alerts operator | CRITICAL |
| T-18 | Robustness: safety escalation | Scenario 4 (CodeSprint 5.3): action triggers high-risk threshold (e.g. vessel departure shift >2h, cost >$10K) → agent halts, produces HITL-5 review card | CRITICAL |

### Phase 6: Agent Core (LangGraph)

| ID | Requirement | Acceptance Criteria | Priority |
|----|-------------|---------------------|----------|
| A-01 | LangGraph StateGraph | `StateGraph` defined with typed state schema (messages, tools, hitl, trace, confidence). Uses `interrupt()` + `Command(resume=)` + `MemorySaver` with `thread_id`. | CRITICAL |
| A-02 | Agent node | LLM receives system prompt + tools + context, reasons about next action, calls tools via tool-calling | CRITICAL |
| A-03 | Tool execution node | Tool calls dispatched to tool registry, results returned to agent | CRITICAL |
| A-04 | HITL Gate 1: Approve ITT Split | Trigger: split computed. Timeout 30 min → Escalate to Duty Manager. Card shows split + cost + confidence. | CRITICAL |
| A-05 | HITL Gate 2: Approve Truck Dispatch | Trigger: truck dispatch ready. Timeout 15 min → Cancel Dispatch. Card shows truck count + route + cost. | CRITICAL |
| A-06 | HITL Gate 3: Approve Feeder Hold | Trigger: feeder hold request ready. Timeout 15 min → Escalate to Duty Manager. Card shows hold duration + cost + tidal risk. | CRITICAL |
| A-07 | HITL Gate 4: Approve Loading Sequence Update | Trigger: Tuas QC sequence update ready. Timeout 10 min → Hold Current Sequence. Card shows bay/QC adjustments. | CRITICAL |
| A-08 | HITL Gate 5: Escalate to Duty Manager | Trigger: escalation fired / agent cannot resolve. Timeout 30 min → Halt Workflow. If Duty Manager also silent 30 min → halt entirely. | CRITICAL |
| A-09 | HITL rejection handling | REJECT: log reason + present `alternatives[]` from Tool 4 or escalate to Duty Manager if no alternatives. MODIFY: re-validate vs LTA/feeder/timeline constraints + re-run Tool 4 + present updated cost + re-request approval. TIMEOUT: per-gate timeout_action + second-level 30 min halt rule. | CRITICAL |
| A-10 | Escalation trigger 1: Low model confidence | `confidence < 0.85` → escalate to human | HIGH |
| A-11 | Escalation trigger 2: Feeder hold exceeds tidal tolerance | `hold_duration > 1.5 hrs` → escalate to Duty Manager | HIGH |
| A-12 | Escalation trigger 3: Financial recovery cost > limit | `action_cost > $10,000` → escalate to Duty Manager | HIGH |
| A-13 | Escalation trigger 4: Data latency exceeds freshness | `data_age > 30 min` → escalate to human | HIGH |
| A-14 | Escalation trigger 5: Road ITT capacity below threshold | `available_trucks < 60% required` → escalate to human | HIGH |
| A-15 | Escalation trigger 6: Feeder operator unresponsive | `feeder_response_time > 15 min` → escalate to human | HIGH |
| A-16 | Escalation trigger 7: Conflict between planners | Planner recommendations conflict → escalate to Duty Manager | HIGH |
| A-17 | Confidence scoring | LLM outputs structured JSON with `confidence` field (0.0–1.0). Threshold 0.85 for auto-approve, below triggers HITL (Trigger #1). Deterministic backup if LLM confidence missing. | HIGH |
| A-18 | Execution trace + deviation log | Every step logged: node entry/exit, tool calls, HITL events, deviations, timestamps. Deviation log: why original plan failed + how recovery executed. | HIGH |
| A-19 | LangSmith integration | Trace exported to LangSmith for visualization (or structured JSON trace if no API key). Env var `LANGSMITH_API_KEY` wired via Phase 4/8. | MEDIUM |
| A-20 | End-to-end: webhook → agent → tools → HITL → result | Send ITT_COORDINATION_REQUEST to webhook, agent processes, tools called, HITL gates fire, result returned. Includes monitoring loop + re-computation after deviation. | CRITICAL |
| A-21 | Input validation guardrails | 6 guards: weight bounds, block capacity, truck availability, feeder capacity, vessel departure margin, tidal window. Checked at webhook bootstrap + before each tool call. | HIGH |
| A-22 | Monitoring / re-computation loop | After dispatch, agent monitors feeder status (re-queries T3). On berth conflict → re-computes split (T4) → presents emergency HITL card → dispatches delta trucks → updates Tuas sequence. | CRITICAL |
| A-23 | Structured logging | JSON lines to stdout + file: `timestamp, run_id, step, event_type, payload` per G-23. Separate from trace. | MEDIUM |

### Phase 7: Web UI & Integration (PSA Nexus Dashboard)

| ID | Requirement | Acceptance Criteria | Priority |
|----|-------------|---------------------|----------|
| U-01 | HTML/CSS/JS frontend ("PSA Nexus" branding) | Loads in browser, header "PSA Nexus — Agentic Multi-Party Coordination Platform", clean professional design, responsive | CRITICAL |
| U-02 | SSE endpoint | `GET /agent/stream/{run_id}` returns SSE with replay buffer (8 event types: thinking, tool_call/result, hitl_card, escalation, trace_entry, confidence, deviation, notification, heartbeat) | CRITICAL |
| U-03 | Real-time agent display | Agent reasoning displayed as it happens (streaming text) | HIGH |
| U-04 | HITL approval cards | Card shows: gate name (HITL-1..5), cost summary, split recommendation, confidence, timeout countdown, approve/reject/modify buttons | CRITICAL |
| U-05 | HITL reject flow | User clicks reject → agent halts → presents alternatives → new card shown (or escalate to HITL-5 if no alternatives) | HIGH |
| U-06 | HITL modify flow | User clicks modify → text input for changes → agent re-validates via guardrails → re-runs T4 → new card | HIGH |
| U-07 | Edge case injection (berth conflict) | Button to inject feeder berth conflict — mutates mock data layer so monitor re-query sees it. Hint: "Inject AFTER dispatch, BEFORE monitor check" | HIGH |
| U-08 | Stale data injection | Button to inject stale container data (backdate timestamps) → triggers Trigger #4 data_stale >30 min | MEDIUM |
| U-09 | Demo scenario runner | "Run Demo" button triggers full happy-path scenario (happy + deviation paths). SSE connects before agent starts (race fix). Reset also clears mock injections. | HIGH |
| U-10 | Execution trace display | Sidebar showing full trace (nodes, tools, timestamps, colour-coded) + deviation log panel | MEDIUM |
| U-11 | Problem switcher | Dropdown: PB-12 ↔ PB-01 (or other sibling). Calls `POST /agent/switch-problem/{id}`, re-registers tools, shows new tool/gate list. Proves platform claim. | CRITICAL |
| U-12 | Notification display | Panel showing `notify_parties` dispatches (stakeholder, message, timestamp). Updates live. | MEDIUM |

### Phase 8: Polish & Deploy

| ID | Requirement | Acceptance Criteria | Priority |
|----|-------------|---------------------|----------|
| D-01 | Dockerfile | `docker build` succeeds, image < 500MB | CRITICAL |
| D-02 | docker-compose.yml | `docker compose up` starts app on port 8000 | CRITICAL |
| D-03 | Railway/Render deployment | App accessible via public URL; env vars: LLM provider, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT=psa-nexus` | CRITICAL |
| D-04 | End-to-end test (PB-12 + sibling) | PB-12: webhook → agent → tools → HITL → approval → dispatch → monitoring → deviation → re-plan. PB-01: switch problem → tools adapt → HITL fires. Both on public URL. | CRITICAL |
| D-05 | 10-slide presentation deck (PSA Nexus) | 10 slides per CodeSprint §6.2 rubric: problem, disruption gap, solution/value prop, autonomy/HITL, architecture, trace/orchestration, guardrails/fallback, scalability+generalisability (PB-12 vs PB-01 visual, 1 YAML = 1 problem), ROI ($8K/incident + $1.26M cluster), roadmap | CRITICAL |
| D-06 | 10-minute demo video (PSA Nexus) | Per CodeSprint §6.3: problem (0:00–2:00) → architecture (2:00–3:30) → live walkthrough normal+deviation+HITL+robustness (3:30–7:30) → guardrails/scalability (7:30–9:00) → ROI/close + sibling switch (9:00–10:00) | CRITICAL |
| D-07 | Submission assets | All assets uploaded to competition portal before 2026-09-04 | CRITICAL |
| D-08 | Latency & Responsible AI metrics | Measure: SSE latency (p50/p95), wall time (target <30s for happy path, <90s with deviation), schema validation on all inputs. Show in deck slide 7. | HIGH |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| COMP-01 | Phase 3 | ✅ Complete |
| COMP-02 | Phases 4–7 | ○ Rebuilding |
| COMP-03 | Phase 8 | ○ Planned |
| COMP-04 | Phase 8 | ○ Planned |
| COMP-05 | Phase 8 | ○ Planned |
| P1-01 through P3-03 | Phases 1–3 | ✅ Complete |
| F-01 through F-13 | Phase 4 | ○ Planned |
| T-01 through T-18 | Phase 5 | ○ Planned |
| A-01 through A-23 | Phase 6 | ○ Planned |
| U-01 through U-12 | Phase 7 | ○ Planned |
| D-01 through D-08 | Phase 8 | ○ Planned |

**Coverage:**
- Total requirements: 70
- Complete: 14 (20%)
- Planned: 56 (80%)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-08-17*
*Last updated: 2026-08-27 — ground-up rebuild planning*
