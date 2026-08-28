# PSA Nexus — Hackathon Presentation Context

> **Purpose:** Source-of-truth for another AI that will generate the 10-slide deck + 10-minute video script for **PSA Code Sprint: Agentic AI in Action** (deadline 2026-09-04).  
> **Status flag:** Phases 1–6 ✅ COMPLETE. **Phases 7 (Web UI & Integration) + 07.1 (Integrated Verification) + 8 (Polish & Deploy) are PLANNED, NOT BUILT YET.** The deck must show planned UI as *mockups / architecture diagrams* with a **"WIP — UI in build"** banner, not fake screenshots. Do not claim Docker/Railway deploy is live.  
> **Flagship:** `PB-12 — Multi-Party ITT Coordination Failure (PPT → Tuas)`  
> **Platform scope:** Cluster C2 — 7 sibling problems, one LangGraph core, one YAML per problem  
> **Product name:** **PSA Nexus — Agentic Multi-Party Coordination Platform**  
> **Tech stack (locked):** Python 3.11, LangGraph 1.2.11, FastAPI, in-memory state, YAML configs, no DB, SSE streaming, LangSmith optional  
> **Repo root:** this file lives in repo root; canonical docs are `README.md`, `.planning/PROJECT.md`, `buildplan/03-03-master-charter.md` (23 gaps), `.planning/ROADMAP.md`, `CodeSprint.md` (§6.2 deck rubric / §6.3 video rubric)

---

## 1) How to Use This File (instructions for the slide-generating AI)

1. **You are writing a 10-slide deck** per CodeSprint §6.2 rubric (see §13 below). Keep each slide dense-but-readable: title + 3–5 bullets + 1 visual + footer rubric tag.
2. **You are also drafting a 10-minute video script** (5 parts per §6.3). Keep it in speaker-notes, not on slides.
3. **Tone:** judge-facing, operator-credible. No marketing fluff. Every claim must tie to a file:line or charter section you can cite.
4. **Do not invent numbers.** Use the grounded Singapore cost params in §11 or cite `buildplan/03-03-master-charter.md:§5`.
5. **Phase 7–8 gap:** Any UI screenshot slot should render a *wireframe/mock* with caption "Planned — Phase 7 (SSE + HITL cards + problem switcher)". Any deploy slot should say "Local Docker (localhost:8000) — Phase 8 pending".
6. **Code snippets:** §14 has curated slots with exact `file:line` refs. Drop 1–2 *short* snippets per technical slide (keep under 12 lines). If you need longer, put it in appendix (slides 11+).
7. **Visual rule:** Every slide gets one visual — architecture diagram, flow chart, table, or cost equation. No wall-of-text slides.
8. **Final output:** 10 slides + appendix + speaker notes + demo checklist (§15).

---

## 2) One-Liner & Elevator Pitch

**One brain, seven problems.** PSA Nexus coordinates multi-party operations at PSA Singapore. One LangGraph reasoning core + 7 YAML configs + 8 LLM providers + live HITL controls. Flagship demo: moving **120 containers PPT → Tuas** (road vs sea split) when CITOS instances are not integrated and the road/sea split is today negotiated by phone.

**Before → After:**
- Before: 4–8 hours, 12+ phone calls, $8,450/incident, vessel waits.
- After: ~27 minutes, 2 human approvals, $450/incident (agent cost $50), vessel on time.
- Savings: **$8,000/incident → $384K–$576K/yr flagship → $1.26M–$2.08M/yr across cluster.**

```
PSA Nexus
├── One LangGraph core — same reasoning engine for every problem
├── 7 YAML configs — swap one file, get a different problem
├── 8 LLM providers — Claude, GPT-4o, Gemini, DeepSeek, Ollama, vLLM, LM Studio, any OpenAI-compatible API
└── Live dashboard (PLANNED Phase 7) — watch the agent think, approve its plans, inject edge cases
```

---

## 3) Problems We Found (ground truth)

### 3.1 The 4 PSA sectors we mapped (Phase 1 → `research/`)
- **Berth & Marine:** vessel traffic, berth allocation, tidal windows, QC split, stowage/stability, transhipment cut-offs.
- **Container Yard & Internal Transport:** AGV fleet, aRMG job sequencing, stacking, reefers, DG yard, empty depot.
- **Gate & External Haulage:** AGS/OCR, OptETruck slot scheduling, Truck Round Trip (TRT), ITT (PPT↔Tuas), demurrage.
- **Multimodal Logistics:** sea-air (OptEModal), PSCH warehousing, TradeNet customs, CALISTA visibility.

Baseline systems mapped (`research/systems/baseline-systems.md`):
`CITOS®` (TOS brain), `PORTNET®` (B2B community), `OptETruck` (TMS), `SmartBooking™/iBOX™` (depot-gate), `OptEModal` (sea-air), `CALISTA®/P!NG™`, `PSA BDP`.

### 3.2 The 16-candidate Problem Bank (`problems/02-03-problem-bank.md`)
We mined 16 “something changed” disruptions where static rules fail:

| ID | Short Title | Sector | Core Friction | Systems Spanned | Est. Cost / Incident | Freq / Month |
|---|---|---|---|---|---|---|
| **PB-01** | Cascading Berth Delay & Tidal Lockout | Berth | ETA slip → stale berth plan, tidal miss, QC + feeder cascade | VTIS, OptEVoyage, CITOS, PORTNET, FMS | $58K–$132K | 2–3 |
| **PB-02** | DTQC Breakdown & Terminal Cascade | Berth | QC down 25% → AGV queue → vessel delay | CITOS, ROCC, FMS, PORTNET | $16K–$24K | 4–6 |
| **PB-03** | Late DG Declaration & IMDG Hold | Berth | DG amendment → IMDG conflict → manual re-stow + MPA wait | PORTNET, CITOS, MPA DGPE | $7.6K–$23K + penalty | 1–2 |
| **PB-04** | Transhipment Missed-Connection (100+ ctrs) | Berth | Mother delay 8h → 100+ ctrs miss feeders → hold vs roll dilemma | CITOS, PORTNET, OptEVoyage | $6.5K–$36K | 3–5 |
| **PB-05** | Reefer Cold-Chain Excursion (Pharma) | Yard | ARMS alarm, unknown root cause, 2–4h spoilage window | ARMS, CITOS, shipping line | $505K+ (loss) | 5–8 |
| **PB-06** | Yard Block Buffer Overflow | Yard | Vessel delay → yard overflow → re-handles vs loading trade-off | CITOS, FMS, aRMG, gate | $12K–$20K | 6–10 |
| **PB-07** | 5G Outage Degrading AGV Fleet | Yard | Latency 10→40ms → de-rating → 20–30% throughput loss | 5G/Singtel, FMS, CITOS | $21K–$65K | 1–2 |
| **PB-08** | eDO/VGM Discrepancy Gate Cascade | Gate | eDO not released / VGM >5% → AGS block → queue spillover | AGS/OCR, PORTNET, weighbridge, OptETruck | $1K–$2K | 8–12 |
| **PB-09** | Expressway Blockage (40% trucks miss slots) | Gate | Traffic → 40% hauliers miss slots → yard/loading cascade | OptETruck, SmartBooking, PORTNET, CITOS | $15K–$20K | 2–4 |
| **PB-10** | Sea-to-Air Cut-Off (OptEModal) | Multimodal | Vessel delay 8h → 50 ctrs miss 12h sea-air window → rebook | OptEModal, CITOS, TradeNet, SATS | $18K–$73K | 1–2 |
| **PB-11** | Customs Inspection Hold (Sea-Air) | Multimodal | Random hold → no partial release → cross-timezone docs | TradeNet, CALISTA, OptEModal | $3.7K–$59K | 2–4 |
| **PB-12** | **Multi-Party ITT Coordination Failure (FLAGSHIP)** | Multimodal | PPT→Tuas 120 ctrs, road/sea split guessed by phone, CITOS not integrated | CITOS PPT, CITOS Tuas, OptETruck, PORTNET/feeder | **$15.6K–$29K (exposure); $8K recoverable** | **4–6** |
| PB-13 | Multiship QC Scheduling Conflict | Berth | Multi-vessel QC re-optimisation NP-hard, manual solver | CITOS, FMS, ROCC, PORTNET | $20K–$55K | 3–5 |
| PB-14 | iWX Reuse Marketplace Race Condition | Yard | Stale iWX prediction → haulier deadhead | iWX, CITOS, PORTNET, OptETruck, iBOX | $200–$800 | 15–25 |
| PB-15 | QC→aRMG Synchronisation Failure | Yard | QC rate change → aRMG starved/overloaded → yard congestion | CITOS, FMS, ROCC, aRMG | $3K–$8K | 8–12/day |
| PB-16 | System-Wide Empty Imbalance | Gate | Depot surplus/deficit → 15% empty trips persist | iWX, OptETruck, iBOX, CITOS, PORTNET | $50K–$150K/mo | — |

> Historical detail lives in `problems/02-01-disruption-scenarios.md` and `problems/02-02-failure-modes.md`.

### 3.3 Clustering & Why Cluster C2 Won
We clustered 16 problems by shared root cause. **Cluster C2 — Manual Multi-Party Coordination** scored **4.80/5.00** (highest “agentic sweet-spot”): 7 problems (PB-01, PB-02, PB-04, PB-09, PB-10, PB-11, PB-12) unified by *no shared system of record + phone-call negotiation + cross-system handoff gaps*. Verdict: one agentic platform pattern solves all 7 with 6 shared primitives (see §7).

### 3.4 Litmus Test (5 filters — all must pass)
Applied per `problem-selection/03-01-litmus-test-scores.md`:

| Filter | Question | PB-12 Verdict |
|---|---|---|
| **L1 Non-deterministic** | Multi-step reasoning & adaptive re-plan, not a lookup? | ✅ Yes — split depends on live truck count, feeder status, tide windows, traffic |
| **L2 Multi-system** | Spans 3+ PSA systems? | ✅ Yes — CITOS PPT, CITOS Tuas, OptETruck, PORTNET/feeder |
| **L3 Real cost** | Failure costs real $ every month? | ✅ $8K/incident, 4–6/mo |
| **L4 Needs human judgment** | Some decisions too risky to fully automate? | ✅ $2,400 truck dispatch / $800/hr feeder hold needs human sign-off |
| **L5 Macro-impact** | Moves a number leadership cares about? | ✅ Vessel dwell time, $384K–$576K/yr (cluster $1.26M) |

12/16 problems passed all 5; C2 had the densest pass rate.

### 3.5 Autonomy Level (the “Autonomy Trap” callout)
Selected **Tier 2 — Human-in-the-Loop Exception Solver** per `problem-selection/03-02-autonomy-level.md`:
- Agent gathers data + drafts plans autonomously, **pauses for 1-click human confirmation** before any state-mutating action.
- Rationale: HIGH financial exposure ($10K+ per action) + multi-party authority boundaries + 30–60 min cross-terminal data asymmetry.
- Quote for deck (from CodeSprint brief): *“Higher autonomy is not automatically better. Teams should select an appropriate level based on use case, operational risk, and available controls.”*

---

## 4) Flagship Deep Dive: PB-12 — Multi-Party ITT Coordination Failure

**Story in one line:** A vessel at Tuas needs 120 containers from PPT. Road (OptETruck) vs sea (feeder via PORTNET) split is guessed on the phone. Feeder gets a berth conflict *after* trucks are already dispatched. Vessel waits.

**Key facts (charter §1–2):**
- **Persona:** PSA ITT Operations Controller (PPT).
- **Cargo:** 120 containers = 40×40ft (FEU) + 80×20ft (TEU) = **160 TEU**, **80 truck trips if 100% road** (LTA: 1×40ft OR 2×20ft per chassis). Affects blocks B-07, B-08, B-12, B-14.
- **Systems:** CITOS PPT (readiness), OptETruck (road), PORTNET/feeder (sea), CITOS Tuas (loading). PPT ↔ Tuas CITOS not integrated (PORTNET lag 30–60 min).
- **Route:** PPT → West Coast Hwy → AYE → Tuas Port Blvd (~35 km, 45 min off-peak / 95 min peak).
- **Sibling proof:** Same failure pattern appears in PB-01 (berth), PB-02 (crane), PB-04 (feeder), PB-09 (expressway), PB-10/11 (customs/sea-air) — all “phone-call coordination”.

**What breaks (no system owns the split):**
- CITOS PPT knows what’s ready; CITOS Tuas knows receiving capacity — they don’t talk.
- OptETruck knows trucks; feeder operator knows berth/tide — they don’t talk.
- No optimiser computes road/sea trade-off under tidal + truck + block constraints in real time.

---

## 5) Baseline vs Agentic Delta (the before/after slide)

### As-Is Manual (current — 12 steps, 4–8 hours, ~12 phone calls)
`buildplan/03-03-master-charter.md:§2`:
1. PPT planner spots 120 in CITOS PPT (T+0)
2. Calls Tuas planner (T+5) — Tuas suggests 60/40 split
3. Calls OptETruck (T+20) — dispatches 15 trucks, 5 delayed by gate
4. Calls feeder operator (T+30) — reports berth conflict, departure slips 1400→1600
5. Re-calls Tuas (T+40) + re-sequences QC (T+50)
6. Road arrives T+3h (10 trucks, 60 ctrs), sea arrives T+6h, vessel loading delayed 2h (T+8h)  
**Root failure:** feeder delay discovered at T+35 min *after* trucks already rolling → can’t re-route.

### To-Be Agentic (PSA Nexus — 17 steps, ~27 min, 2 approvals)
Charter §2 + `README.md:§4`:
1. T+0 webhook → agent receives `ITT_COORDINATION_REQUEST` (≥50 ctrs, departure >now+2h, weight/block guards)
2. T+0.5–1.5 min parallel tool calls: T1 candidates, T2 road (20 trucks, 90 min), T3 sea (feeder window 1400–1600 + tidal)
3. T+2.5 min T4 compute split: **80 road (60 trips) + 40 sea = $10,400** (vs $12K baseline all-road; saves $1,600 + avoids 20 trips on AYE)
4. T+3 min HITL-1 “Approve ITT Split” (30 min timeout) → approve T+5
5. T+5.5–6.5 min dispatch (HITL-2), feeder hold (HITL-3), Tuas loading sequence (HITL-4)
6. **T+21 min monitor re-queries T3 → detects berth conflict** → confidence 0.92→0.78
7. T+22 min re-compute 100 road / 20 sea (70 trips ×$150 + 20×$35 = $11,200), HITL-5 emergency → approve T+25 → delta +4 trucks + second Tuas update → done T+27  
**Key win:** conflict detected *before* road leg fully dispatched; agent re-plans instead of crashing.

> Visual tip: split the slide vertically — left = phone-call spaghetti, right = agent timeline with HITL diamonds and monitor loop highlight.

---

## 6) Solution Overview: PSA Nexus Platform

**Thesis:** Don’t build 7 tools. Build **one intelligent core** and swap what it knows per problem.

| Layer | What It Does | Where |
|---|---|---|
| **Agent Core** | LangGraph state machine — reasons, calls tools, asks humans when unsure, recovers from failures | `app/agent/graph.py:64` (4 nodes: agent/tools/hitl/monitor + MemorySaver) |
| **Tool Registry** | Plug-in system — each problem registers its own tools | `app/tools/registry.py` (TOOLSETS, register_for_problem) |
| **Problem Configs** | One YAML per problem — systems, tools, HITL gates, triggers, costs | `app/configs/pb-12-itt.yaml`, siblings `pb-01/02/04/09/10/11` |
| **Live Dashboard** *(PLANNED)* | Real-time SSE streaming — thoughts, tool calls, approval cards, edge injection, problem switcher | `app/agent/sse.py`, `app/main.py:/agent/stream`, `app/ui/` (Phase 7) |
| **LLM Abstraction** | 8 providers behind one interface — swap with `provider:` line | `app/shared/provider.py` (anthropic/openai/gemini/deepseek/ollama/vllm/lmstudio/custom) |

**Proof of generalisability (not a one-off ITT demo):**
- Same graph runs PB-12 *and* PB-01 (Berth Delay) by `POST /agent/switch-problem/pb-01-berth` → registry clears + re-registers VTIS/OptEVoyage/CITOS-berth tools, prompt re-templates via `app/agent/prompts.py:build_system_prompt(config)` (Phase 4.8).
- Deck must show side-by-side: `PB-12: HITL 5 gates, 8 tools, cost $10.4K` vs `PB-01: 2 gates, 5 tools, berth/tide constraints`.

---

## 7) Architecture — System View

```
External mocks (same FastAPI port 8000):  CITOS PPT, CITOS Tuas, OptETruck, PORTNET/feeder, VTIS/OptEVoyage (PB-01)
                                              │
FastAPI app/main.py ── POST /webhook/itt-coordination (T6, validates ITTCoordinationEvent, bootstraps 11-field initial_state)
                      ── POST /agent/switch-problem/{id} (yaml swap + registry)
                      ── POST /agent/hitl/respond (approve/reject/modify/timeout)
                      ── POST /agent/inject-edge-case (mutates app/mocks/data.py per-run isolated)
                      ── GET  /agent/stream/{run_id} (SSE with replay buffer)
                      ── GET  /ui/ (planned vanilla HTML/JS)
                              │
LanGraph graph (app/agent/graph.py:95) ─  agent ─┬─▶ tools ─▶ agent (loop)
                                                   ├─▶ hitl (interrupt) ─▶ agent
                                                   └─▶ monitor ─▶ hitl / agent / END
                              │
State: AgentState (app/agent/state.py:10) — messages, tool_results, hitl_pending/history, confidence, escalation, trace, deviation_log, problem_config, run_id (=thread_id)
```

**Key invariants:**
- `run_id === thread_id` for `MemorySaver` checkpoint (`app/agent/run.py`).
- `interrupt({approval_card})` is the ONLY pause mechanism (single `hitl` node, not 5). Resume via `Command(resume=decision)`.
- `SSEBroadcaster` replays buffered events for late-join clients (`app/agent/sse.py`).
- Tool invocation = *in-process Python calls* (charter G-06 decision — faster, no extra HTTP hop). Mock data lives in `app/mocks/data.py` (per-run isolated maps `_feeder_overrides`, `_stale_overrides`).

---

## 8) How the Agent Thinks (ReAct Loop + Deterministic HITL Fast-Path)

`app/agent/nodes.py:15 agent_node` (Phase 6.3):
1. **Fast path** (before LLM): if next HITL gate in charter sequence is due (HITL-1→2→3→4 based on `context.split_result` / `context.dispatched` / `context.tuas_sequence`), set `hitl_pending` immediately — avoids 30 s LLM wait and guarantees charter sequencing even when LLM is a mock.
2. Build messages via `app/agent/prompts.py` (templated from `ProblemConfig` — not hardcoded to PB-12).
3. Resolve provider from `problem_config.llm` or active YAML; fallback to `_mock_provider_for_state` (deterministic planner that synthesises `get_itt_candidates → check_road + check_sea → compute_itt_split → …` in charter order so tests/E2E work without a real API key).
4. Adapt tool schemas per family via `app/shared/tool_adapter.py` (OpenAI, Anthropic `input_schema`, Gemini `functionDeclarations`).
5. `chat_with_rate_limit` (Phase 6.12) handles 429 → retry → fallback provider.
6. Validate tool names against registry; hallucinated → error ToolResult + retry message listing `registry.list()`.
7. Run 7 escalation checks; any trigger → set `hitl_pending = HITL-5`.
8. Write trace + SSE (`agent_thinking`, `tool_call`, `escalation`, `trace_entry`, `confidence_update`, etc.), risk_score `= f(confidence, escalation)`.

`app/agent/nodes.py:472 tool_node` (Phase 6.4): parallel calls, per-tool timeout vs 503 distinction, fallback via `FALLBACKS` (e.g. `cached_road_capacity`), HITL approval guard (`post_approval=True` tools block until correct gate approved), full output kept in `context` for downstream, truncated output in checkpoint/messages to avoid `StateGraph` deepcopy blow-up (120 → 5 containers kept).

`app/agent/monitor.py` (Phase 6.10): after HITL-4 + `dispatched`, re-queries T3, detects `berth_status: conflict` → logs deviation, drops confidence 0.95→0.78, re-runs T4 (80/40→100/20), raises HITL-5 emergency, on approve fires delta `+4 trucks` + second `update_tuas_loading_sequence`.

**Routing (pure, no mutation):**
- `route_after_agent` (`app/agent/graph.py:16`): `pending_tool_calls → tools`, `hitl_pending|escalation → hitl`, `dispatched+hitl_4+not_monitored → monitor`, else END.
- `route_after_monitor` (`app/agent/graph.py:51`): `hitl_pending|escalation → hitl`, `deviation_log non-empty → agent`, else END.

**Traceability for slides:** put the LangGraph diagram + hit “pause” icon at each `interrupt()` diamond.

---

## 9) Tools & Mock Environment

### PB-12 Toolset (Phase 5 — all return `ToolResult(output, confidence, metadata)`)
| # | Charter Name | File | What It Returns (demo fixture) |
|---|---|---|---|
| T1 | `get_itt_candidates` | `app/tools/container_readiness.py` | 120 ctrs (40×40ft + 80×20ft = 160 TEU, blocks B-07/08/12/14, 3 DG, LTA trips 80) |
| T2 | `check_road_itt_capacity` | `app/tools/road_itt.py` | 20 trucks, 90 min transit, road conditions AYE/West Coast/Tuas Blvd, peak-aware `transit_*_min` |
| T3 | `check_sea_itt_capacity` | `app/tools/sea_itt.py` | Feeder 800 TEU / 620 occupied / 180 avail, window 1400–1600, tidal Port Klang 23:00 + 5:00 must-depart |
| T4 | `compute_itt_split` | `app/tools/optimiser.py:83` | **80 road (60 trips ×$150=$9K) + 40 sea ($0 charter + 40×$35=$1,400) = $10,400**; alternatives 100/20 & 60/60; `cost_vs_baseline` + `roi` + `guardrails_checked` + `constraints_validated` |
| T5 | `update_tuas_loading_sequence` | `app/tools/tuas_loading.py` | `Bay14(road@14:30)→Bay12→Bay10(sea@16:30)→Bay08`, QC-07/08 adjustments, margin 30 min |
| T6 | *(webhook entrypoint)* | `app/main.py:POST /webhook/itt-coordination` | `ITTCoordinationEvent` (≥50 ctrs, departure >now+2h, weight 0–60000, block ≤4500) → 11-field `initial_state` |
| T7 | `dispatch_road_itt` | `app/tools/dispatch_road_itt.py` | Requires HITL-2; `num_trucks + route` + delta support |
| T8 | `request_feeder_hold` | `app/tools/request_feeder_hold.py` | Requires HITL-3; operator may decline |
| T9 | `notify_parties` | `app/tools/notify.py` | Primitive #5 — logs to trace + publishes SSE `notification`, mocks to `app/mocks/data.py:notification_log` |
| — | Edge hooks *(not tools)* | `app/tools/edge_cases.py` | `inject_feeder_berth_conflict()` / `inject_stale_data()` — mutate `app/mocks/data.py` (per-run isolated) so next T3 sees conflict |

### Sibling stub (PB-01 — proves platform, Phase 5.11)
`app/tools/pb01/` — `query_vessel_arrival`, `check_berth_availability`, `check_qc_availability`, `compute_berth_reassignment`, `notify_vessel_operator` + mocks `app/mocks/routers/vtis.py` / `optevoyage.py` / `berth.py`. Switch via `POST /agent/switch-problem/{id}` (Phase 4.8, `app/agent/problem_switcher.py`).

### Mocks (Phase 4.2)
`app/mocks/data.py` (canonical fixtures), `app/mocks/routers/citos_ppt.py`, `citos_tuas.py`, `optetruck.py`, `feeder.py`, `portnet.py`, `vtis.py`, `optevoyage.py`, `berth.py`, `app/mocks/edge_cases.py`. Data is per-run isolated via `_feeder_overrides: Dict[run_id, FEEDER_DATA]` + `_stale_overrides`.

---

## 10) Human-in-the-Loop & Escalation (the “Responsible AI” slide)

### 5 HITL Gates (`app/hitl/models.py:54 HITL_GATES`, `app/hitl/gates.py:hitl_node` single node with `interrupt()`, `app/hitl/handler.py:handle_hitl_response`)
| Gate | Trigger | Label | Timeout | Timeout Action | Slide Callout |
|---|---|---|---|---|---|
| **HITL-1** | Split computed (T4 done) | Approve ITT Split (cost card) | 30 min | **Escalate to Duty Manager** | “Commit $10.4K?” |
| **HITL-2** | Truck dispatch ready | Approve Truck Dispatch (count + route) | 15 min | **Cancel Dispatch** | “State mutation — OptETruck” |
| **HITL-3** | Feeder hold ready | Approve Feeder Hold (hold hrs + tide risk) | 15 min | **Escalate** | “Commercial + tidal risk” |
| **HITL-4** | Tuas sequence ready | Approve Loading Sequence Update (bay→QC) | 10 min | **Hold Current Sequence** | “Affects live QC ops” |
| **HITL-5** | Any escalation fires | Escalate to Duty Manager | 30 min | **Halt Workflow** | “Agent cannot resolve — human must” |

**Disapproval flows (charter §4):**
- **REJECT** → log reason + present `alternatives[]` from T4, or escalate to HITL-5 if no viable alternative.
- **MODIFY** → re-validate vs LTA chassis/feeder capacity/timeline + re-run T4 + re-present cost + re-ask approval.
- **TIMEOUT** → fire `timeout_action` per gate; HITL-5 second-level rule: if Duty Manager also silent 30 min → `halt_workflow` entirely.
- **Stale resume:** late `POST /agent/hitl/respond` after timeout → 422 stale error.

### 7 Escalation Triggers (`app/agent/escalation.py:149 TRIGGERS` — exact charter thresholds)
| # | Trigger | Threshold | Action | When It Fires in Demo |
|---|---|---|---|---|
| 1 | Low confidence | `< 0.85` | escalate_to_human | Confidence drops 0.92→0.78 on deviation |
| 2 | Feeder hold > tidal tolerance | `> 1.5 h` | escalate_to_duty_manager | Re-computed hold post-conflict |
| 3 | Financial recovery cost | `> $10,000` | escalate_to_duty_manager | Only on high-cost injected scenario (nominal uses `action_cost` = savings $1.6K so stays green) |
| 4 | Data staleness | `> 30 min` | escalate_to_human | Injected via `inject_stale_data` or `data_age_minutes` |
| 5 | Road capacity | `< 60% required` | escalate_to_human | Checked as `available/road_trips` after split |
| 6 | Feeder unresponsive | `> 15 min` | escalate_to_human | `feeder_response_elapsed_minutes` |
| 7 | Planner conflict | `planner_recommendations_conflict == true` | escalate_to_duty_manager | Mutually exclusive HITL decisions on same gate |

All triggers are checked twice: inside `agent_node` (post-LLM) and inside `tool_node` (post-tool-batch). Any fire → `escalation` + `hitl_pending = HITL-5`.

### Confidence & Risk
- **Primary:** LLM self-assessment via structured JSON `confidence` 0.0–1.0 (`app/agent/confidence.py:extract_confidence`).
- **Fallback:** deterministic score from tool-quality metrics.
- **Threshold 0.85** triggers #1; `risk_score = 1 - confidence + 0.15*escalation_count` (shown every trace entry).

---

## 11) Guardrails & Resilience (CodeSprint Phase 5.3 — the “Safety” slide)

### 6 Input Validation Guardrails (`app/agent/validation.py` — checked at webhook + before T4 + post-approval)
| Guard | Rule | On Failure |
|---|---|---|
| Weight bounds | `0 < weight_kg ≤ 60000` (checked over full `_full_for_logic` containers, not truncated 5) | Reject container, `weight_bounds` failure → confidence 0.6 → escalation |
| Yard block capacity | `containers_per_block ≤ 4500 TEU` | Overflow routing |
| Truck availability | `available_trucks ≥ 1` | Fall back to 100% sea |
| Feeder capacity | `sea_containers ≤ feeder_available_teu` | Reduce sea, increase road |
| Tuas departure margin | `itt_arrival < vessel_departure - 60 min` | Reject split — insufficient margin |
| Feeder tidal window | `feeder_departure < tidal_window_deadline` | Enforce hold limit |

### 4 Required Robustness Scenarios (`app/tests/test_robustness.py`)
- **S1 Nominal:** 120 ctrs, all healthy → agent resolves, HITL-1..4 approve, dispatch + Tuas done, `deviation_log == []`.
- **S2 Incomplete Data:** `weight_kg` missing → guardrail fires → agent queries secondary source or asks operator (“weight unknown, verify?”).
- **S3 API Failure:** T2 returns 503 / timeout → agent detects, logs `tool_error` to trace, retries, uses `FALLBACKS` (`cached_road_capacity`), alerts via `notify_parties`. 503 vs timeout distinguished for audit.
- **S4 Safety Escalation:** T4 cost >$10K or vessel shift >2h → agent halts, produces HITL-5 card. (Skipped pre-Phase 6; green after `hitl/monitor` landed.)

### Other resilience
- Rate limit: `429 → retry → fallback_provider` (`app/agent/resilience.py:chat_with_rate_limit`).
- Hallucinated tool → error ToolResult + message `“Unknown tools: … Available: …”`.
- Partial batch: remaining tool calls continue if one fails.
- Per-run isolation: mocks + broadcaster buffers keyed by `run_id`; concurrent runs don’t leak.

---

## 12) Cost Model & ROI — The Math Slide (don’t fudge numbers)

**Grounded params (Singapore, `buildplan/03-03-master-charter.md:§5` + `app/configs/pb-12-itt.yaml:cost_params`):**
- Mother vessel demurrage $2,500/hr, Feeder charter $800/hr, Road trip PPT→Tuas (35 km) $150, LTA chassis 1×40ft OR 2×20ft/truck, Sea marginal charter **$0** (scheduled feeder), Handling $35/lift, Re-handle $35/move, Missed connection $150/ctr, Block max 4,500 TEU, AgV not applicable (external haulier).

**Per-incident equation (charter §5, `app/tools/optimiser.py:35 compute_roi` = `8450 − 450 = 8000`):**
```
Manual:  vessel 2h×$2500 ($5,000) + 5 extra trucks×$150 ($750) + feeder hold 2h×$800 ($1,600) + 20 re-handles×$35 ($700) + staff 8h×$50 ($400) = $8,450
Agent:   vessel 0 + trucks 0 + feeder 0.5h×$800 ($400) + re-handles 0 + agent amortised ($50)               =   $450
Savings per incident = $8,450 − $450 = $8,000
```

**Transport-only delta (tool-level, `app/tools/optimiser.py:cost_vs_baseline`):**
- Baseline 100% road: 80 trips × $150 = $12,000
- Optimised: 60 trips × $150 ($9,000) + 40 ctrs × $35 ($1,400) = **$10,400**
- Direct transport savings: **$1,600** + “20 fewer trips on AYE — avoids peak congestion near Pandan” (use as footnote).

**Deviation emergency (T+21 min):** re-computed 100/20 split = 70×$150 + 20×$35 = **$11,200** (vs original $10,400) — costs $800 more but avoids $5,000 missed-connection penalty → net win for slide.

**Annualised:**
- Flagship PB-12: 4–6/mo × $8K × 12 = **$384K–$576K/yr**
- Cluster C2 (7 problems): 18–30/mo = **$1.26M–$2.08M/yr**

Cluster table for slide (`buildplan/03-03-master-charter.md:§5.3`):

| Problem | /mo | $/incident | /mo $ | /yr $ |
|---|---|---|---|---|
| PB-01 Berth Delay | 2–3 | $8K | $16–24K | $192–288K |
| PB-02 DTQC Breakdown | 4–6 | $4K | $16–24K | $192–288K |
| PB-04 Missed Feeder | 3–5 | $5K | $15–25K | $180–300K |
| PB-09 Expressway Blockage | 2–4 | $5K | $10–20K | $120–240K |
| PB-10 Sea-Air Cut-Off | 1–2 | $10K | $10–20K | $120–240K |
| PB-11 Customs Hold | 2–4 | $3K | $6–12K | $72–144K |
| **PB-12 ITT (flagship)** | **4–6** | **$8K** | **$32–48K** | **$384–576K** |
| **Total C2** | 18–30 | — | $105–173K | **$1.26–2.08M** |

---

## 13) Implementation Status — Honest Trail (critical for credibility)

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| **1–3 Research** | 4 sectors, 7 systems, 16 problems, litmus test, C2 win | ✅ DONE 2026-08-17 | `research/`, `problems/`, `problem-selection/`, `buildplan/03-03-master-charter.md` |
| **4 Foundation** | FastAPI scaffold, 7 YAMLs complete, `provider.py` + `tool_adapter.py`, `registry.py`, `app/mocks/` merged, `shared/models.py` | ✅ DONE 2026-08-27 | 57 tests pass (`app/tests/`), `POST /agent/switch-problem/{id}` live |
| **5 Tools** | 8 PB-12 tools + `notify` + PB-01 stubs + ROI + 4 robustness S1–S3 (S4 skipped) | ✅ DONE 2026-08-27 | 127 pass / 3 skipped, `verify: 80/40=$10,400` in `app/tests/test_tools.py` |
| **6 Agent Core** | LangGraph 4 nodes, 5 HITL `interrupt`+`Command`, 7 triggers, monitor deviation 100/20, E2E both paths | ✅ DONE 2026-08-28 | `app/tests/test_agent_e2e.py` 5 green (37–43 s happy/deviation, `confidence 0.95→0.78→0.90`, `deviation_log` populated) |
| **6.5 Wiring & Cleanup** | requirements UTF-8, lifespan validation, HITL timeout scheduler, SSE `confidence/notification`, YAML consistency, `prototype/` delete, LangSmith | ⬜ NOT STARTED | Planned 6 sub-phases, blocks Phase 7 |
| **7 Web UI** | SSE replay buffer, HTML/JS dashboard, HITL cards, edge injection, demo runner, trace/deviation display, problem switcher, notifications | ⬜ **NOT STARTED** | Deck must render *mockups/wireframes* with “PLANNED” badge |
| **07.1 Integrated Verification** | System-level E2E via HTTP+SSE, HITL 5×5 matrix, resilience chaos, cross-problem PB-12↔PB-01 regression, observability audit | ⬜ NOT STARTED | Gate `pytest app/tests/integration/ -v` blocks Phase 8 |
| **8 Polish & Deploy** | Dockerfile, compose, local smoke, deck, video | ⬜ NOT STARTED | `8.3 Railway/Render DISABLED — local-only demo` per ROADMAP; local `docker compose up` → `localhost:8000` |

**What the deck must NOT claim:**
- No “Live dashboard screenshot” — use wireframe: header “PSA Nexus”, left = agent status + confidence, center = streaming reasoning + tool log, right = HITL card + trace sidebar, bottom = edge injection buttons (“Inject AFTER dispatch” hint) + problem switcher dropdown (PB-12↔PB-01).
- No “Deployed at https://…” — say “Local container — `http://localhost:8000/ui/` (planned Docker, Phase 8)”.
- HITL timeout scheduler is *planned* (6.5.3) — mention “5 timeouts 30/15/15/10/30 with per-gate actions; auto-escalation WIP”.

---

## 14) Code Snippet Slots (fill exactly these — short, judge-readable)

> Replace each placeholder with a trimmed snippet (≤12 lines). Keep syntax-highlighted. Cite file:line.

### SNIPPET A — LangGraph wiring (4 nodes, MemorySaver, thread_id) — *Slide 5 Architecture*
```python
# app/agent/graph.py:64 build_graph()
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)   # LLM + HITL gating
graph.add_node("tools", tool_node)    # registry dispatch
graph.add_node("hitl", hitl_node)     # interrupt()
graph.add_node("monitor", monitor_node) # re-query T3 → deviation
graph.add_conditional_edges("agent", route_after_agent,
    {"tools":"tools","hitl":"hitl","monitor":"monitor", END: END})
_compiled_graph = graph.compile(checkpointer=MemorySaver())
# call site: await graph.ainvoke(state, config={"configurable":{"thread_id": run_id}})
```
**Why this snippet:** Proves HITL is first-class LangGraph, not a hack.

### SNIPPET B — Single HITL node with interrupt (not 5 nodes) — *Slide 7 Guardrails*
```python
# app/hitl/gates.py — hitl_node
from langgraph.types import interrupt
def hitl_node(state):
    card = build_approval_card(state["hitl_pending"], state["context"]["split_result"])
    decision = interrupt({"gate_id": state["hitl_pending"]["gate_id"], "approval_card": card, "timeout": state["hitl_pending"]["timeout_seconds"]})
    return handle_hitl_response(state, decision) # approve / reject→alternatives / modify→re-run T4 / timeout→per-gate action
# resume: await graph.ainvoke(Command(resume={"decision":"approve","reason":"ok"}), config={"configurable":{"thread_id": run_id}})
```
**Why:** Correct `interrupt` + `Command(resume=)` + `thread_id` pattern that reviewers check for.

### SNIPPET C — ToolRegistry + problem switching (platform proof) — *Slide 8 Scalability*
```python
# app/tools/registry.py + app/agent/problem_switcher.py
registry.register_for_problem("pb-12-itt")      # → 8 tools: get_itt_candidates … notify_parties
# POST /agent/switch-problem/pb-01-berth
# → load_problem_config("pb-01") → registry.clear(); registry.register_many(pb01_tools)
#   → build_system_prompt(config) re-templates “You are Nexus, coordinating Berth Delay”
registry.register_for_problem("pb-01-berth")    # → 5 tools: query_vessel_arrival … notify_vessel_operator
```
**Why:** One line = one new problem. No code fork.

### SNIPPET D — T4 optimiser canonical output + guardrails — *Slide 6 Decision Logic*
```python
# app/tools/optimiser.py:83 OptimiserTool.execute() → ToolResult
# Input: candidates (120), road_capacity (20 trucks), sea_capacity (180 TEU avail), tuas_vessel_departure
# Output:
{
  "optimal_split": {"road_containers":80, "road_trips":60, "road_cost":9000,
                    "sea_containers":40, "sea_terminal_handling_cost":1400,
                    "total_transport_cost":10400},
  "alternatives": [{"road_containers":100, "road_trips":70, "total_transport_cost":11200}, ...],
  "cost_vs_baseline": {"baseline_all_road_cost":12000, "optimised":10400, "savings":1600},
  "guardrails_checked": {"weight_bounds_valid": {"passed": True}, ...}
}
# Monitor re-compute: berth_conflict → 100 road / 20 sea = 70×150 + 20×35 = 11,200
```
**Why:** Hard number judges can audit: 60×$150 + 40×$35 = $10,400 is the flagship invariant.

### SNIPPET E — 7 escalation triggers (exact thresholds) — *Slide 7 Guardrails*
```python
# app/agent/escalation.py:149 TRIGGERS (check after every tool batch → HITL-5)
TRIGGERS = {
  "low_confidence": lambda s: s["confidence"] < 0.85,
  "feeder_hold_exceeded": lambda s: s["context"].get("feeder_hold_hours",0) > 1.5,
  "cost_exceeded": lambda s: s["context"].get("action_cost", s["context"].get("split_result",{}).get("total_transport_cost")) > 10000,
  "data_stale": lambda s: tool_output["data_age_minutes"] > 30,
  "road_capacity_low": lambda s: available/required < 0.6,
  "feeder_unresponsive": lambda s: elapsed > 15,  # minutes
  "planner_conflict": check_planner_conflict,      # mutually exclusive HITL decisions on same gate
}
```
**Why:** Every threshold is charter-verbatim; trivial to test (`pytest app/tests/test_escalation.py` style).

### SNIPPET F — YAML config: one problem, one file — *Slide 8 Scalability (side-by-side)*
```yaml
# app/configs/pb-12-itt.yaml:1
problem: {id: PB-12, name: Multi-Party ITT Coordination Failure, sector: Multimodal Logistics}
llm: {provider: anthropic, model: claude-sonnet-4-20250514, fallback_provider: openai}
systems: [citos_ppt, citos_tuas, optetruck, feeder, portnet]
tools: [get_itt_candidates, check_road_itt_capacity, check_sea_itt_capacity, compute_itt_split, update_tuas_loading_sequence, dispatch_road_itt, request_feeder_hold, notify_parties]
hitl_gates: [hitl_1: 30m/escalate, hitl_2: 15m/cancel_dispatch, hitl_3: 15m/escalate, hitl_4: 10m/hold_sequence, hitl_5: 30m/halt]
cost_params: {road_cost_per_trip:150, demurrage:2500, feeder_charter:800, handling:35, ...}
# Sibling: app/configs/pb-01-berth.yaml — same shape, different systems/tools (vtis, optevoyage, citos berth)
```
**Why:** Visual “swap one YAML, get a new problem” claim.

### SNIPPET G — AgentState (what the agent remembers per run) — *Slide 6 Orchestration (small footer)*
```python
# app/agent/state.py:10 AgentState (TypedDict total=False)
class AgentState(TypedDict, total=False):
    messages: list[dict]          # LLM conversation
    tool_results: dict            # {tool_call_id: ToolResult}
    hitl_pending: dict|None       # current gate (interrupt)
    hitl_history: list[dict]      # past decisions
    confidence: float             # 0.0–1.0 (0.85 threshold)
    escalation: dict|None
    trace: list[dict]             # every node/tool/HITL/deviation
    deviation_log: list[dict]     # why original plan failed
    run_id: str                   # also thread_id
    problem_config: dict
    context: dict                 # candidates, road/sea capacity, split_result, dispatched, etc.
```
**Why:** Explains state checkpointing judges will quiz on.

### SNIPPET H — SSE streaming (race-free replay buffer) — *Slide 6 Observability*
```python
# app/agent/sse.py + app/main.py
@broadcaster.publish(run_id,"agent_thinking",{"step": "..."} )  # every node publishes
@broadcaster.publish(run_id,"tool_result",{"tool": name, "risk_score": risk, "fallback_used": flag})
# GET /agent/stream/{run_id} — buffers before SSE connect, replays on connect, 8 events: thinking/tool_call/tool_result/hitl_card/escalation/trace_entry/confidence_update/deviation (+ heartbeat)
# GET /agent/stream/{run_id} supports Last-Event-ID replay
```
**Why:** Answers the “how does the UI not miss events” question.

### SNIPPET I — Webhook validation (entry guard) — *Slide 6 Pipeline (tiny inset)*
```python
# app/shared/models.py: ITTCoordinationEvent + app/main.py: POST /webhook/itt-coordination
class ITTCoordinationEvent(BaseModel):
    container_count: int  # ≥ 50
    tuas_vessel_departure: str  # > now + 2h
    weight_kg: conint(gt=0, le=60000)
    blocks_affected: list[str]  # ≤ 4500 TEU guard
    # 422 on invalid → stay idle + heartbeat 30s otherwise
```
**Why:** Shows guardrail-at-the-door, not just in the optimiser.

---

## 15) Suggested 10-Slide Deck Structure (CodeSprint §6.2 — mandatory)

> Map each slide to the evaluation pillar. Allocate ~45 s talk per slide (7.5 min) + 2.5 min live demo overlay or mock walkthrough. Keep Placeholders where Phase 7 UI not ready.

**Slide 1 — Title / Competition Frame** *(no pillar, first impression)*
- Title: **PSA Nexus — Agentic Multi-Party Coordination Platform**
- Subtitle: *One brain, seven problems.* Flagship: PB-12 cross-terminal ITT (PPT → Tuas)
- Footer: Team name [TO FILL], Submission 2026-09-04, Tech: LangGraph + FastAPI + YAML
- Visual: Nexus hub diagram (center = Agent core, spokes = 5 systems + 7 problem YAMLs + dashboard)
- Code: none

**Slide 2 — The Problem & Cluster** *(Rubric: Innovation & Originality — problem selection)*
- 16 problems mined → 12 passed 5-filter litmus test → C2 cluster (7 problems, score 4.80) wins
- Table: mini bank (7 C2 rows with cost + system count) — highlight PB-12 flagship
- Litmus diagram: 5 diamonds (L1–L5) all green for PB-12
- Footnote: “Sources: `problems/02-03-problem-bank.md`, `problem-selection/03-01-litmus-test-scores.md`”

**Slide 3 — The Disruption Gap (Why Rule Engines Fail)** *(Innovation)*
- Left: as-is spaghetti (12 phone calls, CITOS PPT vs Tuas not integrated, PORTNET lag)
- Right: table Rule Engine vs Agent (stale data, dynamic re-plan, guardrails, calibrated HITL, YAML reuse) — copy from `README.md:§3 Why This Needs an Agent`
- Visual: phone-call timeline vs agent timeline contrast

**Slide 4 — Autonomy Level & Risk Framework** *(Scalability & Responsible AI)*
- Tier 2 — HITL Exception Solver (quote the Autonomy Trap warning)
- Risk matrix: financial ($10K+), authority boundaries, data asymmetry → Tier 2 justified
- 5 gates table (compat, timeout, timeout_action) — see §10; escalation 7 triggers mini-tiles
- Note: “Planned auto-timeout scheduler (Phase 6.5) — per-gate escalate/cancel/hold/halt + 30-min halt rule”

**Slide 5 — System Architecture** *(Agentic Design & Technical Execution)*
- Diagram: FastAPI (8000) → webhook + SSE + HITL + switch-problem → LangGraph (4 nodes + MemorySaver) → ToolRegistry → Mocks
- Badges: 8 providers, 7 YAMLs, in-process tool calls
- Code: **Snippet A** (graph wiring)
- Footer: “No DB — in-memory + YAML sufficient for demo scope”

**Slide 6 — Execution Trace & Multi-Tool Orchestration** *(Agentic Design)*
- 17-step swimlane (T1→T2/T3 parallel → T4 → HITL-1 → dispatch/HITL-2/HITL-3 → Tuas/HITL-4 → monitor re-query T3 → deviation → re-compute → HITL-5 → delta)
- Two paths: happy `deviation_log==[]` vs deviation `0.78 confidence → 100/20 re-split + $11,200`
- Trace: “Every step = TraceEntry(timestamp, node, action, result, risk_score, confidence, duration_ms, fallback_used) → structured JSON + LangSmith”
- Code: **Snippet D** (T4 output) + **Snippet G** (AgentState) tiny, **Snippet H** (SSE events)
- Visual note: “SSE replay buffer — `Last-Event-ID` safe, 8 event types”

**Slide 7 — Safety, Guardrails & Fallback Handling** *(Scalability & Responsible AI)*
- 6 guardrails table + validation points (webhook / before T4 / post-approval)
- 5 HITL gates: approve / reject→alternatives / modify→re-validate + re-run T4 / timeout→per-gate action
- 7 escalation triggers with charter thresholds (verbatim) — **Snippet E**
- 4 robustness rows: S1–S4 with icons (pass/check, skip for S4 pending HITL-5 in Phase 6 is now green)
- Code: **Snippet B** (interrupt) + **Snippet I** (webhook guard)
- WIP badge: “Lifespan validation + HITL timeout scheduler — Phase 6.5 upcoming”

**Slide 8 — Scalability & Platform Generalisability** *(Scalability + Innovation)*
- Hero claim: “1 YAML = 1 problem — same core, no fork”
- Side-by-side: PB-12 (ITT: 5 systems, 8 tools, 5 gates, $10.4K) vs PB-01 (Berth: VTIS/OptEVoyage/CITOS, 5 tools, 2 gates, berth/tide) + switch curl:
  ```
  POST /agent/switch-problem/pb-01-berth → {tools: 5, hitl_gates: 2}
  POST /agent/switch-problem/pb-12-itt   → {tools: 8, hitl_gates: 5}
  ```
- Visual: `build_system_prompt(config)` branching + `register_for_problem(id)` flow
- Code: **Snippet C** (registry switch) + **Snippet F** (YAML)
- Cost roll-up: $1.26M–$2.08M cluster vs $384K–$576K flagship alone

**Slide 9 — Quantified Business Impact & ROI Model** *(Presentation & Clarity)*
- Charter §5 math block (mono font): `Savings = $8,450 − $450 = $8,000 / incident` broken into 5 components
- Transport footnote: baseline 80×$150=$12K → optimised $10,400 → save $1,600 + 20 fewer AYE trips
- Annual bars: flagship $384K–$576K, cluster $1.26M–$2.08M
- Latency: happy <30 s wall, deviation <90 s; SSE p50/p95 *(planned metric — Phase 8.4)*, token budget ~21.5K (~$0.09–$0.10 Claude Sonnet 4)
- Risk note: “Grounded params: Singapore LTA chassis, PSA $35/lift, $2,500/hr demurrage”

**Slide 10 — Summary & Roadmap** *(all pillars — close strong)*
- Left: “What’s built” check-list (Phases 1–6, 184 tests) vs “What’s next” (Phase 6.5 → 7 UI mock → 07.1 integrated verification gate → 8 Docker local + deck/video)
- Center: 27 min vs 4–8 h KPI delta + one-liner “Same brain works for 7 port problems”
- Right: Q&A prep — provider-swap (`provider: custom + base_url`), per-run mock isolation, deterministic mock without API key,诚实 gap inventory (23 gaps, now 63 sub-phases)
- Visual: milestone timeline with deadline 2026-09-04 gate
- Code: none — end on numbers

**Appendix (slides 11+ — not counted, but useful for Q&A):**
- A1 Full 17-step trace dump (`buildplan/03-03-master-charter.md:§7` trace example 89.9 s)
- A2 HITL approval card visual (charter §4 template — road $9K + sea $1,400 = $10,400, confidence 0.92)
- A3 Tool schemas (OpenAI function-calling format per `app/tools/*.py:parameters_schema`)
- A4 Gap Inventory honest table (23 gaps, phases mapped)
- A5 Demo script checklist (see §16)

---

## 16) Demo Script (10 minutes per CodeSprint §6.3 — for video speaker notes)

> Until Phase 7 UI exists, narrate over architecture diagram + API calls via `curl` + log tail. Replace verbs once UI lands.

- **Part 1 (0:00–2:00) — The Operational Problem & PSA Context**
  - Open with vessel `MV PACIFIC STAR` waiting Tuas 20:00, 120 ctrs stuck at PPT, CITOS PPT vs Tuas not talking, 30–60 min PORTNET lag. “Today a 60/40 guess + phone calls — often it does not line up.” Show as-is 12-step phone spaghetti.
- **Part 2 (2:00–3:30) — High-Level Solution Architecture**
  - Unveil Nexus hub: LangGraph core, 7 YAMLs, 8 providers, SSE. “Swap one YAML, get a different port problem — we’ll prove it live with PB-01.” Diagram morph: ITT tools slide out, berth tools slide in.
- **Part 3 (3:30–7:30) — Live System Walkthrough** (current: terminal + logs; planned: dashboard)
  - `curl POST /webhook/itt-coordination` with `buildplan/03-03-master-charter.md:§3.6` payload (120 ctrs). Tail `trace` + SSE stream: T1→T2/T3→T4 `80/40=$10,400`. Pause at HITL-1 card: “Approve ITT Split — $10.4K vs $12K baseline, confidence 0.92” → click Approve (or `POST /agent/hitl/respond`).
  - HITL-2 “Dispatch 16 trucks via West Coast Hwy→AYE→Tuas” → Approve; HITL-3 “Hold feeder 1h, tidal buffer…” → Approve; HITL-4 Tuas sequence → Approve.
  - *Deviation injection:* `POST /agent/inject-edge-case {case:"feeder_berth_conflict", run_id}` — narrative: “Now PORTNET says berth conflict, departure to 1600.” Monitor fires, confidence 0.78, re-compute 100/20 = $11,200, HITL-5 emergency card (“+$1,500 but avoids $5,000 miss”) → Approve → delta +4 trucks + second Tuas sequence. Show `deviation_log` + confidence trajectory.
  - *Robustness cameo* (30 s): briefly mention S2 missing weight (guardrail) + S3 503→fallback side-card.
  - *Platform proof (60 s):* `POST /agent/switch-problem/pb-01-berth` → tool list flips to VTIS/OptEVoyage → query arrival → show 2 gates live (“same brain, new verbs”).
- **Part 4 (7:30–9:00) — Safety, Guardrails & Scalability**
  - Overlay: 6 guardrails at three checkpoints, 7 triggers, 5 gates with timeout logic, per-run mock isolation, hallucination handling, 429 retry.
- **Part 5 (9:00–10:00) — Business Impact & Close**
  - Equation wipe: $8,450→$450, flagship $384K–$576K/yr, cluster $1.26M–$2.08M. “27 minutes vs 4–8 hours. Same brain works for 7 PSA problems. Local Docker today, platform tomorrow.”

---

## 17) Visual Guidance (for the slide AI / designer)

- **Palette:** PSA maritime — deep navy #0E2F5A, teal accent #1AA99F, warning amber #F5A623, danger coral #E94E4E, success green #2ECC71, background #F7F9FC. Keep text high-contrast.
- **Icons:** 📦 containers, 🚛 road, 🚢 feeder, 🏗️ CITOS/yard, 🧠 agent, ✋ HITL hand, ⚠️ escalation, 📝 trace, 📡 SSE.
- **Diagram style:** clean boxes + diamonds (decision), horizontal swimlane for 17 steps; HITL diamond = yellow, monitor = teal, deviation = red dashed loop.
- **Typography:** single sans-serif, mono for math/code, tables > bullet paragraphs.
- **Rule:** No slide exceeds 30 words per bullet, no table exceeds 8 rows. Push extras to appendix.
- **Mockup hint (Phase 7 pending):** render a Figma-style wireframe with dashed border + “⏳ Planned — Phase 7” ribbon, not a photoreal browser.

---

## 18) Evaluation Rubric — Self-Score Map (be honest with judges)

| Criterion (judge) | What judges check | Where we prove it | Status |
|---|---|---|---|
| **Agentic AI Design & Technical Execution** (ReAct, tool orchestration, state, trace) | ReAct loop, conditional edges, checkpointing, observable trace | Graph 4 nodes + `interrupt`/`thread_id`, trace `risk_score` per entry, SSE replay | ✅ Done (Phase 6 E2E 5 green) |
| **Innovation & Originality** (beyond chatbot) | Non-trivial multi-party coordination, not a lookup | Cluster C2 4.80 score, CITOS disintegration gap, optimise road/sea under tide+LTA+block constraints | ✅ Done |
| **Scalability & Responsible AI** (HITL, latency, safety, guardrails) | Risk-calibrated autonomy, guardrails, fallbacks, scalability | 5 gates + 7 triggers + 6 guardrails + 4 robustness + YAML-per-problem + local Docker (planned) | ✅ Core done; timeout scheduler + integrated verification WIP |
| **Presentation & Clarity** (architecture rigor, ROI math) | Clear architecture, quantified throughput/dwell/cost impact | 10-slide flow + charter §5 math grounded (Singapore $2,500/$800/$150/$35) + latency metrics | ✅ Math locked; UI visuals are mockups until Phase 7 |

---

## 19) Gaps & Limitations — Say This Out Loud (builds trust)

- **UI not built:** Dashboard, trace drawer, HITL cards are wireframes until Phase 7. Demo today is via API + logs; HITL timeout auto-fire is still manual (Phase 6.5.3).
- **Mocks, not real PSA systems:** CITOS/OptETruck/PORTNET are in-process fixtures in `app/mocks/data.py` — per-run isolated but synthetic. No production integration attempted.
- **LLM cost not measured at scale:** ~$0.09/incident estimate from charter trace (18K in / 3.5K out, Claude Sonnet 4). Real latency p50/p95 still to be benchmarked in Phase 8.4.
- **Sibling tools stubbed:** PB-02/04/09/10/11 have YAML parity but tools are warnings-only until Phase 5.11 family is extended to all 7. PB-01 is the only fully switchable sibling today.
- **8 providers, 4 families — tested on mocks:** Adapter (`app/shared/tool_adapter.py`) covers all, but e2e with real keys has only been exercised via charter fixture + deterministic mock provider; live key E2E is Phase 4.3/6.11 regression.

---

## 20) Team & Logistical Placeholders (fill before deck build)

```
Team name:        [TO FILL]
Members:          [TO FILL — persona: ITT Controller / Terminal Duty Manager validator if any]
Repo URL:         [TO FILL]
Video length:     10:00 (per §6.3 — 0:00-2:00 problem, 2:00-3:30 arch, 3:30-7:30 live, 7:30-9:00 guardrails, 9:00-10:00 ROI + sibling switch)
Deck file:        submission/deck.pdf (Phase 8.5 — will generate from this context)
Video file:       submission/demo.mp4 (Phase 8.6)
Contact / demo fallback: localhost:8000/ui/ + curl samples in app/tests/test_agent_e2e.py
```

---

## 21) Sources (so the slide AI can cite — don’t fabricate)

- `CodeSprint.md` — competition brief (§3 phase workflows, §6.2 10-slide rubric, §6.3 10-min video rubric)
- `buildplan/03-03-master-charter.md` — flagship charter (11-field webhook T6, 8 tool specs §3, 5 HITL gates §4, 7 triggers §4, cost equation §5, demo trace §7, gap inventory §8 — 23 gaps)
- `README.md:§2–§5` — flagship + cluster + cost grounding + 5-point litmus result
- `.planning/ROADMAP.md` — 63 sub-phases, critical path 4→5→6→6.5→7→07.1→8, Phase 8.3 DISABLED local-only
- `.planning/PROJECT.md` — product rebrand to PSA Nexus, constraints (no DB, 8 providers)
- `.planning/STATE.md` — current position Phase 6 ✅, 127 tests pass, 5 E2E green
- `research/`, `problems/02-03-problem-bank.md`, `problem-selection/03-01-litmus-test-scores.md`, `problem-selection/03-02-autonomy-level.md` — sector maps + 16 problems + selection
- Runtime truth: `app/main.py`, `app/agent/graph.py:64`, `app/agent/nodes.py:15`, `app/agent/state.py:10`, `app/agent/monitor.py`, `app/agent/escalation.py:149`, `app/agent/confidence.py`, `app/hitl/models.py:54`, `app/hitl/gates.py`, `app/tools/optimiser.py:83`, `app/configs/pb-12-itt.yaml`, `app/tools/registry.py`, `app/mocks/data.py`

---

## 22) Appendix Hook — Leave Room

> After the 10 mandatory slides, the deck AI may add up to 5 appendix slides. Reserve them for:
> - A1 Full trace waterfall (happy + deviation, 89.9 s charter example)
> - A2 HITL card render (charter §4 template)
> - A3 JSON tool schemas (one example per tool family)
> - A4 Detailed gap closure plan (Phases 6.5 / 07.1 checklist)
> - A5 Curl cookbook — `POST /webhook`, `POST /hitl/respond`, `POST /inject-edge-case`, `POST /switch-problem`

---

*Generated for PSA Nexus. Keep this file as the single source for the presentation AI — if deck and context disagree, fix the deck.*
