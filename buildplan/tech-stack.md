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
| **Human-in-the-loop** | 5 mandatory HITL gates (split approval, feeder hold, truck dispatch, sequence update, escalation) |
| **Edge case handling** | Stale data (30–60 min latency), berth conflicts, feeder departure slips, AYE peak congestion |
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
│   │   ├── decide.py          # LLM decides next action
│   │   ├── execute.py         # Execute tool call
│   │   ├── hitl.py            # Human approval gate
│   │   └── escalate.py        # Escalation logic
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── citos_tools.py     # CITOS read/write tools
│   │   ├── optetruck_tools.py # OptETruck tools
│   │   ├── feeder_tools.py    # Feeder vessel tools
│   │   ├── portnet_tools.py   # PORTNET tools
│   │   └── split_optimizer.py # ITT split computation
│   ├── state.py               # Agent state definition (TypedDict)
│   ├── llm.py                 # LLM provider abstraction
│   └── config.py              # YAML config loader
├── configs/
│   ├── pb-12-itt.yaml         # PB-12: ITT coordination
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
│   ├── main.py                # FastAPI app (agent endpoint)
│   └── schemas.py             # Request/response models
├── frontend/
│   ├── index.html             # Demo UI
│   ├── app.js                 # Agent interaction logic
│   └── style.css              # Styling
├── tests/
│   ├── test_agent.py          # Agent integration test
│   ├── test_tools.py          # Tool unit tests
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
  - name: citos_tuas
    type: terminal_os
    mock: mocks.citos_tuas
    capabilities: [yard_blocks, vessel_schedule, loading_sequence]
  - name: optetruck
    type: transport
    mock: mocks.optetruck
    capabilities: [truck_availability, routing, gps_tracking]
  - name: feeder
    type: vessel
    mock: mocks.feeder
    capabilities: [departure_window, capacity, hold_request]
  - name: portnet
    type: community
    mock: mocks.portnet
    capabilities: [inventory_sync, message_relay]

tools:
  - name: query_container_readiness
    systems: [citos_ppt]
    description: "Check which containers are ready for ITT transfer"
  - name: check_truck_capacity
    systems: [optetruck]
    description: "Query available prime movers and chassis"
  - name: check_sea_itt_capacity
    systems: [feeder, citos_tuas]
    description: "Check feeder vessel availability and Tuas berth"
  - name: compute_itt_split
    systems: []  # internal computation
    description: "Compute optimal road/sea split minimising total cost"
  - name: update_tuas_loading_sequence
    systems: [citos_tuas]
    description: "Update vessel loading sequence at Tuas"

hitl_gates:
  - trigger: split_computed
    action: require_approval
    label: "Approve ITT Split"
    timeout_minutes: 30
  - trigger: feeder_hold_request
    action: require_approval
    label: "Approve Feeder Hold Request"
    timeout_minutes: 15

cost_params:
  road_cost_per_trip: 150
  vessel_demurrage_per_hr: 2500
  feeder_charter_per_hr: 800
  yard_rehandle: 35
  staff_hourly: 50

constraints:
  lta_chassis: "1x 40ft (FEU) OR up to 2x 20ft (TEU) per prime mover"
  max_road_trips_per_wave: 20
  peak_hours: ["07:30-09:30", "17:30-19:30"]
  transit_off_peak_min: 45
  transit_peak_min: 95
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

## 11. Build Order (<1 Week)

| Day | Morning | Afternoon | Deliverable |
|-----|---------|-----------|------------|
| **1** | Project scaffold, LangGraph setup, LLM abstraction | Mock API server (all 5 systems) | FastAPI app with mock endpoints |
| **2** | Agent state definition, graph skeleton | Tool registration (all 5 systems) | Agent can read from all mocks |
| **3** | ITT split logic, cost computation | HITL gate nodes | Agent computes split, requests approval |
| **4** | Config system (YAML loading) | Edge cases (stale data, berth conflict) | Agent handles all Master Charter scenarios |
| **5** | Demo trace walkthrough | Web UI (real-time agent decisions) | Presentable demo |
| **6** | Testing, polish, bug fixes | Deploy to Railway/Render | Live demo URL |
| **7** | Buffer / presentation prep | Record demo video, practice pitch | Competition-ready |

---

## 12. Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Architecture** | AI Agent (medium agenticity) | Dynamic tool selection needed; not fully autonomous |
| **Framework** | LangGraph v1.2.11 | Provider-agnostic, HITL first-class, state checkpointing |
| **LLM** | Configurable (start with available key) | Provider abstraction for flexibility |
| **Backend** | FastAPI | Lightweight, async, Python-native |
| **Database** | None (in-memory) | Demo scope doesn't require persistence |
| **State** | Python dict + YAML configs | Simple, no infrastructure overhead |
| **Deployment** | Docker → free-tier (Railway/Render) | Zero cost, fast setup |
| **Generalisation** | YAML config per problem | Same agent core, different parameters |

**Total estimated cost to demo:** $0 infrastructure + $5–15 LLM calls = **under $20**
