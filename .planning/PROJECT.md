# PSA Nexus — Agentic Multi-Party Coordination Platform

## What This Is

Build and competition workspace for the **PSA Code Sprint: Agentic AI in Action** competition. Covers the full pipeline: (1) mapping PSA Singapore's operations, (2) mining disruptions and selecting the flagship problem, (3) building **PSA Nexus** — a generalizable, provider-agnostic agentic platform for multi-party coordination (Cluster C2, 7 problems) using LangGraph — demonstrated via PB-12 cross-terminal ITT, and (4) preparing submission assets.

> **Product name:** **PSA Nexus** — Agentic Multi-Party Coordination Platform
> **Flagship demo:** PB-12 (Multi-Party ITT Coordination Failure — PPT↔Tuas)
> **Platform scope:** Cluster C2 (7 sibling problems, one core — swap YAML + tools per problem)

## Core Value

Build **PSA Nexus** — a working, provider-agnostic agentic platform that handles multi-party coordination failures across 7 PSA problems with HITL gates, real-time escalation, and demonstrable cost savings. Flagship demo: PB-12 (Multi-Party ITT Coordination Failure) — coordinating PPT↔Tuas container transfers across 5 PSA systems ($8,000/incident saved). Prove generalisability by running a second sibling problem (e.g. PB-01 Berth Delay) on the same core.

## Current State (2026-08-27)

**Everything is broken.** Phases 1–3 (research) are solid. Phases 4+ are a pile of disconnected code fragments:

- `provider.py` (735 lines, 8 providers) — dead code, never imported
- `orchestrator.py` — linear async pipeline, no LLM, no LangGraph
- `compute_itt_split.py` — works standalone, not integrated
- `in_approval/` and `post_approval/` — empty directories
- No web UI, no SSE, no HITL gates, no Docker
- Duplicate mock implementations (two webhook handlers, two sets of Pydantic schemas)
- YAML configs exist (7 files for C2) but only PB-12 is complete — siblings lack triggers/confidence/edge cases, none loaded by runtime
- No sibling tool implementations (VTIS, OptEVoyage, ROCC, etc.)
- No notification primitive (charter primitive #5)
- `tests/test_orchestrator.py` — broken (imports nonexistent function)

**This requires a ground-up rebuild of the entire prototype.**

## Requirements

### Validated

(None yet — ship to validate)

### Active

#### Research (Phases 1–3) — COMPLETE
- [x] Map all 4 operational sectors
- [x] Map all 7 baseline digital systems
- [x] Map Physical, Information, and Decision flows
- [x] Identify 16 candidate problems (Problem Bank)
- [x] Apply 5-Point Agentic AI Litmus Test
- [x] Select and charter PB-12 with persona, autonomy level, impact equation
- [x] Define Cluster C2 platform generalisation (7 siblings, 6 shared primitives)

#### Build (Phases 4–8) — GROUND-UP REBUILD

**Phase 4: Foundation Reformation + Platform Generalisation**
- [ ] Unified FastAPI app (`app/main.py`) serving agent + mocks + webhook + UI
- [ ] provider.py + tool adapter tested end-to-end with real API key
- [ ] YAML config system validated — loads ALL 7 C2 problem configs correctly (PB-12 complete, siblings completed)
- [ ] Sibling YAML configs completed (triggers, confidence, constraints, cost params, edge cases)
- [ ] Problem switching: `POST /agent/switch-problem/{id}` — same core, different config
- [ ] Duplicate files consolidated (two webhooks → one, two schema sets → one)
- [ ] Directory restructured: `agent/`, `tools/`, `mocks/`, `hitl/`, `ui/`, `shared/`, `configs/`

**Phase 5: Tool Integration + Notification + Robustness**
- [ ] 5 PB-12 tools + 2 post-approval tools with consistent `ToolResult` interface
- [ ] Tool 5 (Tuas loading sequence) implemented as Python function
- [ ] Post-approval tools (dispatch_road_itt, request_feeder_hold) implemented
- [ ] Notification tool: `notify_parties()` — multi-party alert (charter primitive #5)
- [ ] Sibling tool stubs: at least PB-01 tools (VTIS, OptEVoyage, CITOS berth) stubbed with mock data
- [ ] 4 robustness scenarios verified: nominal, incomplete data, API failure (503), safety escalation
- [ ] All tools wired into tool registry with JSON schemas + input validation guardrails
- [ ] Each tool tested against mock server

**Phase 6: Agent Core (LangGraph)**
- [ ] LangGraph StateGraph with state schema (messages, tools, HITL, trace)
- [ ] Agent node: LLM reasons, selects tools, processes results (prompt templated from ProblemConfig — not hardcoded to PB-12)
- [ ] 5 HITL gates as interrupt nodes with approve/reject/modify + per-gate timeout/timeout_action
- [ ] 7 escalation triggers with charter thresholds (0.85, 1.5h, $10k, 30m, 60%, 15m, planner conflict)
- [ ] Confidence scoring via LLM self-assessment (structured JSON output)
- [ ] Execution trace + deviation log + structured logging + LangSmith integration
- [ ] Monitoring / re-computation loop: re-query T3 → detect berth conflict → re-compute → HITL-5 → delta dispatch
- [ ] Webhook → agent → tools → HITL → result end-to-end (happy + deviation paths, 17 steps)
- [ ] Latency & cost/ROI equation verified (wall time, $8K/incident math)

**Phase 7: Web UI & Integration**
- [ ] SSE endpoint streaming agent thoughts, tool calls, HITL cards (replay buffer for race condition)
- [ ] HTML/CSS/JS frontend: "PSA Nexus" branding, professional design
- [ ] Problem switcher dropdown (PB-12 ↔ PB-01, etc.)
- [ ] HITL approval cards with approve/reject/modify buttons
- [ ] Edge case injection controls (feeder berth conflict, stale data) — mutates mock data layer
- [ ] Demo scenario runner (2 problems) + trace/deviation display

**Phase 8: Polish & Deploy**
- [ ] Dockerfile + docker-compose.yml (pinned versions)
- [ ] Deployed to Railway/Render free tier
- [ ] End-to-end test: webhook → agent → approval → dispatch → monitoring (both problems)
- [ ] 10-slide deck: includes generalisability visual (1 YAML = 1 problem, PB-12 vs PB-01)
- [ ] 10-minute demo video: shows PB-12 full flow + sibling problem switch + edge cases
- [ ] All submission assets uploaded before 2026-09-04

### Out of Scope

- **Production deployment** — demo only, no PSA production systems
- **Real LLM costs at scale** — estimated ~$0.09/incident (Claude Sonnet 4)

## Context

- **Competition:** PSA Code Sprint: Agentic AI in Action
- **Product:** PSA Nexus — Agentic Multi-Party Coordination Platform (Cluster C2)
- **Domain:** PSA Singapore port and supply chain operations
- **Deadline:** 4 September 2026 (hard submission gate)
- **Flagship demo:** PB-12 (Multi-Party ITT Coordination Failure) — 5 PSA systems, Tier 2 HITL
- **Platform scope:** 7 problems (PB-01, PB-02, PB-04, PB-09, PB-10, PB-11, PB-12) — one LangGraph core, YAML + tools per problem
- **4 Operational Sectors:** Berth & Marine; Container Yard & Internal Transport; Gate & External Haulage; Multimodal Logistics & Supply Chain Adjacencies
- **7 Baseline Systems:** CITOS, PORTNET, OptETruck, SmartBooking & iBOX, OptEModal, CALISTA & CALISTA P!NG, PSA BDP Enterprise Solutions
- **6 Shared Primitives:** Event Ingestion, Reasoning Planner, Multi-Tool Orchestrator, HITL Gate, Multi-Party Notification, Deviation Logger
- **6 Mandatory Agent Capabilities:** Event Ingestion & Perception; Reasoning & Dynamic Planning; Tool & System Orchestration; State Tracking & Observable Execution Trace; Human-in-the-Loop Controls; Uncertainty & Error Recovery
- **4 Evaluation Pillars:** Agentic AI Design & Technical Execution; Innovation & Originality; Scalability & Responsible AI; Presentation & Clarity
- **4 Robustness Scenarios:** Nominal Path, Incomplete Data, Tool/API Failure (503), Safety Escalation
- **Tech Stack:** LangGraph v1.2.11, Python 3.11+, FastAPI, in-memory state, YAML configs, no database

## Constraints

- **Schedule:** Submission deadline 2026-09-04 (8 days from 2026-08-27)
- **Autonomy Trap:** Higher autonomy is not automatically better; autonomy level must be use-case and risk calibrated
- **Evaluation Gates:** The four competition evaluation criteria act as acceptance gates
- **Non-Trivial Requirement:** Selected problem must pass Innovation & Originality criterion
- **No Database:** In-memory state + YAML configs sufficient for demo scope
- **Provider Agnostic:** Must work with Claude, GPT-4o, Gemini, DeepSeek, Ollama, or any OpenAI-compatible API

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Product name: PSA Nexus | Generalizable platform, not single-problem agent. Nexus = connection hub for multi-party coordination | ✅ Decided |
| Autonomy level: HITL Exception Solver | HIGH financial risk ($15K–$29K/incident) + multi-party authority boundaries + cross-terminal data asymmetry | ✅ Confirmed |
| Flagship problem: PB-12 ITT Coordination | 5 PSA systems, systemic CITOS disintegration gap, highest cluster leverage (7 sibling problems) | ✅ Locked |
| Platform generalisation: YAML per problem | Same LangGraph core, different systems/tools/costs/constraints per config. Prove with 2 E2E problem switches. | ✅ Decided |
| Winning cluster: C2 Manual Multi-Party | Score 4.80/5.00 — highest agentic sweet spot, broadest coverage, most compelling demo | ✅ Selected |
| Tech: LangGraph v1.2.11 | Provider-agnostic, HITL first-class, state checkpointing | ✅ Decided |
| No database | In-memory state + YAML configs sufficient for demo scope | ✅ Decided |
| Web app UI (not Streamlit) | HTML/JS + SSE from FastAPI for real-time agent streaming | ✅ Decided |
| HITL pattern: single hitl_node | `interrupt()` + `Command(resume=)` + `MemorySaver(thread_id)` — not 5 separate nodes | ✅ Decided |
| Ground-up rebuild | Existing prototype is fragmented dead code; rewriting is faster than fixing | ✅ Decided |

---

*Last updated: 2026-08-27 — PSA Nexus rebrand + platform generalisation*
