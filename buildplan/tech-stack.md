# Tech Stack Selection Decision Report

**PSA Code Sprint — Agentic AI for Cross-Terminal ITT Coordination**  
**Date:** 2026-08-23  
**Audience:** Build team (developers + architect)

---

## 1. Requirements Analysis

### Business Scenario
Build a working product demo of an agentic AI system that coordinates multi-party inter-terminal transfer (ITT) operations at PSA Singapore. The flagship problem (PB-12) involves moving 120 containers from Pasir Panjang Terminal (PPT) to Tuas Port, optimising the road/sea transport split across 5 disconnected systems.

### Core Requirements

| Requirement | Detail |
|-------------|--------|
| **Agent capability** | Dynamically decide tool usage based on real-time conditions (traffic, berth conflicts, feeder availability, data staleness) |
| **Multi-system coordination** | Read/write across 5 mock PSA systems (CITOS×2, OptETruck, Feeder, PORTNET) |
| **Human-in-the-loop** | 5 mandatory HITL gates: (1) Split approval, (2) Truck dispatch, (3) Feeder hold request, (4) Loading sequence update, (5) Escalation to Duty Manager |
| **Escalation triggers** | 7 automatic escalation triggers with threshold checks (confidence, tidal tolerance, financial, data freshness, capacity, responsiveness, planner conflict) |
| **Confidence scoring** | Agent must output confidence score (0–1) per decision; triggers escalation when < 0.85 |
| **Edge case handling** | Stale data (30–60 min latency), berth conflicts, feeder departure slips, AYE peak congestion |
| **Event ingestion** | Webhook endpoint to receive `ITT_COORDINATION_REQUEST` events from CITOS |
| **Provider flexibility** | Should not be locked to a single LLM vendor — ability to swap models/providers |
| **Generalisation** | Same agent core, different configs for 7 Cluster C2 problems |
| **Demo deployment** | Must be deployable and presentable within <1 week |

### Hard Constraints

| Constraint | Detail |
|------------|--------|
| **Timeline** | <1 week to working demo |
| **Infrastructure** | Starting from zero (no cloud accounts, no CI/CD) |
| **API access** | Mock APIs only — no real PSA system integration |
| **Budget** | Minimal — free-tier hosting, LLM costs under $20 for demo |
| **Team** | Assumed small (1–3 developers), variable AI experience |

### Performance Requirements

| Metric | Target |
|--------|--------|
| Response latency | 2–30 seconds per agent step (acceptable for HITL demo) |
| Concurrent sessions | 1 (single demo instance) |
| Data volume | Mock data only — no production data scale |
| LLM calls per incident | ~10–20 calls (per Master Charter 17-step trace) |

---

## 2. Architecture Paradigm Selection

### Decision: AI Agent (Medium Agenticity)

This is **not** a traditional service and **not** a fully autonomous Deep Agent. It sits in the middle:

```
┌─────────────────────────────────────────────────────────────────┐
│  Traditional     Router       Workflow     State Machine    Agent│
│  (No LLM)       (Routing)    (Workflow)    (State Machine) (Auto)│
├─────────────────────────────────────────────────────────────────┤
│  Code fully    LLM makes     Multi-step    Loops +         Autono- │
│  controls      single        fixed path    conditions      mous    │
│                routing       predefined    until met       planning│
│                decisions     steps                         & exec  │
├─────────────────────────────────────────────────────────────────┤
│  Low ◀─────────────────────────────────────────────────────▶ High│
│                                                                 │
│                          ▲                                      │
│                    WE ARE HERE                                   │
│              (Medium agenticity)                                │
└─────────────────────────────────────────────────────────────────┘
```

### Why Agent (not Workflow)

| Criterion | Assessment |
|-----------|-----------|
| Steps predefinable? | Partially — the coordination flow is known, but the agent must dynamically choose tools based on conditions |
| 100% determinism? | No — split optimisation and escalation decisions require reasoning |
| Long-term planning? | No — max ~17 steps per incident |
| Latency requirement? | Seconds acceptable (HITL already adds minutes) |
| Error consequences? | HIGH — requires strict HITL gates (designed in 03-02) |

The agent must handle branching logic that would make a fixed workflow unwieldy:
- Skip sea ITT if feeder unavailable
- Escalate if PPT data is stale (>20 min old)
- Re-compute split if berth conflict detected mid-operation
- Route to different tools based on which systems are responsive

### Why NOT Deep Agent

- <1 week timeline — Deep Agent requires planning tools, sub-agents, file system memory
- Problem scope is contained — ~17 steps, 5 systems, clear success criteria
- Demo audience cares about the concept, not production-grade autonomy

### Why NOT Traditional Service

- The whole point of the competition is demonstrating agentic AI
- Fixed rules can't handle the dynamic multi-party coordination
- Judges expect LLM-driven decision-making

---

## 3. Database Decision

### Short Answer: **No database for the demo**

| Concern | Assessment |
|---------|-----------|
| **State persistence** | Not needed — demo runs in-memory, resets between runs |
| **Audit trail** | Nice-to-have, but agent logs (to console/file) are sufficient |
| **Concurrent access** | Single demo instance — no concurrency |
| **Data volume** | Mock data only — fits in Python dicts |
| **Recovery** | Demo can be restarted in seconds |

### What to use instead

| Need | Solution |
|------|----------|
| Agent state during execution | Python `dict` or `dataclass` in memory |
| Configuration (per problem) | YAML files on disk |
| Demo logs / audit trail | Structured logging to `stdout` + optional JSON log file |
| Mock data | Python dicts / JSON files loaded at startup |

### When you WOULD need a database

If this moved beyond demo to production:
- **PostgreSQL** — for audit trails, multi-user sessions, persistent state
- **Redis** — for real-time state caching across agent restarts
- **SQLite** — lightweight option for single-server deployment

But for the competition demo: **keep it simple. In-memory state + YAML configs + log files.**

---

## 4. Provider-Agnostic Design

### Why provider-agnostic matters

| Reason | Detail |
|--------|--------|
| **Competition flexibility** | Judges may have preferences; team may want to demo with different models |
| **Cost optimisation** | Different providers have different pricing; swap for cost savings |
| **Resilience** | If one provider is down, fall back to another |
| **Future-proofing** | Don't bet the demo on a single vendor's API stability |
| **Generalisation** | Some Cluster C2 problems may benefit from different model strengths |

### Provider landscape (2026)

| Provider | Best Model | Price (Input/Output per MTok) | Strengths | Context Window |
|----------|-----------|-------------------------------|-----------|---------------|
| **Anthropic** | Claude Sonnet 4 | $3 / $15 | Reasoning, safety, long context, tool use | 1M tokens |
| **Anthropic** | Claude Haiku 4.5 | $1 / $5 | Fast, cheap, good enough for simple tools | 200K tokens |
| **OpenAI** | GPT-4o | $2.50 / $10 | Mature ecosystem, vision, function calling | 128K tokens |
| **Google** | Gemini 2.0 Flash | $0.10 / $0.40 | Extremely cheap, multimodal | 1M tokens |
| **DeepSeek** | DeepSeek V3 | $0.27 / $1.10 | Very cheap, strong coding | 128K tokens |

### Recommended approach: LLM abstraction layer

```python
# llm_provider.py — abstract the LLM call behind a common interface

from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict] = None) -> dict:
        """Unified chat interface across providers."""
        pass

class AnthropicProvider(LLMProvider):
    def chat(self, messages, tools=None):
        # Claude API call
        pass

class OpenAIProvider(LLMProvider):
    def chat(self, messages, tools=None):
        # OpenAI API call
        pass

class GeminiProvider(LLMProvider):
    def chat(self, messages, tools=None):
        # Gemini API call
        pass
```

**Config-driven provider selection:**
```yaml
# config.yaml
llm:
  provider: anthropic          # or openai, gemini, deepseek
  model: claude-sonnet-4       # or gpt-4o, gemini-2.0-flash
  api_key_env: ANTHROPIC_API_KEY
  fallback_provider: openai    # optional fallback
  fallback_model: gpt-4o
```

**For the demo:** Start with one provider (whichever the team has API keys for). The abstraction layer means switching is a config change, not a code rewrite.

---

## 5. Framework Evaluation

### Candidates

| Framework | Positioning | Provider Support | HITL Support | State Management | Learning Curve |
|-----------|-------------|-----------------|-------------|-----------------|---------------|
| **Claude Agent SDK** | Anthropic-native | Anthropic only | Built-in | Simple | Low |
| **LangGraph** | Provider-agnostic orchestration | Any (via LangChain) | First-class | Checkpointing, persistence | Medium |
| **OpenAI Agents SDK** | OpenAI-native | OpenAI only | Built-in | Simple | Low |
| **Raw LLM API + custom code** | DIY | Any | Build yourself | Build yourself | Low-Medium |

### Quantified Evaluation

| Dimension (Weight) | Claude Agent SDK | LangGraph | OpenAI Agents SDK | Raw API + Custom |
|--------------------|-----------------|-----------|-------------------|-----------------|
| **Provider flexibility** (20%) | 3 — Anthropic only | 9 — Any provider | 3 — OpenAI only | 10 — Any provider |
| **Implementation speed** (20%) | 9 — Minimal boilerplate | 6 — More setup | 8 — Lightweight | 5 — Build everything |
| **HITL support** (15%) | 8 — Built-in | 9 — First-class concept | 7 — Built-in | 4 — Build yourself |
| **State management** (15%) | 5 — In-memory only | 9 — Checkpointing, persistence | 5 — In-memory only | 3 — Build yourself |
| **Demo suitability** (15%) | 8 — Fast to demo | 7 — More overhead | 8 — Fast to demo | 6 — More work |
| **Generalisation potential** (15%) | 5 — Single provider lock-in | 9 — Config-driven multi-problem | 5 — Single provider lock-in | 8 — Full control |
| **TOTAL** | **6.35** | **7.85** | **5.95** | **6.35** |

### Winner: **LangGraph**

Despite the steeper learning curve, LangGraph wins because:
1. **Provider-agnostic** — matches the "versatile agent for all providers" requirement
2. **HITL is first-class** — built-in human approval nodes, exactly what PB-12 needs
3. **State checkpointing** — agent can pause/resume (useful for demo edge cases)
4. **Generalisation** — same graph structure, different configs per problem
5. **Observable** — native LangSmith integration for tracing

**The extra 1–2 days of setup are worth it** for a cleaner, more extensible demo.

### Why NOT Claude Agent SDK for this project

It's excellent for Anthropic-native projects, but:
- Locks you to Claude — can't demo with GPT-4o or Gemini
- No built-in state persistence
- Less flexibility for the generalisation layer
- If Anthropic API has issues during demo day, no fallback

---

## 6. Recommended Tech Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    RECOMMENDED TECH STACK                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Language:        Python 3.11+                                   │
│  Agent Framework: LangGraph v1.2.11                             │
│  LLM Provider:    Configurable (start with available API key)   │
│  Default Model:   Claude Sonnet 4 or GPT-4o (team choice)       │
│  Backend:         FastAPI + uvicorn                              │
│  Mock APIs:       FastAPI sub-routers (5 mock services)          │
│  State:           In-memory (dict/dataclass) — no database      │
│  Config:          YAML files per problem                         │
│  Observability:   LangSmith (free tier) or Langfuse (self-host) │
│  Frontend:        Simple web UI (HTML/JS) or Streamlit           │
│  Deployment:      Docker → Railway / Render / Fly.io (free tier) │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Full dependency list

```
# requirements.txt
langgraph>=1.2.11
langchain-core>=0.3.0
langchain-anthropic>=0.3.0      # if using Claude
langchain-openai>=0.3.0         # if using OpenAI
langchain-google-genai>=2.0.0   # if using Gemini
fastapi>=0.115.0
uvicorn>=0.34.0
pydantic>=2.0.0
pyyaml>=6.0
httpx>=0.28.0                   # for mock API calls
langsmith>=0.8.0                # optional: tracing
```

### Why no database

| Concern | Solution without DB |
|---------|-------------------|
| Agent state | In-memory dict — resets per demo run |
| Problem configs | YAML files on disk |
| Audit trail | Structured logging to stdout + JSON log file |
| Mock data | Python dicts loaded at startup |
| Demo replay | Log file can be replayed for presentation |

**Total infrastructure cost: $0** (free-tier hosting + in-memory state)

---

## 7. Project Structure

```
psa-agent/
├── agent/
│   ├── __init__.py
│   ├── core.py                # LangGraph graph definition
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── ingest.py          # Read from all 5 systems
│   │   ├── decide.py          # LLM decides next action + confidence score
│   │   ├── execute.py         # Execute tool call
│   │   ├── hitl.py            # 5 HITL gate nodes (see Section 8)
│   │   ├── escalate.py        # 7 escalation trigger checks
│   │   └── confidence.py      # Confidence scoring + threshold check
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── webhook.py         # Event ingestion endpoint (ITT_COORDINATION_REQUEST)
│   │   ├── citos_tools.py     # Tool 1: query_container_readiness
│   │   ├── optetruck_tools.py # Tool 2: check_road_itt_capacity
│   │   ├── feeder_tools.py    # Tool 3: check_sea_itt_capacity
│   │   ├── portnet_tools.py   # PORTNET inventory sync
│   │   ├── split_optimizer.py # Tool 4: compute_itt_split
│   │   └── loading_seq.py     # Tool 5: update_tuas_loading_sequence
│   ├── state.py               # Agent state definition (TypedDict)
│   ├── llm.py                 # LLM provider abstraction
│   ├── config.py              # YAML config loader
│   └── edge_cases.py          # Stale data detection, berth conflict simulation
├── configs/
│   ├── pb-12-itt.yaml         # PB-12: ITT coordination (full config)
│   ├── pb-07-yard.yaml        # Placeholder: yard re-handle
│   ├── pb-09-gate.yaml        # Placeholder: gate scheduling
│   └── default.yaml           # Shared defaults
├── mocks/
│   ├── __init__.py
│   ├── citos_ppt.py           # PPT CITOS mock
│   ├── citos_tuas.py          # Tuas CITOS mock
│   ├── optetruck.py           # OptETruck mock
│   ├── feeder.py              # Feeder operator mock
│   ├── portnet.py             # PORTNET mock
│   └── app.py                 # FastAPI mock server
├── api/
│   ├── __init__.py
│   ├── main.py                # FastAPI app (agent + webhook + mocks)
│   └── schemas.py             # Request/response models
├── frontend/
│   ├── index.html             # Demo UI
│   ├── app.js                 # Agent interaction logic (SSE)
│   └── style.css              # Styling
├── observability/
│   ├── trace.py               # LangSmith/Langfuse trace wrapper
│   └── deviation_logger.py    # Deviation logging (plan changes)
├── tests/
│   ├── test_agent.py          # Agent integration test
│   ├── test_tools.py          # Tool unit tests
│   ├── test_escalation.py     # Escalation trigger tests
│   ├── test_hitl.py           # HITL gate tests
│   └── test_mocks.py          # Mock API tests
├── logs/                      # Structured logs (demo audit trail)
├── docker-compose.yml         # Local dev (agent + mocks)
├── Dockerfile                 # Production container
├── requirements.txt
├── .env.example               # API key template
└── README.md
```

---

## 8. Generalisation Architecture

### "Same agent, different configs" approach

The agent core (LangGraph graph) is **identical** for all 7 Cluster C2 problems. Only the config changes:

```yaml
# configs/pb-12-itt.yaml — PB-12: Multi-Party ITT Coordination
problem:
  id: PB-12
  name: "Multi-Party ITT Coordination Failure"
  sector: "Multimodal Logistics"
  description: "Move 120 containers PPT→Tuas, optimise road/sea split"

systems:
  - name: citos_ppt
    type: terminal_os
    mock: mocks.citos_ppt
    capabilities: [container_readiness, yard_status, customs_hold]
    data_freshness_max_min: 30   # escalation if data age > 30 min
  - name: citos_tuas
    type: terminal_os
    mock: mocks.citos_tuas
    capabilities: [yard_blocks, vessel_schedule, loading_sequence]
    data_freshness_max_min: 30
  - name: optetruck
    type: transport
    mock: mocks.optetruck
    capabilities: [truck_availability, routing, gps_tracking]
  - name: feeder
    type: vessel
    mock: mocks.feeder
    capabilities: [departure_window, capacity, hold_request]
    response_timeout_min: 15     # escalation if no response in 15 min
  - name: portnet
    type: community
    mock: mocks.portnet
    capabilities: [inventory_sync, message_relay]

# --- 6 Tools (matches Master Charter §Tools) ---
tools:
  - name: query_container_readiness
    systems: [citos_ppt]
    description: "Check which containers are ready for ITT transfer"
    tool_id: tool_1
  - name: check_road_itt_capacity
    systems: [optetruck]
    description: "Query available prime movers, chassis, transit time, road conditions"
    tool_id: tool_2
  - name: check_sea_itt_capacity
    systems: [feeder, citos_tuas]
    description: "Check feeder vessel availability and Tuas berth capacity"
    tool_id: tool_3
  - name: compute_itt_split
    systems: []  # internal computation
    description: "Compute optimal road/sea split minimising total cost subject to constraints"
    tool_id: tool_4
  - name: update_tuas_loading_sequence
    systems: [citos_tuas]
    description: "Update vessel loading sequence at Tuas with ITT arrival slots"
    tool_id: tool_5
  - name: receive_webhook
    systems: [citos_ppt]
    description: "Webhook endpoint for ITT_COORDINATION_REQUEST events"
    tool_id: trigger
    type: event_trigger

# --- 5 Mandatory HITL Gates (matches Master Charter §HITL) ---
hitl_gates:
  - gate_id: hitl_1
    trigger: split_computed
    action: require_approval
    label: "Approve ITT Split"
    description: "Agent has computed optimal road/sea split — requires ITT coordinator approval before committing"
    timeout_minutes: 30
    timeout_action: escalate_to_duty_manager
  - gate_id: hitl_2
    trigger: truck_dispatch_ready
    action: require_approval
    label: "Approve Truck Dispatch"
    description: "Agent is ready to dispatch trucks via OptETruck — requires approval"
    timeout_minutes: 15
    timeout_action: cancel_dispatch
  - gate_id: hitl_3
    trigger: feeder_hold_request
    action: require_approval
    label: "Approve Feeder Hold Request"
    description: "Agent requests feeder operator to hold departure — commercial decision requiring human approval"
    timeout_minutes: 15
    timeout_action: escalate_to_duty_manager
  - gate_id: hitl_4
    trigger: sequence_update_ready
    action: require_approval
    label: "Approve Loading Sequence Update"
    description: "Agent wants to update Tuas vessel loading sequence — requires yard planner approval"
    timeout_minutes: 10
    timeout_action: hold_current_sequence
  - gate_id: hitl_5
    trigger: escalation_triggered
    action: escalate_to_duty_manager
    label: "Escalation to Duty Manager"
    description: "Agent has detected an escalation condition — duty manager must intervene"
    timeout_minutes: 30
    timeout_action: halt_workflow

# --- 7 Escalation Triggers (matches 03-02-autonomy-level.md §Step 5) ---
escalation_triggers:
  - trigger_id: esc_1
    name: "Low model confidence"
    condition: "confidence_score < 0.85"
    threshold: 0.85
    rationale: "Agent is uncertain about optimal split — requires senior judgment"
  - trigger_id: esc_2
    name: "Feeder hold exceeds downstream tolerance"
    condition: "feeder_hold_hours > 1.5"
    threshold: 1.5
    rationale: "Feeder may miss downstream tidal window — commercial risk escalation"
  - trigger_id: esc_3
    name: "Financial recovery cost exceeds limit"
    condition: "recommended_action_cost > 10000"
    threshold: 10000
    rationale: "High single-action cost — requires duty manager sign-off"
  - trigger_id: esc_4
    name: "Data latency exceeds freshness window"
    condition: "max_data_age_min > 30"
    threshold: 30
    rationale: "Agent operating on stale cross-terminal data — human must verify current state"
  - trigger_id: esc_5
    name: "Road ITT capacity below threshold"
    condition: "available_trucks < (required_trucks * 0.6)"
    threshold: 0.6
    rationale: "Insufficient road capacity — requires emergency sea ITT coordination"
  - trigger_id: esc_6
    name: "Feeder operator unresponsive"
    condition: "feeder_response_time_min > 15"
    threshold: 15
    rationale: "Cannot confirm feeder availability — human must escalate via phone"
  - trigger_id: esc_7
    name: "Conflict between PPT and Tuas planners"
    condition: "planner_recommendations_conflict == true"
    threshold: null
    rationale: "Cross-terminal disagreement — requires duty manager arbitration"

# --- Confidence Scoring ---
confidence:
  enabled: true
  threshold: 0.85
  method: "llm_self_assessment"  # LLM outputs confidence score per decision
  on_below_threshold: "escalate"  # triggers esc_1

# --- Cost Parameters (matches Master Charter §ROI) ---
cost_params:
  road_cost_per_trip: 150
  vessel_demurrage_per_hr: 2500
  feeder_charter_per_hr: 800
  sea_terminal_handling: 35       # per lift-move
  yard_rehandle: 35
  staff_hourly: 50
  missed_connection_per_container: 150

# --- Constraints (matches Master Charter §constraints) ---
constraints:
  lta_chassis: "1x 40ft (FEU) OR up to 2x 20ft (TEU) per prime mover"
  max_road_trips_per_wave: 20
  peak_hours: ["07:30-09:30", "17:30-19:30"]
  transit_off_peak_min: 45
  transit_peak_min: 95
  total_containers: 120
  container_mix: "40x 40ft (FEU) + 80x 20ft (TEU)"
  baseline_trips: 80              # 40 FEU trips + 40 TEU paired trips
  vessel_departure: "20:00"
  itt_arrival_deadline: "18:00"

# --- Edge Cases (demo injection points) ---
edge_cases:
  - case_id: ec_1
    name: "Feeder berth conflict"
    inject_at_step: 8
    description: "PORTNET reports feeder berth conflict — departure delayed to 1600"
    agent_response: "Detect deviation, re-compute split (80/40 → 100/20), request re-approval"
  - case_id: ec_2
    name: "Data staleness"
    inject_at_step: 2
    description: "PPT CITOS data is 25 min old — containers may not be ready"
    agent_response: "Trigger escalation, present stale-data alert to ITT coordinator"
```

### Adding a new problem

1. Duplicate an existing YAML config
2. Change `problem`, `systems`, `tools`, `cost_params`, `constraints`
3. If new tool logic is needed, add a tool file in `agent/tools/`
4. Agent core (`agent/core.py`) stays **unchanged**

### Example: PB-07 (Yard Re-Handle) config differences

```yaml
# Only the differences from PB-12 are shown
problem:
  id: PB-07
  name: "Yard Re-Handle Cascade"
  sector: "Container Yard & Internal Transport"

systems:
  - name: citos_yard
    type: terminal_os
    capabilities: [block_occupancy, rehandle_queue, equipment_status]
  - name: crane_ctrl
    type: equipment
    capabilities: [crane_availability, job_queue]

tools:
  - name: query_rehandle_queue
  - name: optimise_block_placement
  - name: dispatch_crane

cost_params:
  rehandle_cost: 35
  crane_hourly: 200
  delay_cost_per_hr: 500
```

---

## 9. LLM Cost Estimate

### Per-incident token usage (PB-12)

| Step | Input Tokens | Output Tokens | Calls |
|------|-------------|--------------|-------|
| Ingest (5 systems) | ~3,000 | ~500 | 1 |
| Decide (tool selection) | ~2,000 | ~200 | 5–8 |
| Execute (tool results) | ~4,000 | ~300 | 5–8 |
| HITL decision | ~1,000 | ~100 | 1–2 |
| Escalation handling | ~1,500 | ~200 | 0–2 |
| **Total per incident** | **~15,000** | **~3,000** | **~15** |

### Cost per provider (per incident)

| Provider/Model | Input Cost | Output Cost | Total per Incident |
|---------------|-----------|------------|-------------------|
| Claude Sonnet 4 | $0.045 | $0.045 | **$0.09** |
| Claude Haiku 4.5 | $0.015 | $0.015 | **$0.03** |
| GPT-4o | $0.038 | $0.030 | **$0.07** |
| Gemini 2.0 Flash | $0.002 | $0.001 | **$0.003** |
| DeepSeek V3 | $0.004 | $0.003 | **$0.007** |

### Demo budget (100 test runs)

| Provider | Cost for 100 runs |
|----------|-------------------|
| Claude Sonnet 4 | ~$9 |
| GPT-4o | ~$7 |
| Gemini 2.0 Flash | ~$0.30 |
| DeepSeek V3 | ~$0.70 |

**Recommendation:** Use Claude Sonnet 4 for quality, or Gemini 2.0 Flash for near-zero cost. The abstraction layer makes switching trivial.

---

## 10. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **API downtime during demo** | Low | Critical | Provider abstraction → fallback to second provider |
| **LLM hallucination in tool calls** | Medium | High | Input validation on all tool outputs; HITL gates catch bad decisions |
| **Mock APIs unrealistic** | Medium | Medium | Ground mock data in actual PSA operational parameters (from Phase 1 research) |
| **Demo doesn't impress judges** | Medium | High | Focus on edge case handling (stale data, berth conflict) — that's the drama |
| **Over-engineering kills timeline** | High | Critical | Strict scope: PB-12 only, no multi-agent, no database, no fancy UI |
| **LangGraph learning curve** | Medium | Medium | Start with simple linear graph, add branches incrementally |
| **Cost overrun on LLM calls** | Low | Low | Cap at 100 demo runs; use Haiku/Gemini for testing, Sonnet for final demo |

---

## 11. Observability & Trace Tracking

### LangGraph + LangSmith Integration

LangGraph has **native LangSmith integration** — every graph execution is automatically traced.

| Capability | What's Captured | How |
|-----------|----------------|-----|
| **Graph execution trace** | Every node visit, state transition, edge taken | Auto-instrumented by LangGraph |
| **Tool call logging** | Each tool invocation: input params, output, latency | Logged per tool call |
| **LLM interaction logging** | Full prompt + completion + token usage per call | Logged per LLM call |
| **State snapshots** | Agent state at each node (checkpointing) | Built into LangGraph state |
| **Confidence scores** | Agent confidence per decision | Custom field in agent state |
| **HITL gate events** | Approval/rejection/modification with timestamps | Custom logging in hitl.py |
| **Escalation events** | Which trigger fired, threshold vs actual, resolution | Custom logging in escalate.py |
| **Deviation logging** | When agent deviates from original plan and why | Custom: deviation_logger.py |
| **Cost tracking** | Token usage per call, aggregated per run | LangSmith dashboard |

### LangSmith Setup

```python
# In agent/core.py — enable tracing
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "psa-code-sprint"
```

**Free tier:** 5K traces/month — sufficient for ~100 demo runs (~15 traces each = 1,500 traces).

### Langfuse Alternative (Self-Hosted)

If you don't want LangSmith vendor dependency:

```bash
# docker-compose.yml addition
langfuse:
  image: langfuse/langfuse:latest
  ports:
    - "3000:3000"
  environment:
    - DATABASE_URL=sqlite:///langfuse.db
    - NEXTAUTH_SECRET=your-secret
```

```python
# In agent/core.py — use Langfuse instead
from langfuse.callback import CallbackHandler
handler = CallbackHandler(
    public_key="your-key",
    secret_key="your-secret",
    host="http://localhost:3000"
)
# Pass handler to LangGraph .invoke() or .stream()
```

### Custom Deviation Logger

```python
# observability/deviation_logger.py
import json
from datetime import datetime

class DeviationLogger:
    """Logs when agent deviates from original plan — required by Master Charter §7."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir

    def log_deviation(self, run_id: str, step: int, original_plan: str,
                      actual_action: str, reason: str):
        entry = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "original_plan": original_plan,
            "actual_action": actual_action,
            "reason": reason,
            "type": "deviation"
        }
        with open(f"{self.log_dir}/deviations.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_escalation(self, run_id: str, trigger_id: str, threshold: float,
                       actual: float, resolution: str):
        entry = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "trigger_id": trigger_id,
            "threshold": threshold,
            "actual": actual,
            "resolution": resolution,
            "type": "escalation"
        }
        with open(f"{self.log_dir}/escalations.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_hitl(self, run_id: str, gate_id: str, action: str,
                 decision: str, response_time_sec: float):
        entry = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "gate_id": gate_id,
            "action": action,
            "decision": decision,
            "response_time_sec": response_time_sec,
            "type": "hitl"
        }
        with open(f"{self.log_dir}/hitl_events.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")
```

### Trace Output Example (LangSmith Dashboard)

```
Run: demo-2026-08-23-001
├── [T+0.0s] node: ingest → Read from CITOS_PPT (2.1s, 1,200 tokens)
├── [T+2.1s] node: ingest → Read from OptETruck (1.8s, 800 tokens)
├── [T+3.9s] node: ingest → Read from Feeder (1.5s, 600 tokens)
├── [T+5.4s] node: decide → LLM call: "query_container_readiness" (3.2s, 2,100 tokens, confidence: 0.92)
├── [T+8.6s] node: execute → tool_1 output: 120 containers ready (0.3s)
├── [T+8.9s] node: decide → LLM call: "check_road_itt_capacity" (2.8s, 1,800 tokens, confidence: 0.88)
├── [T+11.7s] node: execute → tool_2 output: 20 trucks, 90 min transit (0.4s)
├── [T+12.1s] node: decide → LLM call: "check_sea_itt_capacity" (2.5s, 1,600 tokens, confidence: 0.90)
├── [T+14.6s] node: execute → tool_3 output: feeder at 1400, 200 TEU (0.3s)
├── [T+14.9s] node: decide → LLM call: "compute_itt_split" (4.1s, 3,200 tokens, confidence: 0.87)
├── [T+19.0s] node: execute → tool_4 output: 80 road / 40 sea, $10,400 (0.2s)
├── [T+19.2s] node: hitl_1 → WAITING: "Approve ITT Split" (awaiting human)
│   └── [T+45.0s] HITL DECISION: APPROVED (25.8s response time)
├── [T+45.0s] node: decide → LLM call: "dispatch trucks" (2.0s, 1,400 tokens, confidence: 0.91)
├── [T+47.0s] node: hitl_2 → WAITING: "Approve Truck Dispatch"
│   └── [T+52.0s] HITL DECISION: APPROVED (5.0s response time)
├── [T+52.0s] node: execute → OptETruck dispatch (1.2s)
├── [T+53.2s] node: hitl_3 → WAITING: "Approve Feeder Hold Request"
│   └── [T+60.0s] HITL DECISION: APPROVED (6.8s response time)
├── [T+60.0s] node: execute → Feeder hold request sent (0.8s)
├── ⚠️ [T+81.0s] DEVIATION: Feeder berth conflict detected (step 8)
│   └── Agent re-computes: 80/40 → 100/20 split
├── [T+81.0s] node: hitl_4 → WAITING: "Emergency Re-Split Approval"
│   └── [T+88.0s] HITL DECISION: APPROVED (7.0s response time)
├── [T+88.0s] node: execute → Updated truck dispatch (1.0s)
├── [T+89.0s] node: execute → Updated Tuas loading sequence (0.9s)
└── [T+89.9s] node: complete → Incident resolved, deviation logged

Total: 89.9s wall time | ~18,000 input tokens | ~3,500 output tokens | ~$0.10 (Claude Sonnet 4)
```

---

## 12. Build Order (<1 Week)

| Day | Morning | Afternoon | Deliverable |
|-----|---------|-----------|------------|
| **1** | Project scaffold, LangGraph setup, LLM abstraction, webhook endpoint | Mock API server (all 5 systems with realistic data) | FastAPI app with mock endpoints + webhook |
| **2** | Agent state definition, graph skeleton | Tool registration (all 6 tools: 5 + webhook) | Agent can read from all mocks |
| **3** | ITT split logic, cost computation | All 5 HITL gate nodes with timeout logic | Agent computes split, requests approval at each gate |
| **4** | 7 escalation trigger checks, confidence scoring | Edge cases: stale data detection, berth conflict simulation | Agent handles all Master Charter scenarios |
| **5** | Deviation logger, LangSmith tracing setup | Web UI (real-time agent decisions via SSE) | Presentable demo with trace dashboard |
| **6** | End-to-end testing (happy path + edge cases) | Deploy to Railway/Render | Live demo URL |
| **7** | Buffer / bug fixes | Record demo video, practice pitch | Competition-ready |

### Demo Script Checklist (per Master Charter §7)

- [ ] Webhook receives `ITT_COORDINATION_REQUEST` → agent starts
- [ ] Agent queries all 5 systems (ingest node)
- [ ] Agent computes optimal split (80 road / 40 sea = $10,400)
- [ ] HITL Gate 1: Split approval → APPROVED
- [ ] HITL Gate 2: Truck dispatch → APPROVED
- [ ] HITL Gate 3: Feeder hold → APPROVED
- [ ] **Edge case injection:** Feeder berth conflict at Step 8
- [ ] Agent detects deviation, re-computes (100/20 split)
- [ ] HITL Gate 4: Emergency re-split → APPROVED
- [ ] HITL Gate 5: Loading sequence update → APPROVED
- [ ] Agent logs deviation with reason
- [ ] Total resolution time < 30 seconds wall time
- [ ] All 7 escalation triggers tested (unit tests)
- [ ] LangSmith trace shows full execution graph
- [ ] Confidence scores logged for every decision

---

## 13. Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Architecture** | AI Agent (medium agenticity) | Dynamic tool selection needed; not fully autonomous |
| **Framework** | LangGraph v1.2.11 | Provider-agnostic, HITL first-class, state checkpointing |
| **LLM** | Configurable (start with available key) | Provider abstraction for flexibility |
| **Backend** | FastAPI | Lightweight, async, Python-native |
| **Database** | None (in-memory) | Demo scope doesn't require persistence |
| **State** | Python dict + YAML configs | Simple, no infrastructure overhead |
| **Observability** | LangSmith (free tier) or Langfuse (self-hosted) | Full trace of graph execution, tool calls, HITL events |
| **Deployment** | Docker → free-tier (Railboard/Render) | Zero cost, fast setup |
| **Generalisation** | YAML config per problem | Same agent core, different parameters |

### Requirements Coverage (Post-Update)

| Requirement | Status |
|-------------|--------|
| 6 tools (incl. webhook) | ✅ All defined in YAML config |
| 5 HITL gates | ✅ All with timeout + escalation logic |
| 7 escalation triggers | ✅ All with threshold conditions |
| Confidence scoring | ✅ LLM self-assessment, threshold 0.85 |
| Edge cases (stale data, berth conflict) | ✅ Injected at specific steps |
| Deviation logging | ✅ Custom logger + LangSmith traces |
| Provider flexibility | ✅ LLM abstraction layer |
| Generalisation (7 problems) | ✅ YAML config per problem |

**Total estimated cost to demo:** $0 infrastructure + $5–15 LLM calls = **under $20**
