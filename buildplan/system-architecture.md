# PSA Nexus — System Architecture

## Overview

PSA Nexus is a LangGraph-based agentic multi-party coordination platform. Think of it as a **virtual human equipped with tools** — it receives a problem (ITT coordination request), reasons about what to do, calls the right tools, asks for human approval on important decisions, and monitors for deviations. The system follows a state graph pattern: a webhook receives events, the LangGraph StateGraph processes them through agent reasoning, tool execution, HITL gates, and monitoring, while an SSE bridge streams real-time updates to a vanilla HTML/JS browser UI.

---

## Core Concepts (What Everything Is)

### FastAPI — The Server

FastAPI is a Python web framework that creates an API server. It listens for HTTP requests and responds with data.

**Analogy:** Think of a restaurant. FastAPI is the kitchen. HTTP requests are orders coming in from customers. FastAPI processes the order and sends back a plate (JSON response).

In this project, FastAPI IS the API. It exposes endpoints that:
- The browser UI calls (to run demos, approve HITL, inject edge cases)
- External systems could call (to trigger ITT coordination)
- The SSE stream is served from (to push live updates to the browser)

### SSE (Server-Sent Events) — Live Updates

SSE is a way for the server to push live updates to the browser WITHOUT the browser having to keep asking.

**Without SSE (polling):** Browser asks "any updates?" → server says "no" → browser asks again 2 seconds later → server says "no" → browser asks again... (wasteful).

**With SSE:** Browser opens one connection → server pushes updates whenever it has them → connection stays open.

In this project: when the LangGraph agent is thinking, calling tools, or waiting for HITL approval, it publishes events to the SSE broadcaster. The browser's `EventSource` receives them instantly and renders them in the bento UI (agent reasoning appears as typewriter text, tool calls appear in the log, HITL cards appear in the approval section).

### LangGraph — The Agent Brain

LangGraph is a Python library for building **state machines** (also called graphs) that power AI agents.

**Without LangGraph**, you'd manually write:
```python
result = await agent_reason(state)
if result.tool_calls:
    result = await execute_tools(result)
if needs_approval:
    result = await wait_for_human(result)
# ... manually manage every state transition
```

This works for simple cases but breaks when:
- The agent needs to loop (reason → tools → reason → tools → ...)
- You need to pause and resume (HITL approval)
- You need to save state between steps (crash recovery)
- You need conditional routing (if confidence < 0.85 → HITL, else → continue)

**LangGraph gives you:**
- **StateGraph** — a directed graph of nodes (agent, tools, hitl, monitor) with edges (conditional routing based on state)
- **MemorySaver** — saves state at every step to a checkpoint (thread_id = run_id). If the server crashes, you can resume from the last checkpoint
- **interrupt()** — pause the graph at any node, return control to the caller. Used for HITL: the graph pauses, the frontend shows an approval card, user clicks approve, `Command(resume=)` continues the graph from where it left off
- **Conditional routing** — after the agent node, the graph decides: call tools? show HITL card? go to monitor? end? Based on what's in the state

**In this project:**
- The graph has 4 nodes: agent, tools, hitl, monitor
- Agent node calls the LLM, which decides what tools to call
- Tool node executes those tools, returns results to agent
- HITL node uses `interrupt()` to pause for human approval
- Monitor node re-checks for deviations after dispatch
- `MemorySaver(thread_id=run_id)` saves all state so you can resume after HITL approval

**The alternative** (raw Python) would require you to manually implement state management, checkpointing, interrupt/resume, and conditional routing. LangGraph does all of this out of the box.

### How Agentic AI Replaces "Write Code"

Traditional automation: a human writes code that says "if X, do Y." The code is fixed — it can't adapt to new situations.

Agentic AI: the LLM (large language model) IS the code. Instead of a human writing "if container_count > 100, call tool T1," the LLM reads the problem, reasons about what tools are available, and decides what to call. It can adapt to:
- Different problem types (PB-12 ITT vs PB-01 Berth Delay)
- Unexpected situations (feeder berth conflict → re-compute split)
- Missing data (weight unknown → ask operator)

The tools (get_itt_candidates, compute_itt_split, etc.) are still written by humans. But the AGENT that decides which tools to call and when — that's the LLM. It's like giving a human a toolbox and a problem description, and letting them figure out the solution.

---

## Full System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PSA NEXUS — SYSTEM ARCHITECTURE                      │
│                    LangGraph StateGraph + FastAPI + SSE UI                  │
└─────────────────────────────────────────────────────────────────────────────┘

                          ┌─────────────────────┐
                          │   EXTERNAL TRIGGER   │
                          │  (Webhook / Demo UI) │
                          └──────────┬──────────┘
                                     │
                          POST /webhook/itt-coordination
                          or POST /agent/run-demo
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI SERVER (app/main.py)                        │
│                         The kitchen — handles all requests                  │
│                                                                             │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Webhook  │  │  HITL        │  │  Edge Case   │  │  Problem         │   │
│  │ Endpoint │  │  Response    │  │  Injection   │  │  Switcher        │   │
│  │ POST /   │  │  POST /      │  │  POST /      │  │  POST /          │   │
│  │ webhook/ │  │  agent/hitl/ │  │  agent/      │  │  agent/switch-   │   │
│  │ itt-     │  │  respond     │  │  inject-edge-│  │  problem/{id}    │   │
│  │ coord.   │  │              │  │  case        │  │                  │   │
│  └────┬─────┘  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│       │               │                  │                    │             │
│       │               │     Command(resume=)                  │             │
│       ▼               ▼                  ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │              run_agent() / resume_agent()                       │       │
│  │         Creates run_id, initial_state, thread_id                │       │
│  └──────────────────────────┬──────────────────────────────────────┘       │
│                             │                                              │
│  ┌──────────────────────────┼──────────────────────────────────────┐       │
│  │                     SSE Broadcaster                             │       │
│  │  (singleton: app/agent/sse.py)                                  │       │
│  │  Queues + Replay Buffer (deque maxlen=100)                      │       │
│  │  Events: agent_thinking, tool_call, tool_result, hitl_card,     │       │
│  │          escalation, trace_entry, confidence_update, deviation, │       │
│  │          notification, heartbeat                                 │       │
│  └──────────────────────────┬──────────────────────────────────────┘       │
└─────────────────────────────┼──────────────────────────────────────────────┘
                              │
                              │  GET /agent/stream/{run_id} (SSE)
                              │  The pipe — live updates flow through here
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BROWSER UI (app/ui/index.html)                        │
│                      The window — what the human sees                       │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Agent Status │  │ Confidence   │  │ Tool Calls   │  │ Trace        │  │
│  │ (typewriter) │  │ (0.0-1.0)    │  │ (per tool)   │  │ (sidebar)    │  │
│  │              │  │              │  │              │  │              │  │
│  │ "Calling T4" │  │    0.92      │  │ T1 → 120 ctr │  │ ● agent 14:32│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ HITL Approval Cards (Approve / Reject / Modify + countdown)         │  │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │ │ HITL-1: Approve ITT Split                                      │ │  │
│  │ │ Road: 60 trips ($9,000)  Sea: 40 containers ($1,400)           │ │  │
│  │ │ Total: $10,400  Confidence: 92%  Timeout: 30 min              │ │  │
│  │ │ [Approve]  [Reject]  [Modify]                                  │ │  │
│  │ └─────────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    │
│  │ Run Demo     │  │ Inject       │  │ Problem      │                    │
│  │              │  │ Edge Cases   │  │ Switcher     │                    │
│  │ [Run Demo]   │  │ [Conflict]   │  │ PB-12 ▼      │                    │
│  └──────────────┘  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              │ EventSource (SSE)
                              │ The pipe — live updates flow through here
                              │
┌─────────────────────────────┼──────────────────────────────────────────────┐
│                             │                                              │
│  ╔══════════════════════════╧════════════════════════════════════════╗     │
│  ║              LANGGRAPH STATEGRAPH (app/agent/graph.py)            ║     │
│  ║              The brain — decides what to do at each step          ║     │
│  ║                                                                   ║     │
│  ║   config = {"configurable": {"thread_id": run_id}}               ║     │
│  ║   checkpointer = MemorySaver()                                    ║     │
│  ║                                                                   ║     │
│  ║         ┌─────────┐                                               ║     │
│  ║         │  START  │                                               ║     │
│  ║         └────┬────┘                                               ║     │
│  ║              │                                                    ║     │
│  ║              ▼                                                    ║     │
│  ║    ┌─────────────────┐     ┌─────────────────┐                   ║     │
│  ║    │                 │     │                 │                   ║     │
│  ║    │   AGENT NODE    │────▶│   TOOL NODE     │──┐                ║     │
│  ║    │  (LLM Reasoning)│◀───│  (Execute Tools) │  │                ║     │
│  ║    │                 │     │                 │  │                ║     │
│  ║    │  provider.py    │     │  tool_registry  │  │                ║     │
│  ║    │  chat(tools)    │     │  .call(name)    │  │                ║     │
│  ║    │                 │     │                 │  │                ║     │
│  ║    └────────┬────────┘     └─────────────────┘  │                ║     │
│  ║             │                                    │                ║     │
│  ║             │ if hitl_pending                    │ if pending_    ║     │
│  ║             ▼                                    │ tool_calls     ║     │
│  ║    ┌─────────────────┐                           │                ║     │
│  ║    │                 │                           │                ║     │
│  ║    │   HITL NODE     │── approve ────────────────┘                ║     │
│  ║    │  (interrupt())  │── reject ───▶ agent (retry w/ alt)        ║     │
│  ║    │                 │── modify ───▶ agent (re-validate)         ║     │
│  ║    │  Command(       │                                            ║     │
│  ║    │  resume=)       │                                            ║     │
│  ║    └────────┬────────┘                                            ║     │
│  ║             │ timeout                                              ║     │
│  ║             ▼                                                      ║     │
│  ║    ┌─────────────────┐                                             ║     │
│  ║    │                 │──▶ agent (escalation context)               ║     │
│  ║    │  HITL-5         │                                             ║     │
│  ║    │  (Duty Manager) │                                             ║     │
│  ║    └─────────────────┘                                             ║     │
│  ║             │                                                      ║     │
│  ║             │ if dispatched && !monitored                          ║     │
│  ║             ▼                                                      ║     │
│  ║    ┌─────────────────┐                                             ║     │
│  ║    │                 │── deviation ──▶ hitl (HITL-5)              ║     │
│  ║    │  MONITOR NODE   │                                             ║     │
│  ║    │  (re-query T3)  │── no conflict ──▶ agent (continue)        ║     │
│  ║    │                 │                                             ║     │
│  ║    └─────────────────┘                                             ║     │
│  ║             │                                                      ║     │
│  ║             ▼                                                      ║     │
│  ║    ┌─────────────────┐                                             ║     │
│  ║    │      END        │                                             ║     │
│  ║    └─────────────────┘                                             ║     │
│  ╚═══════════════════════════════════════════════════════════════════╝     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    AGENT STATE (TypedDict)                          │    │
│  │  The memory — everything the agent knows at any moment              │    │
│  │  messages, tool_results, hitl_pending, hitl_history, confidence,    │    │
│  │  escalation, trace, deviation_log, problem_config, run_id, status,  │    │
│  │  context (11 charter fields)                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                  TOOL REGISTRY (app/tools/registry.py)              │    │
│  │                  The toolbox — available tools per problem           │    │
│  │                                                                     │    │
│  │  PB-12 Tools:              PB-01 Tools:                             │    │
│  │  ├─ get_itt_candidates     ├─ query_vessel_arrival                  │    │
│  │  ├─ check_road_itt_cap.    ├─ check_berth_availability             │    │
│  │  ├─ check_sea_itt_cap.     ├─ check_qc_availability                │    │
│  │  ├─ compute_itt_split      ├─ compute_berth_reassignment           │    │
│  │  ├─ update_tuas_loading    └─ notify_vessel_operator               │    │
│  │  ├─ dispatch_road_itt (post-approval)                              │    │
│  │  ├─ request_feeder_hold (post-approval)                            │    │
│  │  └─ notify_parties                                                  │    │
│  │                                                                     │    │
│  │  register_for_problem(id) → swaps tool set per YAML config          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                 SHARED SERVICES                                     │    │
│  │                  The utilities — shared infrastructure               │    │
│  │                                                                     │    │
│  │  provider.py          tool_adapter.py        yaml_reader.py         │    │
│  │  (8 LLM providers)    (Anthropic/Gemini/    (load YAML configs)    │    │
│  │                        OpenAI format)                               │    │
│  │                                                                     │    │
│  │  problem_config.py    models.py             logging.py              │    │
│  │  (load ProblemConfig) (Pydantic schemas)    (structured JSON)      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                 MOCK DATA LAYER (app/mocks/data.py)                 │    │
│  │                  The simulation — fake PSA systems                   │    │
│  │                                                                     │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│    │
│  │  │ CITOS PPT│ │CITOS Tuas│ │OptETruck │ │ Feeder   │ │ PORTNET  ││    │
│  │  │ containers│ │ loading  │ │ trucks   │ │capacity  │ │ feeder   ││    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│    │
│  │                                                                     │    │
│  │  edge_cases.py: inject_feeder_berth_conflict(), inject_stale_data() │    │
│  │  (mutates data.py directly → monitor re-query sees conflict)       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                 YAML CONFIGS (app/configs/)                         │    │
│  │                  The recipes — one per problem                       │    │
│  │                                                                     │    │
│  │  pb-12-itt.yaml (complete, flagship)                                │    │
│  │  pb-01-berth.yaml  pb-02-dtqc.yaml  pb-04-feeder.yaml             │    │
│  │  pb-09-expressway.yaml  pb-10-sea-air.yaml  pb-11-customs.yaml     │    │
│  │                                                                     │    │
│  │  Each config: systems, tools, hitl_gates, escalation_triggers,      │    │
│  │               cost_params, constraints, edge_cases, llm settings    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## How the Browser UI Connects (Step by Step)

```
BROWSER                          FASTAPI SERVER
  │                                    │
  │  1. User clicks "Run Demo"         │
  │  ──POST /agent/run-demo─────────▶  │
  │                                    │  → creates run_id
  │  ◀──{run_id, status}─────────────  │  → starts LangGraph agent
  │                                    │
  │  2. Browser opens SSE stream       │
  │  ──GET /agent/stream/{run_id}───▶  │
  │     (connection stays open)        │
  │                                    │
  │                                    │  → agent calls T1 (get_itt_candidates)
  │  ◀──event: tool_call─────────────  │  → SSE broadcaster pushes to browser
  │  ◀──event: tool_result───────────  │
  │                                    │
  │                                    │  → agent calls T4 (compute_itt_split)
  │  ◀──event: agent_thinking────────  │
  │  ◀──event: hitl_card─────────────  │  → HITL-1 approval card appears
  │                                    │
  │  3. User clicks "Approve"          │
  │  ──POST /agent/hitl/respond──────▶ │  → Command(resume=) resumes graph
  │  ◀──{status: "waiting_hitl"}─────  │  → HITL-2 card appears
  │  ◀──event: hitl_card─────────────  │
  │                                    │
  │  ... continues through all 17 steps│
```

The browser has TWO connections:
1. **POST requests** — for actions (run demo, approve HITL, inject edge cases)
2. **GET SSE stream** — for receiving live updates (agent thinking, tool calls, cards)

---

## Edge Case Injection Flow

```
1. User clicks "Run Demo"
   → agent starts processing normally

2. After step 10 (dispatch tools run)
   → "Inject Feeder Conflict" button lights up amber

3. User clicks "Inject Feeder Conflict"
   → browser sends POST /agent/inject-edge-case
   → FastAPI calls inject_feeder_berth_conflict()
   → mutates app/mocks/data.py (berth status: "available" → "conflict")

4. Monitor node (step 13) re-queries T3
   → T3 reads from mock data layer
   → sees berth_status: "conflict"

5. Monitor detects deviation
   → triggers HITL-5 emergency re-split
   → agent re-computes split (80/40 → 100/20)
```

The button appears AFTER dispatch because injecting BEFORE dispatch would break the normal happy path. Timing hint: "Inject after dispatch, before monitor check (steps 9-12)".

---

## Trace on the Bento UI

The trace is a real-time log of every step the agent takes. It appears as a sidebar panel showing rows like:

```
● agent  · reason           14:32:01.123 · 234ms · risk 0.05
● tool   · call_tool        14:32:01.358 · 89ms  · risk 0.05
● tool   · call_tool        14:32:01.447 · 156ms · risk 0.05
● hitl   · show_card        14:32:01.604 · 0ms   · risk 0.05
● hitl   · approve          14:33:15.221 · 0ms   · risk 0.05
● tool   · call_tool        14:33:15.445 · 203ms · risk 0.05
● monitor· deviation        14:33:20.112 · 12ms  · risk 0.22
```

Each row shows: which node ran, what action it took, when it happened, how long it took, and the current risk score. Color-coded: green=agent, blue=tool, yellow=HITL, red=escalation, purple=monitor. This is what the judges see — proof that the agent is reasoning, not just running a script.

---

## 17-Step Workflow (Happy Path + Deviation)

```
STEP  PATH     NODE       ACTION
─────────────────────────────────────────────────────────────
 1    webhook  INGEST     Receive ITT_COORDINATION_REQUEST
 2    agent    REASON     LLM reads context, calls T1 (get_itt_candidates)
 3    tools    EXECUTE    T1 → 120 containers, 160 TEU, breakdown
 4    agent    REASON     LLM calls T2 (check_road_itt_cap.) + T3 (check_sea_itt_cap.)
 5    tools    EXECUTE    T2 → 20 trucks available, T3 → feeder capacity + tidal window
 6    agent    REASON     LLM calls T4 (compute_itt_split) → 80/40 split = $10,400
 7    hitl     PAUSE      HITL-1: Approve ITT Split (30 min timeout)
                          ── user clicks Approve ──
 8    hitl     PAUSE      HITL-2: Approve Truck Dispatch (15 min timeout)
                          ── user clicks Approve ──
 9    hitl     PAUSE      HITL-3: Approve Feeder Hold (15 min timeout)
                          ── user clicks Approve ──
10    tools    EXECUTE    dispatch_road_itt + request_feeder_hold
11    tools    EXECUTE    T5 (update_tuas_loading_sequence)
12    hitl     PAUSE      HITL-4: Approve Loading Sequence (10 min timeout)
                          ── user clicks Approve ──
  ──── DEVIATION PATH (feeder berth conflict injected) ────
13    monitor  CHECK      Re-query T3 → detects berth_status: conflict
14    agent    REASON     Re-compute T4 → 100/20 = $11,200
15    hitl     PAUSE      HITL-5: Emergency Re-Split
                          ── user clicks Approve ──
16    tools    EXECUTE    Delta dispatch (+4 trucks)
17    tools    EXECUTE    T5 again with updated ETAs → COMPLETE
```

---

## HITL Gate Details

| Gate | Name | Trigger | Timeout | Timeout Action |
|------|------|---------|---------|----------------|
| HITL-1 | Approve ITT Split | Split computed | 30 min | Escalate to Duty Manager |
| HITL-2 | Approve Truck Dispatch | Truck dispatch ready | 15 min | Cancel Dispatch |
| HITL-3 | Approve Feeder Hold | Feeder hold request ready | 15 min | Escalate to Duty Manager |
| HITL-4 | Approve Loading Sequence Update | Tuas QC sequence update ready | 10 min | Hold Current Sequence |
| HITL-5 | Escalate to Duty Manager | Escalation fired | 30 min | Halt Workflow |

---

## Escalation Triggers

| # | Trigger | Threshold | Action |
|---|---------|-----------|--------|
| 1 | Low model confidence | `confidence < 0.85` | Escalate to human |
| 2 | Feeder hold exceeds tidal tolerance | `hold_duration > 1.5 hrs` | Escalate to Duty Manager |
| 3 | Financial recovery cost > limit | `action_cost > $10,000` | Escalate to Duty Manager |
| 4 | Data latency exceeds freshness | `data_age > 30 min` | Escalate to human |
| 5 | Road ITT capacity below threshold | `available_trucks < 60% required` | Escalate to human |
| 6 | Feeder operator unresponsive | `feeder_response_time > 15 min` | Escalate to human |
| 7 | Conflict between planners | Planner recommendations conflict | Escalate to Duty Manager |

---

## Key Architectural Decisions

- **Tool invocation:** In-process Python calls (not HTTP self-calls)
- **HITL pattern:** Single `hitl_node` with `interrupt()` + `Command(resume=)` + `MemorySaver(thread_id)` (not 5 separate nodes)
- **SSE bridge:** Singleton broadcaster with replay buffer — decouples LangGraph from frontend
- **Platform generalization:** Same LangGraph core, YAML config per problem, `register_for_problem()` swaps tool set
- **LLM confidence:** Structured JSON output (`{confidence: float}`) with deterministic fallback
- **Edge case injection:** Mutates `app/mocks/data.py` directly (not AgentState), so monitor re-query sees conflict
