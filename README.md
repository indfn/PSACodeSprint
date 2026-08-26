# PSA Nexus — Agentic Multi-Party Coordination Platform

> **One brain, seven problems.** PSA Nexus is a provider-agnostic, agentic AI platform that coordinates multi-party operations at PSA Singapore. Built for the **PSA Code Sprint: Agentic AI in Action** competition. Flagship demo: cross-terminal container transfers (PPT → Tuas).

```
  PSA Nexus
  ├── One LangGraph core — same reasoning engine for every problem
  ├── 7 YAML configs — swap one file, get a different problem
  ├── 8 LLM providers — Claude, GPT-4o, Gemini, DeepSeek, Ollama, vLLM, LM Studio, any OpenAI-compatible API
  └── Live dashboard — watch the agent think, approve its plans, test its limits
```

---

## Table of Contents

1. [What Is PSA Nexus?](#1-what-is-psa-nexus)
2. [The Problem & Cluster](#2-the-problem--cluster)
3. [Why This Needs an Agent (Not a Script)](#3-why-this-needs-an-agent-not-a-script)
4. [What Happens — How the Agent Solves It](#4-what-happens--how-the-agent-solves-it)
5. [How the Program Works — Technical Logic](#5-how-the-program-works--technical-logic)
6. [Project Structure](#6-project-structure)
7. [Getting Started](#7-getting-started)
8. [Configuration — Switching Problems & Providers](#8-configuration--switching-problems--providers)
9. [Evaluation — How This Meets the Competition Rubric](#9-evaluation--how-this-meets-the-competition-rubric)
10. [Key Numbers](#10-key-numbers)
11. [Sources & Research](#11-sources--research)

---

## 1. What Is PSA Nexus?

**PSA Nexus** is an agentic AI coordination platform for port operations. Instead of building seven separate tools for seven separate problems, Nexus builds **one intelligent core** and swaps what it knows per problem.

| Layer | What It Does |
|-------|-------------|
| **Agent Core** | LangGraph state machine — reasons, calls tools, asks humans when unsure, recovers from failures |
| **Tool Registry** | Plug-in system — each problem registers its own tools (CITOS, OptETruck, PORTNET for ITT; VTIS, OptEVoyage for berth delays, etc.) |
| **Problem Configs** | One YAML file per problem — systems, tools, HITL gates, escalation rules, cost parameters |
| **Live Dashboard** | Real-time SSE streaming — watch the agent's thoughts, approve its plans, inject edge cases to test it |
| **LLM Abstraction** | 8 providers behind one interface — swap Claude for a local Ollama model with a single config line |

**Flagship demo:** PB-12 (Multi-Party ITT Coordination Failure) — moving 120 containers between terminals. But the same platform handles 6 sibling problems in the same cluster by swapping the YAML and tool set.

---

## 2. The Problem & Cluster

### The Flagship — PB-12: Multi-Party ITT Coordination Failure

A vessel waiting at **Tuas Port** needs **120 containers** moved from **Pasir Panjang Terminal (PPT)** before it departs. The containers can travel by **road** (trucks via OptETruck) or by **sea** (feeder vessel via PORTNET). The PPT and Tuas yard systems (CITOS) are not integrated — what's ready at PPT is invisible at Tuas for 30–60 minutes. The road/sea split is negotiated by **phone calls** between the PPT planner, Tuas planner, and feeder operator.

**When it works:** Someone guesses a 60/40 split, calls 15 trucks and a feeder, and hopes. Often it does not line up.

**When it breaks:** A feeder berth conflict delays the sea leg. By then, trucks are already dispatched and can't be rerouted. The vessel waits.

### The Cluster — C2: Manual Multi-Party Coordination (7 Problems)

PB-12 is not alone. Six sibling problems share the same root cause — **manual phone-call coordination between parties with no shared system of record**:

| Problem | What Breaks | Who Calls Whom |
|---------|------------|---------------|
| **PB-01** Berth Delay Cascade | Vessel arrives late, berth plan must shift | VTIS → OptEVoyage → CITOS |
| **PB-02** DTQC Breakdown | Quay crane fails mid-operation, jobs must re-route | ROCC → CITOS → FMS |
| **PB-04** Missed Feeder Connection | Feeder departs without transhipment containers | PORTNET → CITOS |
| **PB-09** Expressway Blockage | Trucks stuck, gate slots must re-flow | OptETruck → SmartBooking |
| **PB-10** Sea-Air Cut-Off | Sea leg delayed, air freight must rebook | OptEModal → TradeNet → SATS |
| **PB-11** Customs Hold | Containers held, loading must deprioritize them | TradeNet → CALISTA |
| **PB-12** ITT Coordination *(flagship)* | Road/sea split guessed, feeder delayed | CITOS → OptETruck → PORTNET → CITOS (Tuas) |

**Cluster score:** 4.80/5.00 — highest agentic sweet spot, broadest coverage, most compelling demo (litmus test across 16 candidates).

### What It Costs

| Layer | Detail | Value |
|-------|--------|-------|
| **Per incident (flagship)** | Vessel delay (2h × $2,500) + extra trucks (5 × $150) + feeder hold (2h × $800) + re-handles (20 × $35) + staff (8h × $50) | **$8,450** manual → **$450** with agent |
| **Net savings per incident** | Avoided waste minus agent runtime cost | **$8,000** |
| **Incidents per month** | Flagship alone: 4–6/month | $32K–$48K/month |
| **Flagship annual** | $8K × 4–6/month × 12 | **$384K–$576K** |
| **Cluster annual (all 7)** | 18–30 incidents/month across all problems | **$1.26M–$2.08M** |

**Grounded cost parameters (Singapore-specific):**

| Parameter | Value | Source |
|-----------|-------|--------|
| Mother vessel demurrage | $2,500/hr | Panamax container vessel standard |
| Feeder charter | $800/hr | Regional feeder standard |
| Road ITT trip (PPT→Tuas, ~35 km) | $150 | Prime mover + driver + fuel |
| LTA chassis limit | 1× 40ft (FEU) OR 2× 20ft (TEU) per truck | Land Transport Authority |
| Sea ITT marginal charter | $0 | Existing scheduled feeder rotation |
| Sea ITT handling | $35/lift-move | PSA standard |
| Yard re-handle | $35/move | PSA standard |
| Missed connection | $150/container | SLA penalty |
| Yard block capacity | 4,500 TEU | CITOS parameter |

**The math:**

```
Savings = Avoided Vessel Delay ($5,000)
        + Avoided Truck Overprovision ($750)
        + Avoided Sea Overcharge ($1,600)
        + Avoided Re-handles ($700)
        - Agent Cost ($50)
        = $8,000 per incident

Annual (flagship) = $8,000 × 4–6/month × 12 = $384K–$576K
Cluster (all 7)   = $1.26M–$2.08M
```

---

## 3. Why This Needs an Agent (Not a Script)

### The 5-Point Litmus Test

Every candidate problem was scored against 5 yes/no questions. A problem must pass all 5 to justify an agentic solution:

| Filter | Question | PB-12 Answer | Why It Matters |
|--------|----------|-------------|----------------|
| **L1** Non-deterministic | Does it need multi-step reasoning and adaptive re-planning — not just a lookup? | ✅ Yes — road/sea split depends on live truck counts, feeder status, tide windows, and traffic that change every minute | A simple if/else would fail when conditions shift mid-operation |
| **L2** Multi-system | Does it span 3+ PSA systems? | ✅ Yes — CITOS (PPT), CITOS (Tuas), OptETruck, PORTNET, Feeder operator | The value is bridging disconnected systems no single dashboard covers |
| **L3** Real cost | Does failure cost PSA money every month? | ✅ Yes — $8K/incident, 4–6/month | No real cost = no real impact |
| **L4** Needs human judgment | Are some decisions too risky or ambiguous to fully automate? | ✅ Yes — dispatching 16 trucks ($2,400) or holding a feeder ($800/hr, tidal risk) needs a human's sign-off | This is where agents earn trust — by knowing when to ask |
| **L5** Macro-impact | Does fixing it move a number leadership cares about? | ✅ Yes — vessel dwell time, $384K–$576K annual, $1.26M cluster | A micro-optimisation is not worth an agent |

**Result:** 12 of 16 problems passed all 5 filters. Cluster C2 (7 problems) won.

### Why Rule Engines Fail Here

| Property | Rule Engine | Agentic Approach |
|----------|------------|-----------------|
| **Data** | Assumes data is fresh and complete | Handles stale data (30-min PORTNET delay), incomplete fields, missing containers |
| **Plan** | One fixed sequence | Dynamic — re-computes the road/sea split when the feeder is delayed |
| **Failure** | Crashes or silently continues | Detects via guardrails → retries, uses fallback, or escalates to a human |
| **Human role** | All or nothing (manual or fully auto) | Calibrated — autonomous for gathering, HITL for committing (5 gates, 7 triggers) |
| **Reuse** | New code per problem | Same core, new YAML — PB-12's logic becomes PB-01's with a config swap |

### The Autonomy Trap

> *Higher autonomy is not automatically better. Teams should select an appropriate level based on use case, operational risk, and available controls.*

**Selected: Tier 2 — Human-in-the-Loop Exception Solver.** The agent gathers data and drafts plans autonomously, but waits for a 1-click human confirmation before any state-mutating action (dispatching trucks, holding a vessel, changing a loading sequence). This matches the risk profile: HIGH financial exposure ($10K+ per action) + multi-party authority boundaries + cross-terminal data asymmetry.

---

## 4. What Happens — How the Agent Solves It

*Plain-English flowchart — for the judge, the operator, and anyone who wants to understand the flow without reading code.*

```
 ╔══════════════════════════════════════════════════════════════════════╗
 ║         PSA NEXUS — HOW IT SOLVES A PROBLEM                        ║
 ║         Example: Moving 120 containers from PPT to Tuas            ║
 ╚══════════════════════════════════════════════════════════════════════╝

  ┌─────────────────────────────────────────────────────────┐
  │  ①  SOMETHING HAPPENS                                  │
  │  PPT yard says: "120 containers need to get to Tuas"   │
  │  → System receives an alert (webhook)                  │
  │  → Checks: Is this real? (≥50 containers, ship still  │
  │    2+ hours away) — if not, ignore                     │
  └───────────────────────┬─────────────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ②  THE AGENT LOOKS AROUND (Gathers Information)       │
  │  The AI asks 3 systems at once:                        │
  │                                                        │
  │   📦  "What containers are ready?"     → PPT Yard      │
  │   🚛  "How many trucks are free?       → Road System   │
  │        How long is the drive?"           (OptETruck)   │
  │   🚢  "Is the feeder ship available?   → Port Network  │
  │        Will it catch the tide?"                        │
  └───────────────────────┬─────────────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ③  THE AGENT THINKS (Makes a Plan)                    │
  │  AI weighs all the answers and calculates:              │
  │                                                        │
  │   "Best plan:  80 by road  +  40 by sea  = $10,400"   │
  │   "Other options: 100/20 or 60/60 if needed"           │
  │   Also checks 6 safety rules: Are weights OK? Is      │
  │   there enough space? Will we make it on time?         │
  └───────────────────────┬─────────────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ④  ASK THE HUMAN (Approval Gates)                     │
  │  The agent NEVER acts alone on big decisions.          │
  │  It shows a card and waits:                            │
  │                                                        │
  │   Gate 1 ─ "Approve this split?"         (30 min)      │
  │   Gate 2 ─ "Send these trucks?"          (15 min)      │
  │   Gate 3 ─ "Hold the feeder ship?"       (15 min)      │
  │   Gate 4 ─ "Update Tuas loading order?"  (10 min)      │
  │                                                        │
  │   Human can:  ✅ Approve  ✏️ Change  ❌ Reject         │
  │   If no answer in time → auto-escalate or cancel      │
  │   If rejected → agent shows other options              │
  │   If changed → agent re-checks and asks again          │
  └───────────────────────┬─────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
  ┌────────────────────┐  ┌────────────────────────────┐
  │  ✅ APPROVED        │  │  ⚠️  SOMETHING IS OFF?     │
  │  Agent goes ahead:  │  │  Agent watches for 7       │
  │  • Sends trucks     │  │  warning signs:            │
  │    (West Coast Hwy  │  │  • Not confident (<85%)    │
  │     → AYE → Tuas)  │  │  • Ship hold too long      │
  │  • Holds feeder     │  │  • Cost too high (>$10K)   │
  │  • Updates Tuas     │  │  • Data is old (>30 min)   │
  │    loading plan     │  │  • Not enough trucks       │
  └──────────┬─────────┘  │  • Ship not responding     │
             │            │  • Planners disagree         │
             │            │  → Escalate to Duty Manager  │
             │            └──────────────┬─────────────┘
             │                           │ (Gate 5, 30 min → halt if no reply)
             ▼                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ⑤  KEEP WATCHING (The Clever Part)                    │
  │  Even after dispatch, the agent keeps checking:        │
  │                                                        │
  │   "Is the feeder still on time?"  → asks Port again   │
  │                                                        │
  │   ┌─ No problem ──────────────►  ✅ Done               │
  │   │                                                    │
  │   └─ 🚨 Berth conflict! Ship delayed to 4pm            │
  │       → Agent thinks again: "New plan: 100 by road,   │
  │         20 by sea — costs $1,500 more but saves        │
  │         a $5,000 missed connection"                    │
  │       → Shows EMERGENCY card to human                  │
  │       → If approved: sends 4 more trucks, updates      │
  │         Tuas again, logs what went wrong               │
  └───────────────────────┬─────────────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ⑥  WHAT YOU SEE (Live Dashboard)                      │
  │                                                        │
  │   The judge / operator watches everything live:        │
  │   • 💭  What the AI is thinking (streaming text)       │
  │   • 🔧  Which tools it called and what they returned   │
  │   • 📋  Approval cards with Approve / Reject / Modify  │
  │   • 📊  Full trace: every step, time, confidence       │
  │   • 🎮  Buttons to test: "Inject ship conflict"        │
  │         "Inject stale data"  "Run Demo"  "Reset"      │
  │   • 🔄  Problem switcher: PB-12 ↔ PB-01 (same core!)  │
  └─────────────────────────────────────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────────────┐
  │  📝  EVERYTHING IS RECORDED                            │
  │  • Trace: who did what, when, how long, risk score     │
  │  • Deviation log: why the first plan failed            │
  │  • Confidence: 95% → 78% (problem!) → 90% (fixed)    │
  │  • Structured logs for audit  |  LangSmith if enabled  │
  └─────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────┐
  │  💡  WHY THIS MATTERS                                  │
  │  Before: 4–8 hours, 12+ phone calls, $8,450/event     │
  │  After:  ~27 minutes, 2 approvals, $450/event          │
  │  Saving: $8,000 per incident → $384K–$576K per year   │
  │  Same brain works for 7 other port problems            │
  │  ($1.26M–$2.08M across the cluster)                    │
  └─────────────────────────────────────────────────────────┘
```

---

## 5. How the Program Works — Technical Logic

*Standard CS programming methodology flowchart — control flow, decisions, loops, and error paths. Same story as above, in technical notation.*

```
 PROGRAM: PSA Nexus — Agentic Multi-Party Coordination Platform
 LANGUAGE: Python 3.11  |  FRAMEWORK: LangGraph  |  SERVER: FastAPI

 ┌─────────────────────────────────────────────────────────────────┐
 │  [TERMINAL]  START                                              │
 └───────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  [PROCESS]  INITIALIZE                                          │
 │  • Load settings from file (which port, which AI to use)        │
 │  • Load all 7 problem configs (pb-01..pb-12 YAML)              │
 │  • Prepare AI provider (any of 8: anthropic/openai/gemini/     │
 │    deepseek/ollama/vllm/lmstudio/custom + base_url)             │
 │  • Prepare tool adapter (translates between AI tool formats)    │
 └───────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  [PROCESS]  BUILD COMPONENTS                                    │
 │  • Register tools per active problem (TOOLSETS dict)            │
 │  • Build AI brain: system prompt templated from ProblemConfig   │
 │    (not hardcoded — "You are Nexus, coordinating {problem}")    │
 │  • Build state container: messages, results, approvals,         │
 │    confidence, trace log, deviation log, risk score             │
 │  • Build decision graph (see MAIN GRAPH below)                  │
 │  • Build live-stream broadcaster (replay buffer for late join)  │
 └───────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  [PROCESS]  START SERVER  (port 8000)                           │
 │  • Mock systems:  /api/citos/ppt  /api/optetruck                │
 │  │                /api/feeder  /api/portnet  /api/citos/tuas   │
 │  │                /api/vtis  /api/optevoyage (sibling PB-01)   │
 │  • Entry point:   POST /webhook/itt-coordination → run_agent()  │
 │  • Problem switch: POST /agent/switch-problem/{id}              │
 │  • Live stream:   GET  /agent/stream/{run_id}  (SSE)           │
 │  • Controls:      POST /agent/hitl/respond  (approve/reject)    │
 │  │                POST /agent/inject-edge-case                  │
 │  │                POST /agent/run-demo                          │
 │  • Dashboard:     GET  /ui/  (PSA Nexus — problem switcher)     │
 └───────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  [DECISION]  Wait for event?  ◇                                 │
 │                        ┌── No ──►  [PROCESS] stay idle         │
 │                        │              heartbeat every 30s        │
 │                        │                    │                    │
 │                        │ ◄─────────────────┘                    │
 │                        ▼                                        │
 │                   Yes (event arrives)                           │
 └───────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
 ╔═══════════════════════════════════════════════════════════════════╗
 ║  [SUBPROCESS]  HANDLE EVENT  (called per request)               ║
 ╠═══════════════════════════════════════════════════════════════════╣
 ║                                                                 ║
 ║  ┌──────────────────────────────────────────────────────────┐    ║
 ║  │ [INPUT]  Receive ITTCoordinationEvent                   │    ║
 ║  │  vessel_id, container_count, blocks, departure_time     │    ║
 ║  └──────────────────────┬───────────────────────────────────┘    ║
 ║                         │                                       ║
 ║                         ▼                                       ║
 ║  ┌──────────────────────────────────────────────────────────┐    ║
 ║  │ [DECISION]  Input valid?  ◇                              │    ║
 ║  │  Pydantic checks: count ≥ 50?  departure > now + 2h?    │    ║
 ║  │  weight 0–60000?  block ≤ 4500 TEU?  422 if invalid     │    ║
 ║  │       ┌── No ──► [OUTPUT] return 422 error, [END] run  │    ║
 ║  │       ▼                                                  │    ║
 ║  │      Yes ──► check LLM rate limit (429 → retry+fallback)│    ║
 ║  └──────────────────────┬───────────────────────────────────┘    ║
 ║                         │                                       ║
 ║                         ▼                                       ║
 ║  ┌──────────────────────────────────────────────────────────┐    ║
 ║  │ [PROCESS]  Create initial state                          │    ║
 ║  │  run_id = new ID (also thread_id for LangGraph resume)  │    ║
 ║  │  state = { messages, tool_results={}, hitl_pending=null, │    ║
 ║  │           confidence=1.0, trace=[], deviation_log=[],     │    ║
 ║  │           problem_config: active YAML, run_id, status }  │    ║
 ║  │  Validate 6 guardrails (weight, block, trucks, feeder,   │    ║
 ║  │  margin, tide) before any tool call                     │    ║
 ║  └──────────────────────┬───────────────────────────────────┘    ║
 ║                         │                                       ║
 ║                         ▼                                       ║
 ║  ╔══════════════════════════════════════════════════════════╗     ║
 ║  ║  [MAIN GRAPH]  LangGraph StateGraph                      ║     ║
 ║  ║  Loops through agent_node until END                      ║     ║
 ║  ║                                                          ║     ║
 ║  ║   ┌──────────────────────────────┐                        ║     ║
 ║  ║   │  agent_node  (AI thinks)     │ ◄── loopback from      ║     ║
 ║  ║   │  1. Build prompt from        │     every other node   ║     ║
 ║  ║   │     ProblemConfig + history  │                        ║     ║
 ║  ║   │  2. Adapt tool schemas for   │                        ║     ║
 ║  ║   │     provider (Anthropic /    │                        ║     ║
 ║  ║   │     OpenAI / Gemini format)  │                        ║     ║
 ║  ║   │  3. chat(messages, tools)    │                        ║     ║
 ║  ║   │     with retry               │                        ║     ║
 ║  ║   │  4. Filter hallucinated      │                        ║     ║
 ║  ║   │     tools → error ToolResult │                        ║     ║
 ║  ║   │  5. Check 7 triggers +       │                        ║     ║
 ║  ║   │     compute risk_score       │                        ║     ║
 ║  ║   │  6. Write trace + SSE event  │                        ║     ║
 ║  ║   └──────────────┬───────────────┘                        ║     ║
 ║  ║                  │                                        ║     ║
 ║  ║                  ▼                                        ║     ║
 ║  ║          ┌───────────────┐                                ║     ║
 ║  ║          │ ◇ route?      │  conditional_edge              ║     ║
 ║  ║          │ (what next?)  │                                ║     ║
 ║  ║          └──┬──┬───┬──┬──┘                                ║     ║
 ║  ║             │  │   │  │                                   ║     ║
 ║  ║     tool_calls │   │  │  done                             ║     ║
 ║  ║             │ need │ need │                               ║     ║
 ║  ║             │ hitl │ esc. │ monitor                       ║     ║
 ║  ║             ▼  ▼   ▼  ▼   ▼                               ║     ║
 ║  ║        ┌──────┐┌──────┐┌──────┐┌─────────┐  ┌─────┐       ║     ║
 ║  ║        │ tool ││ hitl ││ HITL ││ monitor │  │ END │       ║     ║
 ║  ║        │ node ││ node ││  -5  ││  node   │  │     │       ║     ║
 ║  ║        └──┬───┘└──┬───┘└──┬───┘└────┬────┘  └─────┘       ║     ║
 ║  ║           │       │       │         │                     ║     ║
 ║  ║           └───────┴───────┴─────────┘                     ║     ║
 ║  ║                   │  all return to agent_node ────────────║─────╫── loop
 ║  ╚═══════════════════╪═══════════════════════════════════════╝     ║
                     │                                             ║
                     │  expanded below — what each node does       ║
                     ▼                                             ║
 ║  ┌─────────────────────────────────┐                            ║
 ║  │ EXPANDED: tool_node             │  ← when agent emits       ║
 ║  │ ─────────────────────────────   │    tool_calls              ║
 ║  │ FOR EACH tool in tool_calls:    │                            ║
 ║  │   try: call tool (in-process)   │                            ║
 ║  │   except Timeout  → fallback    │                            ║
 ║  │   except 503      → fallback    │                            ║
 ║  │   except partial  → save what   │                            ║
 ║  │     succeeded, continue batch   │                            ║
 ║  │   save ToolResult + risk_score  │                            ║
 ║  │   publish SSE tool_result       │                            ║
 ║  │ END FOR                         │                            ║
 ║  │ ──► return to agent_node        │                            ║
 ║  └─────────────────────────────────┘                            ║
 ║                                                                 ║
 ║  ┌─────────────────────────────────┐                            ║
 ║  │ EXPANDED: hitl_node             │  ← when approval needed   ║
 ║  │ ─────────────────────────────   │                            ║
 ║  │ interrupt({ approval_card })    │                            ║
 ║  │   ── PAUSE execution ──         │                            ║
 ║  │   wait for POST /hitl/respond   │                            ║
 ║  │   (identified by thread_id)     │                            ║
 ║  │                                 │                            ║
 ║  │   ◇ human replied?              │                            ║
 ║  │   ├─ approve ─► clear pending,  │                            ║
 ║  │   │           notify, back to   │                            ║
 ║  │   │           agent_node        │                            ║
 ║  │   ├─ reject ─► show alts or     │                            ║
 ║  │   │           escalate(HITL-5), │                            ║
 ║  │   │           back to agent_node│                            ║
 ║  │   ├─ modify ─► re-validate,     │                            ║
 ║  │   │           re-run T4, then   │                            ║
 ║  │   │           ask again         │                            ║
 ║  │   ├─ timeout ─► per-gate rule:  │                            ║
 ║  │   │           escalate / cancel │                            ║
 ║  │   │           / hold / halt     │                            ║
 ║  │   └─ late resume after timeout? │                            ║
 ║  │      → return stale error (422) │                            ║
 ║  │   ──► all paths return to       │                            ║
 ║  │       agent_node (or END)       │                            ║
 ║  └─────────────────────────────────┘                            ║
 ║                                                                 ║
 ║  ┌──────────────────────────────────────────────────────────┐    ║
 ║  │ [DETAIL]  Tools the agent can call                      │    ║
 ║  │  T1 get_itt_candidates      → what is ready at PPT      │    ║
 ║  │  T2 check_road_itt_capacity → trucks + drive time       │    ║
 ║  │  T3 check_sea_itt_capacity  → ship + tide window        │    ║
 ║  │  T4 compute_itt_split       → best road/sea mix ($10,400)│   ║
 ║  │     + cost_vs_baseline ($12K→$10.4K) + ROI ($8K/incident)│  ║
 ║  │  T5 update_tuas_loading     → new loading order at Tuas │    ║
 ║  │  T6 dispatch_road_itt       → send trucks (needs HITL-2)│    ║
 ║  │  T7 request_feeder_hold     → ask ship to wait (HITL-3) │    ║
 ║  │  T8 notify_parties          → alert stakeholders         │    ║
 ║  │  PB-01 siblings: query_vessel_arrival, berth_avail, ... │    ║
 ║  └──────────────────────────────────────────────────────────┘    ║
 ║                                                                 ║
 ║  ┌──────────────────────────────────────────────────────────┐    ║
 ║  │ [DETAIL]  7 warning checks (run after every tool batch) │    ║
 ║  │  1. confidence < 0.85 ─────────► escalate to human       │    ║
 ║  │  2. ship hold > 1.5 hours ────► escalate to manager     │    ║
 ║  │  3. cost > $10,000 ───────────► escalate to manager     │    ║
 ║  │  4. data older than 30 min ───► escalate to human       │    ║
 ║  │  5. trucks < 60% of needed ──► escalate to human       │    ║
 ║  │  6. ship not replying >15 min ► escalate to human       │    ║
 ║  │  7. planners disagree ────────► escalate to manager     │    ║
 ║  │  Any trigger → set HITL-5 card → hitl_node              │    ║
 ║  └──────────────────────────────────────────────────────────┘    ║
 ║                                                                 ║
 ║  ┌──────────────────────────────────────────────────────────┐    ║
 ║  │ [DETAIL]  monitor_node (runs after dispatch)            │    ║
 ║  │  1. Ask Port again: "Is the feeder still on time?"      │    ║
 ║  │  2. ◇ Berth conflict? ── No ──► mark done, go to END   │    ║
 ║  │                      └─ Yes ─► log deviation,           │    ║
 ║  │     lower confidence to 0.78, re-run T4:                │    ║
 ║  │     80/40 → 100/20, build emergency card (HITL-5),     │    ║
 ║  │     on approve: send 4 more trucks, call T5 again       │    ║
 ║  └──────────────────────────────────────────────────────────┘    ║
 ║                                                                 ║
 ╚══════════════════════════╤══════════════════════════════════════╝
                            │
                            ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  [PROCESS]  RECORD & STREAM                                      │
 │  Every step: TraceEntry(time, node, action, result, risk_score, │
 │  confidence, duration_ms, fallback_used) → state.trace           │
 │  On deviation: append to deviation_log                           │
 │  Stream 10 event types via SSE (replay buffer for late join):   │
 │   thinking, tool_call, tool_result, hitl_card, escalation,      │
 │   trace_entry, confidence, deviation, notification, heartbeat    │
 │  Structured JSON log → console + file (for audit)               │
 │  LLM metrics: latency_ms, input/output tokens per call          │
 │  If LangSmith key exists → also send trace there                │
 └───────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  [OUTPUT]  RETURN RESULT                                         │
 │  { run_id, final_state, trace, deviation_log, confidence,       │
 │    risk_score, cost_vs_baseline, roi }                          │
 │  Shown on dashboard + available via API + GET /runs/{run_id}    │
 └───────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  [DECISION]  Demo controls  ◇  (user may interact at any time)  │
 │  • POST /agent/inject-edge-case → mutates mock data            │
 │    (so next Port check sees the problem — per-run isolated)    │
 │  • POST /agent/switch-problem/{id} → swaps YAML + tool set     │
 │    (PB-12 ↔ PB-01, same core, different tools)                 │
 │  • POST /agent/run-demo → creates sample event + starts flow   │
 │  • POST /agent/reset-mocks → restores clean mock data          │
 └───────────────────────────┬─────────────────────────────────────┘
                             │
              ┌───────────────┴───────────────┐
              ▼                               ▼
 ┌────────────────────────┐    ┌──────────────────────────────┐
 │ [PROCESS] Go back to   │    │ [TERMINAL]  SHUTDOWN        │
 │ Wait for next event    │    │  Stop server, save logs     │
 └────────────────────────┘    └──────────────────────────────┘


 VARIABLES  (what the program remembers per run)
 ─────────────────────────────────────────────
  state.messages        conversation history with the AI
  state.tool_results    answers from each tool (with latency, confidence, risk)
  state.hitl_pending    which approval card is waiting (with timeout + action)
  state.hitl_history    all past approvals / rejections / modifications
  state.confidence      0.0 – 1.0  (below 0.85 = escalate, LLM self-assessed)
  state.risk_score      0.0 – 1.0  (derived from confidence + active warnings)
  state.trace           step-by-step record (every node, tool, HITL, deviation)
  state.deviation_log   what went wrong and how it was fixed
  state.run_id          unique ID for this run (also LangGraph thread_id)
  state.problem_config  active problem's YAML (systems, tools, costs, gates)
  state.context         event details, tool outputs, split plan, cost/ROI

 KEY RULES
 ─────────────────────────────────────────────
  1. No big action without human approval (5 gates, each with timeout).
  2. If confidence is low or a warning fires, always ask human (7 triggers → HITL-5).
  3. Tools run inside the program (fast); mock data is per-run isolated.
  4. Every decision is streamed live and saved for audit (trace + risk_score).
  5. If plan fails mid-way, re-plan and ask again — do not crash (fallback → notify → escalate).
  6. Same core, different problem — swap one YAML, get a different port scenario.
```

---

## 6. Project Structure

```
 PSACodeSprint/
 ├── README.md                              # This file
 ├── buildplan/
 │   ├── tech-stack.md                      # Why LangGraph, FastAPI, YAML, no database
 │   └── 03-03-master-charter.md            # Locked problem charter (flagship PB-12)
 │       ├── Section 1: Executive summary & persona
 │       ├── Section 2: As-Is (12 steps) vs To-Be (17 steps)
 │       ├── Section 3: 8 tool specs with exact I/O schemas
 │       ├── Section 4: 5 HITL gates + 7 triggers + guardrails + edge cases
 │       ├── Section 5: Cost model + ROI ($8K/incident, $1.26M–$2.08M cluster)
 │       ├── Section 6: Platform generalisation (7 siblings, 6 primitives)
 │       ├── Section 7: Execution trace + demo script (89.9s walkthrough)
 │       ├── Section 8: Gap inventory (23 gaps, honest built-vs-missing)
 │       └── Section 9: Target architecture + tech stack
 │
 ├── research/                              # Phase 1 — How PSA works
 │   ├── sectors/
 │   │   ├── berth-marine.md               # Vessels, berths, cranes
 │   │   ├── container-yard-transport.md   # AGVs, yard cranes, reefers
 │   │   ├── gate-haulage.md               # Gates, trucks, customs
 │   │   └── multimodal-logistics.md       # Sea-air, warehousing, visibility
 │   ├── systems/
 │   │   └── baseline-systems.md           # 7 PSA digital systems
 │   └── flows/
 │       └── critical-flows.md             # Physical, info, decision flows
 │
 ├── problems/                              # Phase 2 — What breaks
 │   ├── 02-01-disruption-scenarios.md     # 16 disruption scenarios
 │   ├── 02-02-failure-modes.md            # Why each is hard (gaps, costs)
 │   └── 02-03-problem-bank.md            # 16 structured problem charters
 │
 ├── problem-selection/                     # Phase 3 — What to build
 │   ├── 03-01-litmus-test-scores.md       # 5-filter litmus test + cluster ranking
 │   └── 03-02-autonomy-level.md           # HITL guardrails + risk profile
 │
 ├── app/                                   # ← NEW: PSA Nexus platform (Phases 4–8)
 │   ├── main.py                           # FastAPI: webhook + SSE + HITL + switch + UI
 │   ├── agent/
 │   │   ├── state.py                      # AgentState (TypedDict — messages, trace, confidence)
 │   │   ├── graph.py                      # LangGraph StateGraph (agent → tools → hitl → monitor)
 │   │   ├── run.py                        # run_agent() + resume_agent() + create_initial_state()
 │   │   ├── nodes.py                      # agent_node (LLM + adapter) + tool_node (guards+fallback)
 │   │   ├── monitor.py                    # monitor_node (re-query T3, detect deviation, re-plan)
 │   │   ├── prompts.py                    # build_system_prompt(config) — templated, not hardcoded
 │   │   ├── escalation.py                 # 7 trigger checks (charter thresholds)
 │   │   ├── confidence.py                 # LLM self-assessment + deterministic backup + risk_score
 │   │   ├── trace.py                      # TraceEntry + export_trace() + validation
 │   │   ├── resilience.py                 # Rate limit 429→retry→fallback, stale resume guard
 │   │   ├── sse.py                        # SSEBroadcaster (replay buffer, Last-Event-ID)
 │   │   └── problem_switcher.py           # switch_problem() — YAML swap at runtime
 │   ├── tools/
 │   │   ├── base.py                       # ToolResult + BaseTool (auto metadata, timeout, fallback)
 │   │   ├── registry.py                   # ToolRegistry — TOOLSETS, singleton, register_for_problem()
 │   │   ├── container_readiness.py        # T1: get_itt_candidates
 │   │   ├── road_itt.py                   # T2: check_road_itt_capacity (peak-aware)
 │   │   ├── sea_itt.py                    # T3: check_sea_itt_capacity (fleet + tidal)
 │   │   ├── optimiser.py                  # T4: compute_itt_split ($10,400 + cost_vs_baseline + ROI)
 │   │   ├── tuas_loading.py               # T5: update_tuas_loading_sequence
 │   │   ├── dispatch_road_itt.py          # T6: dispatch_road_itt (HITL-2 gated, delta support)
 │   │   ├── request_feeder_hold.py        # T7: request_feeder_hold (HITL-3 gated)
 │   │   ├── notify.py                     # T8: notify_parties (primitive #5)
 │   │   ├── pb01/                         # PB-01 sibling stubs (VTIS, OptEVoyage, CITOS berth)
 │   │   ├── edge_cases.py                 # Hooks: inject_feeder_conflict, inject_stale_data (per-run)
 │   │   └── fallbacks.py                  # cached_road/sea_capacity (fallback_used flag)
 │   ├── mocks/
 │   │   ├── data.py                       # Canonical fixtures (120 containers, 20 trucks, feeder windows)
 │   │   ├── edge_cases.py                 # simulate_feeder_conflict, simulate_stale_data
 │   │   └── routers/                      # Mock API endpoints (CITOS, OptETruck, PORTNET, VTIS, etc.)
 │   ├── hitl/
 │   │   ├── models.py                     # HITLGate, HITLDecision, HITL_GATES (5 gates, timeouts)
 │   │   ├── gates.py                      # hitl_node: interrupt({card}) + build_approval_card()
 │   │   └── handler.py                    # handle_hitl_response(): approve/reject/modify/timeout
 │   ├── shared/
 │   │   ├── provider.py                   # 8 providers: anthropic/openai/gemini/deepseek/ollama/vllm/lmstudio/custom
 │   │   ├── tool_adapter.py               # Translates tool schemas per provider family
 │   │   ├── models.py                     # Canonical Pydantic schemas (single source)
 │   │   ├── logging.py                    # Structured JSON logging (stdout + file)
 │   │   └── yaml_reader.py                # YAML loading with defaults
 │   ├── configs/
 │   │   ├── pb-12-itt.yaml               # Flagship: 5 systems, 8 tools, 5 HITL, 7 triggers, edge cases
 │   │   ├── pb-01-berth.yaml             # Sibling: berth delay (VTIS, OptEVoyage)
 │   │   └── pb-0*.yaml                   # 7 C2 configs total (all completed to parity)
 │   ├── ui/
 │   │   ├── index.html                    # PSA Nexus dashboard + problem switcher
 │   │   ├── style.css                     # Professional dark theme
 │   │   └── app.js                        # SSE client, HITL cards, trace, notifications
 │   └── tests/
 │       ├── test_config.py               # All 7 YAML configs load correctly
 │       ├── test_provider.py             # All 8 providers + adapter + fallback
 │       ├── test_tools.py                # Every tool against mock server
 │       ├── test_hitl.py                 # HITL approve/reject/modify/timeout + stale guard
 │       ├── test_escalation.py           # 7 triggers with charter thresholds
 │       ├── test_robustness.py           # 4 scenarios: nominal/incomplete/503/safety
 │       ├── test_platform.py             # Switch PB-12↔PB-01, prompt adapts, tool set changes
 │       ├── test_resilience.py           # 429→retry→fallback, webhook 422, concurrency
 │       └── test_latency.py              # Wall time + SSE p50/p95 instrumentation
 │
 ├── prototype/                             # Legacy — fragmented code (being migrated to app/)
 ├── .planning/                             # Internal project management (planning docs)
 │   ├── PROJECT.md                        # Project scope + phase checklist
 │   ├── REQUIREMENTS.md                   # 70 requirements (F/T/A/U/D)
 │   ├── ROADMAP.md                        # 8 phases, 48 sub-phases
 │   └── phases/                           # Detailed PLAN.md per phase
 │
 └── submission/                            # Deliverables (Phase 8)
     ├── deck.pdf                          # 10-slide deck per competition rubric
     ├── demo.mp4                          # 10-minute video per rubric
     └── source.zip                        # Source archive
```

---

## 7. Getting Started

### Requirements

- Python 3.11+
- An API key for at least one LLM provider (or a local model via Ollama)

### Install & Run

```bash
# 1. Clone
git clone https://github.com/your-org/PSACodeSprint.git
cd PSACodeSprint

# 2. Install
pip install -r requirements.txt
# pinned: fastapi, uvicorn, langgraph==1.2.11, anthropic, openai,
#         pydantic, pyyaml, httpx, google-generativeai, langsmith

# 3. Set your LLM provider (any one — see Configuration below)
export ANTHROPIC_API_KEY=sk-ant-...          # for Claude
# or: export OPENAI_API_KEY=sk-...          # for GPT-4o
# or: export GEMINI_API_KEY=...             # for Gemini
# or: ollama pull llama3.1:8b               # for local (no key needed)

# 4. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Open the dashboard
open http://localhost:8000/ui/
```

### Docker

```bash
docker build -t psa-nexus .
docker compose up              # reads LLM_PROVIDER, LLM_MODEL, LLM_BASE_URL from env
# or override:
LLM_PROVIDER=ollama LLM_MODEL=llama3.1:8b LLM_BASE_URL=http://host.docker.internal:11434/v1 docker compose up
```

### Run the Demo

| Action | How |
|--------|-----|
| **Happy path** | Dashboard → click **"Run Demo"** → watch the agent query 3 systems, compute the split, and show approval cards |
| **Approve** | Click **Approve** on each HITL card → agent dispatches trucks, holds feeder, updates Tuas |
| **Reject / Modify** | Click **Reject** (shows alternatives) or **Modify** (enter new road/sea numbers → agent re-validates and re-presents) |
| **Inject failure** | After dispatching, click **"Inject Feeder Berth Conflict"** → monitor detects it → agent re-plans → shows emergency card |
| **Switch problem** | Use the **Problem** dropdown → select **PB-01 Berth Delay** → same core, different tools and gates |
| **API trigger** | `curl -X POST http://localhost:8000/webhook/itt-coordination -H "Content-Type: application/json" -d @sample-event.json` |

### Run Tests

```bash
pytest app/tests/ -v                          # all tests
pytest app/tests/test_robustness.py -v        # 4 robustness scenarios
pytest app/tests/test_platform.py -v          # problem switching (PB-12 ↔ PB-01)
pytest app/tests/test_latency.py -v           # wall time + SSE latency
```

---

## 8. Configuration — Switching Problems & Providers

### Switch the Problem (Proves Platform Generalisability)

One YAML file = one problem. The agent core never changes.

```yaml
# app/configs/pb-12-itt.yaml (flagship)       # app/configs/pb-01-berth.yaml (sibling)
problem:                                       problem:
  id: PB-12                                      id: PB-01
  name: "ITT Coordination Failure"                name: "Berth Delay Cascade"
systems: [citos_ppt, citos_tuas,               systems: [vtis, optevoyage, citos_ppt]
           optetruck, feeder, portnet]         tools: [query_vessel_arrival,
tools: [get_itt_candidates,                      check_berth_availability,
        check_road_itt_capacity, ...]                   check_qc_availability, ...]
hitl_gates: 5  |  triggers: 7                 hitl_gates: 2  |  triggers: 7
```

```bash
# Runtime switch — no restart, no rebuild
curl -X POST http://localhost:8000/agent/switch-problem/pb-01-berth
# → {"problem_id": "pb-01-berth", "systems": ["vtis", ...], "tools": ["query_vessel_arrival", ...]}

# Or use the dashboard dropdown:  PB-12 ↔ PB-01
```

The system prompt, tool list, HITL gates, and cost model all regenerate from the active YAML — `build_system_prompt(config)` and `registry.register_for_problem(id)` do the work.

### Switch the LLM Provider (Provider-Agnostic)

Any of 8 provider names. Hosted, local, or any OpenAI-compatible API.

```yaml
# Hosted — Claude
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  api_key_env: ANTHROPIC_API_KEY

# Hosted via OpenRouter — any model, one key
llm:
  provider: custom
  model: anthropic/claude-sonnet-4
  base_url: https://openrouter.ai/api/v1
  api_key_env: OPENROUTER_API_KEY

# Local — Ollama (no API key, runs on your machine)
llm:
  provider: ollama
  model: llama3.1:8b
  base_url: http://localhost:11434/v1

# With automatic fallback
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  fallback_provider: openai
  fallback_model: gpt-4o
```

```bash
# Or via environment (no YAML edit needed)
LLM_PROVIDER=custom LLM_MODEL=qwen3:8b LLM_BASE_URL=http://localhost:11434/v1 uvicorn app.main:app --reload
LLM_PROVIDER=openai LLM_MODEL=gpt-4o uvicorn app.main:app --reload
```

| Provider Name | Class | Example Models | Needs API Key |
|---------------|-------|---------------|---------------|
| `anthropic` | AnthropicProvider | claude-sonnet-4-20250514 | ANTHROPIC_API_KEY |
| `openai` | OpenAIProvider | gpt-4o | OPENAI_API_KEY |
| `gemini` | GeminiProvider | gemini-2.0-flash | GEMINI_API_KEY |
| `deepseek` | DeepSeekProvider | deepseek-chat | DEEPSEEK_API_KEY |
| `ollama` | CustomProvider | llama3.1:8b, qwen3:8b | No (local) |
| `vllm` | CustomProvider | any HF model | Local server |
| `lmstudio` | CustomProvider | any GGUF | No (local) |
| `custom` | CustomProvider | anything | depends on `base_url` |

The tool adapter (`tool_adapter.py`) translates tool schemas automatically — OpenAI format for `openai/deepseek/ollama/vllm/lmstudio/custom`, `input_schema` for Anthropic, `functionDeclarations` for Gemini.

---

## 9. Evaluation — How This Meets the Competition Rubric

### 6 Mandatory Agentic Capabilities

| # | Capability | How Nexus Demonstrates It | Where to See It |
|---|-----------|--------------------------|----------------|
| 1 | **Event Ingestion & Perception** | Webhook receives `ITT_COORDINATION_REQUEST` (Pydantic-validated, 422 on invalid), extracts 11-field state from structured event + 120 container records | `POST /webhook/itt-coordination` → `app/agent/run.py:create_initial_state()` |
| 2 | **Reasoning & Dynamic Planning** | LLM (via `build_system_prompt(config)`) reasons over 3 system outputs, decides next tool, handles mid-operation deviation (80/40 → 100/20 re-plan) | `agent_node` with `adapt_tools_for_provider()` + `monitor_node` |
| 3 | **Tool & System Orchestration** | 8 tools across 5 systems (plus PB-01's 5 tools), dynamically registered per YAML, called via unified `ToolRegistry` | `app/tools/registry.py` → `tool_node` |
| 4 | **State Tracking & Execution Trace** | LangGraph `MemorySaver(thread_id=run_id)` checkpoints every step; trace exports `time, node, action, result, risk_score, confidence, duration_ms, fallback_used` | `AgentState` + `export_trace()` + LangSmith if key set |
| 5 | **Human-in-the-Loop Controls** | 5 gates (30/15/15/10/30 min) with per-gate timeout actions; approve/reject/modify/timeout; stale-resume guard (422) | `hitl_node` via `interrupt()` + `Command(resume=)` + `handle_hitl_response()` |
| 6 | **Uncertainty & Error Recovery** | 4 robustness scenarios: incomplete data → guardrail → HITL; 503/timeout → retry → fallback; hallucinated tool → error not crash; cost breach → HITL-5 | `test_robustness.py` + `resilience.py` + `fallbacks.py` |

### 4 Evaluation Pillars

| Pillar | How Nexus Addresses It | Evidence |
|--------|----------------------|----------|
| **1. Agentic AI Design & Technical Execution** | LangGraph ReAct loop (thought → tool → observe), state checkpointing, 8-tool orchestration, `risk_score` in every trace entry | Live trace (89.9s, 18K input tokens, confidence 0.95→0.78→0.90) |
| **2. Innovation & Originality** | Non-trivial multi-party coordination — 5 disconnected systems, non-deterministic (live truck/berth/tide data), beyond simple chatbots | Litmus test (12/16 pass, C2 wins 4.80/5.00) + deck slide 2 (why rule engines fail) |
| **3. Scalability & Responsible AI** | Provider-agnostic (8 endpoints), 6 input guardrails, 7 escalation triggers, 4 robustness tests, HITL-calibrated (Tier 2), latency measured (wall <30s, SSE p95), structured logging | `test_latency.py` + `test_resilience.py` + deck slide 7 |
| **4. Presentation & Clarity** | 10-slide deck per rubric + 10-min video per walkthrough spec, ROI math ($8K equation, $1.26M cluster), two presentation flowcharts in this README | `submission/deck.pdf` + `submission/demo.mp4` |

### Submission Assets (Per Competition Requirements)

| Deliverable | Spec | Status |
|-------------|------|--------|
| **10-slide deck** | Per CodeSprint §6.2: problem → gap → solution → autonomy → architecture → trace → guardrails → scalability → ROI → roadmap | Phase 8.5 |
| **10-minute video** | Per CodeSprint §6.3: problem (0:00–2:00) → architecture (2:00–3:30) → live walkthrough normal+robustness+platform-switch (3:30–7:30) → safety/scalability (7:30–9:00) → ROI/close (9:00–10:00) | Phase 8.6 |
| **Running demo** | Webhook → agent → tools → HITL → monitoring → deviation → re-plan + sibling switch + edge case injection | Phases 4–7 |

---

## 10. Key Numbers

| Metric | Value |
|--------|-------|
| Operational sectors mapped | 4 (Berth & Marine, Yard & Transport, Gate & Haulage, Multimodal) |
| Digital systems documented | 7 (CITOS, PORTNET, OptETruck, SmartBooking & iBOX, OptEModal, CALISTA, PSA BDP) |
| Disruption scenarios | 16 across all 4 sectors |
| Problem charters | 16 structured |
| Litmus test passes | 12 of 16 (4 filtered: deterministic / micro-ROI / pure MILP) |
| Root-cause clusters | 6 |
| Winning cluster | C2 — Manual Multi-Party Coordination (4.80/5.00, 7 problems) |
| Flagship problem | PB-12 — Multi-Party ITT Coordination Failure |
| LLM providers | 8 (anthropic, openai, gemini, deepseek, ollama, vllm, lmstudio, custom) |
| Problem configs | 7 YAMLs (PB-01, 02, 04, 09, 10, 11, 12) — one core, swap one YAML |
| Tools (flagship) | 8 (6 pre-approval + 2 post-approval + notification) |
| HITL gates | 5 (30/15/15/10/30 min, per-gate timeout actions) |
| Escalation triggers | 7 (0.85, 1.5h, $10K, 30 min, 60%, 15 min, planner conflict) |
| Shared primitives | 6 (ingestion, planner, orchestrator, HITL, notification, deviation logger) |
| Flagship annual ROI | $384K–$576K |
| Cluster annual ROI (all 7) | $1.26M–$2.08M |
| Planning requirements | 70 (F-01..F-13, T-01..T-18, A-01..A-23, U-01..U-12, D-01..D-08) |
| Sub-phases | 48 (4:9, 5:13, 6:12, 7:8, 8:7 — including resilience + platform) |
| Demo wall time | ~89.9s (normal), ~30s (happy path automated), ~90s (with deviation) |
| Research sources cited | 100+ |

---

## 11. Sources & Research

All research claims are cited with a priority ladder: **PSA official → Singapore government → industry/academic → news.**

| Phase | What Was Researched | Output |
|-------|-------------------|--------|
| **Phase 1** | 4 sectors + 7 systems + 3 flow types (physical, information, decision) | `research/sectors/*.md`, `research/systems/baseline-systems.md`, `research/flows/critical-flows.md` |
| **Phase 2** | 16 disruption scenarios across all sectors (trigger, workaround, cost) | `problems/02-01-disruption-scenarios.md`, `problems/02-02-failure-modes.md`, `problems/02-03-problem-bank.md` |
| **Phase 3** | 5-point litmus test on all 16 → cluster scoring → autonomy level → master charter | `problem-selection/03-01-litmus-test-scores.md`, `problem-selection/03-02-autonomy-level.md`, `buildplan/03-03-master-charter.md` |

**Key references:**
- PSA Singapore — CITOS, PORTNET, OptETruck, Tuas Mega Port
- Singapore Land Transport Authority — Prime mover chassis regulations
- Maritime and Port Authority of Singapore (MPA) — Vessel arrival and berth planning
- Industry standards — Vessel demurrage rates, feeder charter rates, container handling costs

---

*PSA Nexus is a competition prototype — not a production deployment. It runs on mock data that mirrors real PSA operations with Singapore-grounded cost parameters.*

*Built for the PSA Code Sprint: Agentic AI in Action. Deadline: 4 September 2026.*
