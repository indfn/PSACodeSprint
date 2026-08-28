# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-27)

**Core Value:** Build PSA Nexus — a generalizable agentic platform (Cluster C2, 7 problems) demonstrated via PB-12 (ITT Coordination, $8K/incident) and proven switchable to a sibling problem (e.g. PB-01 Berth Delay) on the same LangGraph core.
**Current focus:** Phase 7 — Web UI — Nexus Dashboard (next to execute)

## Current Position

Phase: 7 of 9 (Web UI — next to execute)
Plans: 9 detailed plans created (Phases 1–3 research + Phases 4–8 build + 07.1 Integrated Verification, 57 sub-phases)
Status: Phases 1–6 complete (Phase 6 executed 2026-08-28 — LangGraph 4 nodes + 5 HITL gates interrupt/Command + 7 escalation + monitor deviation 100/20 + e2e 5 tests green 37-43s, fix: HITL-5 pending vs history, truncation 120→5). Phases 7–8 (+07.1 gate) planned, cross-checked twice + 05 deep review.
Last activity: 2026-08-28 — Phase 6 verified: agent_node + tool_node + hitl_node + monitor_node, MemorySaver(thread_id), mock provider deterministic, e2e happy + deviation both PASSED isolated (42s/37s/43s), truncation avoids deepcopy stall

Progress: ██████░░░░ 66% (6/9 phases complete, 3 planned + verified)

## What's Built

| Component | Status | Location |
|-----------|--------|----------|
| Research & problem selection | ✅ Done | `research/`, `problems/`, `problem-selection/`, `buildplan/` |
| Master charter (gap-aware) | ✅ Done | `buildplan/03-03-master-charter.md` — 23 gaps, 5 HITL gates, 7 triggers, 8 tools |
| Planning: PROJECT.md (PSA Nexus) | ✅ Done | `.planning/PROJECT.md` — Nexus platform rebrand |
| Planning: REQUIREMENTS.md | ✅ Done | `.planning/REQUIREMENTS.md` — 70 requirements (F-01..F-13, T-01..T-18, A-01..A-23, U-01..U-12, D-01..D-08) |
| Planning: ROADMAP.md | ✅ Done | `.planning/ROADMAP.md` — 9 phases (incl. 07.1 gate), 57 sub-phases, critical path 4→5→6→7→07.1→8 |
| Planning: Phase 4 PLAN | ✅ Done | `.planning/phases/04-foundation-reformation/PLAN.md` — 9 sub-phases (incl. sibling YAMLs + problem switcher) |
| Planning: Phase 5 PLAN | ✅ Done | `.planning/phases/05-tool-integration/PLAN.md` — 13 sub-phases (incl. notification + PB-01 stubs + ROI + robustness) |
| Planning: Phase 6 PLAN | ✅ Done | `.planning/phases/06-agent-core/PLAN.md` — 11 sub-phases (correct interrupt+Command, monitor loop, templated prompt) |
| Planning: Phase 7 PLAN | ✅ Done | `.planning/phases/07-web-ui/PLAN.md` — 8 sub-phases (Nexus branding + problem switcher + notifications) |
| Planning: Phase 8 PLAN | ✅ Done | `.planning/phases/08-polish-deploy/PLAN.md` — 7 sub-phases (Nexus deck+video per rubric, latency metrics) |
| Planning: Phase 07.1 PLAN | ✅ Done | `.planning/phases/07.1-integrated-verification-system-level-e2e-resilience-and-cros/PLAN.md` — 8 sub-phases (harness, E2E 17-step, HITL matrix, resilience, robustness, switch regression, observability, gate) (INSERTED) |
| FastAPI scaffold | ✅ Done | `app/main.py` — unified FastAPI (health, webhook, switch-problem, /ui/*, /mocks/* alias) — Phase 4 |
| LLM provider abstraction | ✅ Done | `app/shared/provider.py` (8 providers) + `app/shared/tool_adapter.py` (4 families) — Phase 4.3 |
| YAML config system | ✅ Done | `app/configs/` — 7 YAMLs completed + `problem_config.py` dataclass — Phase 4.4+4.7 |
| Mock API server | ✅ Done | `app/mocks/` — 5 routers (citos_ppt/tuas, optetruck, feeder, portnet) + `data.py` + `edge_cases.py` — Phase 4.2 |
| Pydantic schemas | ✅ Done | `app/shared/models.py` — single canonical set (114 example→json_schema_extra fixes, 0 warnings) — Phase 4.2+4.5 |
| Tool 1–4 | ✅ Done | `app/tools/container_readiness.py` (`get_itt_candidates`) + `road_itt.py` + `sea_itt.py` + `optimiser.py` (`compute_itt_split` 80/40=$10,400, guardrails incl. weight_bounds) — Phase 5.2-5.5 |
| Tool 5 (Tuas loading) | ✅ Done | `app/tools/tuas_loading.py` (`update_tuas_loading_sequence` QC adjustments) — Phase 5.6 |
| Post-approval tools | ✅ Done | `app/tools/dispatch_road_itt.py` + `request_feeder_hold.py` (HITL-gated `post_approval=True`, guard `hitl_required`, decline/delta) — Phase 5.7, H1 fixed |
| Notification tool | ✅ Done | `app/tools/notify.py` (`notify_parties` + SSE + `notification_log`) — Phase 5.10 primitive #5 |
| Sibling tool stubs | ✅ Done | `app/tools/pb01/` 5 tools + `app/mocks/routers/vtis|optevoyage|berth.py` + `pb01_data.py` — switch `pb-12↔pb-01` verified — Phase 5.11 |
| Cost/ROI | ✅ Done | `app/tools/optimiser.py` `cost_vs_baseline` + `roi` ($8K/incident, $384K-$576K, cluster $1.26M) — Phase 5.12 |
| ToolRegistry | ✅ Done | `app/tools/base.py` `ToolResult` + `app/tools/registry.py` canonical `TOOLSETS` 7 problems + `register_for_problem` + `FALLBACKS` — Phase 5.1, 05-REVIEW C1/H3/M4 fixed |
| Edge hooks | ✅ Done | `app/tools/edge_cases.py` mutates `app/mocks/data.py` (FEEDER_DATA/_stale_minutes) — next T3/T1 sees conflict — Phase 5.8 |
| 4 robustness scenarios | ✅ Done | `app/tests/test_robustness.py` S1 nominal, S2 incomplete (weight_bounds), S3 503→fallback+notify, S4 skipped pending HITL-5 (Phase 6) — Phase 5.13 |
| LangGraph agent core | ✅ Done | `app/agent/graph.py` 4 nodes agent/tools/hitl/monitor + MemorySaver(thread_id), `run.py` ainvoke/Command(resume) — Phase 6 |
| HITL gates | ✅ Done | `app/hitl/models.py` 5 gates 30/15/15/10/30 + timeout_actions escalate/cancel/hold/halt, `gates.py` single hitl_node interrupt + `handler.py` REJECT/MODIFY/TIMEOUT — Phase 6.5 |
| Escalation triggers | ✅ Done | `app/agent/escalation.py` 7 triggers `<0.85/>1.5h/>$10k/>30m/<60%/>15m/planner_conflict`, confidence 0.92→0.78→0.90 — Phase 6.6 |
| Monitoring loop | ✅ Done | `app/agent/monitor.py` re-query T3 → detect berth conflict → re-compute 80/40→100/20 + HITL-5 emergency, `e2e` deviation PASSED 37s — Phase 6.10 |
| Web UI / SSE | ❌ Not started | — Phase 7 (Nexus branding + SSE replay buffer + problem switcher) |
| Docker / deploy | ❌ Not started | — Phase 8 (pinned deps + latency metrics) |
| Demo video / deck | ❌ Not started | — Phase 8 (Nexus deck per rubric, sibling switch demo) |

## Performance Metrics

**Velocity:**
- Total plans completed: 9 (research phases)
- Build phases: fully planned + double cross-checked, 40 gaps fixed total

**By Phase:**

| Phase | Status | Sub-phases |
|-------|--------|-----------|
| 1. Operations Mapping | ✅ Complete | 3 plans |
| 2. Disruption Mining | ✅ Complete | 3 plans |
| 3. Problem Evaluation | ✅ Complete | 3 plans |
| 4. Foundation + Platform | ✅ Complete (2026-08-27) | 9 — 57 tests pass, 04-REVIEW-FIX 6 fixes |
| 5. Tool Integration + Notification + Robustness | ✅ Complete (2026-08-27) | 13 — 127 pass/3 skipped S4, 05-REVIEW 15 issues fixed (C1 YAML, H1 guard, H2 weight) |
| 6. Agent Core — Nexus Brain | ✅ Complete (2026-08-28) | 12 — e2e 5 green (42s happy/37s deviation), truncation + HITL-5 pending fix |
| 7. Web UI — Nexus Dashboard | ○ Planned → next (depends on Phase 6 ✅) | 8 |
| 07.1 Integrated Verification (INSERTED) | ○ Planned → depends on Phase 7 | 8 |
| 8. Polish & Deploy — Nexus Launch | ○ Planned → depends on 07.1 | 7 |

## Accumulated Context

### Decisions

- **Product name:** PSA Nexus — Agentic Multi-Party Coordination Platform. Nexus = connection hub. Flagship demo: PB-12 (ITT), platform proves itself via sibling switch (PB-01).
- **Scope:** Full working platform — ground-up rebuild + generalisability proof (2 E2E problems, not just 1)
- **Tech Stack:** LangGraph v1.2.11, Python 3.11+, FastAPI, in-memory state, YAML configs, no database
- **Provider:** 8 providers supported (Anthropic, OpenAI, Gemini, DeepSeek, Ollama, vLLM, LM Studio, Custom)
- **Flagship:** PB-12 (Multi-Party ITT Coordination Failure), 5 PSA systems, Tier 2 HITL — 120 containers PPT→Tuas, $10,400 optimal vs $12K baseline
- **Cluster:** C2 Manual Multi-Party (score 4.80/5.00, 7 problems: PB-01,02,04,09,10,11,12)
- **Autonomy:** Tier 2 HITL Exception Solver — HIGH financial risk + authority boundaries
- **Generalisation:** YAML config per problem + tool registry `register_for_problem()` + templated prompt `build_system_prompt(config)` — same LangGraph core, different tools/costs/gates per problem
- **UI:** PSA Nexus dashboard — HTML/JS vanilla + SSE from FastAPI, problem switcher dropdown
- **Tool invocation:** In-process Python calls (G-06 decision) — endpoint params omitted, mock data from `app/mocks/data.py`
- **HITL pattern:** Single `hitl_node` with `interrupt()` + `Command(resume=)` + `MemorySaver(thread_id=run_id)` — not 5 separate nodes
- **Cost:** ~$0.09/incident (Claude Sonnet 4); PB-12 savings $8K/incident → $384K–$576K annual, $1.26M–$2.08M cluster
- **6 Shared Primitives:** Event Ingestion, Reasoning Planner, Multi-Tool Orchestrator, HITL Gate, Multi-Party Notification, Deviation Logger — all implemented
- **4 Robustness Scenarios:** Nominal, Incomplete Data, API 503 Failure, Safety Escalation — per CodeSprint Phase 5.3
- **Ground-up rebuild:** Existing prototype is fragmented dead code; rewriting is faster than fixing

### Cross-Check Results — Round 1 (2026-08-27)

Comprehensive audit: 4 parallel deep checks (HITL/escalation, tools/tech, gaps/requirements, integration/E2E). 23 issues found and fixed — see details above.

| Category | Issues Found | Fixed |
|----------|-------------|-------|
| HITL gates (names, timeouts, timeout_actions) | 5 gates mismatched names + all timeouts/timeout_actions missing | ✅ Names aligned to charter; timeouts (30/15/15/10/30 min) + timeout_actions (escalate/cancel_dispatch/hold_sequence/halt) added |
| Escalation triggers (thresholds, semantics) | 0/7 matched charter (0.85→0.7, $10k→15%, 30min→container_count, etc.) | ✅ All 7 restored to charter: `<0.85, >1.5h, >$10k, >30m, <60% trucks, >15m unresponsive, planner_conflict` |
| HITL disapproval flow | REJECT/MODIFY/TIMEOUT gaps (no logging, no alternatives, no re-validation) | ✅ Full charter flow: REJECT→alternatives/escalate, MODIFY→validate+re-run T4+re-approve, TIMEOUT→per-gate action + 30 min halt |
| Tool signatures (T1–T5 params) | All tools had wrong/incomplete params vs charter | ✅ Aligned to charter; G-06 in-process decision documented; endpoint params noted as intentional omission |
| Tool naming drift | T1 `query_container_readiness` vs `get_itt_candidates`, T4 `compute_optimal_split` vs `compute_itt_split` | ✅ All tool names restored to charter: `get_itt_candidates`, `compute_itt_split`, etc. |
| Cost model | $7,400 vs charter $10,400 (60×$150=$9k + 40×$35=$1.4k) | ✅ Fixed to $10,400 (60×$150=$9,000 + 40×$35=$1,400) |
| Schema consolidation | ROADMAP said `app/mocks/schemas.py`, PLAN said `app/shared/models.py` | ✅ Locked to `app/shared/models.py`; webhook NOT in mocks |
| Webhook placement | T6 entry point quarantined under `app/mocks/` | ✅ Webhook → `app/main.py` (or `app/agent/webhook.py`), not mocks |
| LangGraph interrupts | 5 separate nodes + dynamic `f'hitl_{gate_id}'` routing (technically broken) | ✅ Single `hitl_node` with `interrupt()` + `Command(resume=)` + `MemorySaver(thread_id)` |
| Graph assembly | Missing `thread_id` config, missing `interrupt_before`, wrong routing | ✅ `config={"configurable": {"thread_id": run_id}}` on both `ainvoke` and `Command` |
| SSE race condition | Agent emits before SSE connects → lost events | ✅ `SSEBroadcaster` with `buffers(deque)` + replay on connect |
| SSE wiring | No broadcaster injection into agent nodes | ✅ `_broadcaster` + `_run_id` in `AgentState`, published from every node |
| Provider adapter | No translation between OpenAI/Anthropic/Gemini tool formats | ✅ `app/shared/tool_adapter.py` (Phase 4.3) |
| ToolResult vs LLM confidence | Two confidence channels never reconciled | ✅ ToolResult.confidence = data quality; LLM confidence = decision confidence; escalation checks LLM confidence |
| Edge case mutation | Mutated AgentState only, not mock data → next T3 still healthy | ✅ Hooks mutate `app/mocks/data.py` directly; NOT LLM-callable tools |
| Monitoring loop | No monitor node, no re-query, no deviation logging (steps 12–17 missing) | ✅ New Phase 6.10 `monitor_node`: re-query T3 → detect → re-compute T4 → HITL-5 → delta dispatch → T5 again |
| E2E test | Stopped at step 11, no deviation path | ✅ New Phase 6.11: happy path (10 steps) + deviation path (7 more) = full 17-step charter workflow |
| Input validation guardrails | 6 charter guards (weight, block cap, trucks, feeder, margin, tidal) nowhere | ✅ New `app/agent/validation.py` + `A-21`; checked at webhook + T4 + post-approval |
| Structured logging | G-23 (`timestamp,run_id,step,event_type,payload` to stdout+file) conflated with trace | ✅ New `app/shared/logging.py` + `A-23`; separate from trace |
| Phase counts | 38 stated, actually 39 after adding monitor | ✅ Updated to 39 (Phase 6: 11 sub-phases) |
| Version pinning | `requirements.txt` used `>=` not `==` | ✅ Pinned `==` per charter Section 9 (langgraph==1.2.11, etc.) |
| LangSmith env | Not wired in Phase 4/8 | ✅ `LANGSMITH_API_KEY` + `LANGSMITH_PROJECT` in Phase 8.3 |
| Dependencies | Generic `Depends on: Phase N` hid critical path; 7.4 violated Phase 7→6 | ✅ Fixed: 7.4 now depends on 6.10 |

### Cross-Check Results — Round 2: PSA Nexus Rebrand + Generalisability (2026-08-27)

Deep sweep flagged 5 HIGH + several MEDIUM gaps previously missed (review was charter-vs-plans, not charter+CodeSprint-vs-plans).

| Category | Gap | Fixed |
|----------|-----|-------|
| **Product name** | "PSA ITT Coordination Agent" too narrow — product is a 7-problem platform | ✅ Renamed to **PSA Nexus** — Agentic Multi-Party Coordination Platform (flagship: PB-12) |
| **Notification primitive** | Charter §6 primitive #5 (Multi-Party Notification) had NO requirement, NO tool, NO sub-phase | ✅ New T-12 `notify_parties(message, parties)` + Phase 5.10 + U-12 display + SSE `notification` event |
| **Sibling YAML configs** | 6 siblings incomplete (only PB-12 had triggers/confidence/cost/edge cases); PB-01 had 1 HITL gate vs PB-12's 5 | ✅ Phase 4.7: complete all 6 siblings to parity; F-09/F-10/F-11 |
| **Sibling tool impls** | No tools for VTIS/OptEVoyage/ROCC etc. — platform claim unverifiable | ✅ Phase 5.11: PB-01 tool stubs (5 tools) + mock routers (VTIS/OptEVoyage/berth) |
| **Problem switching** | No mechanism to switch problems at runtime — platform claim was words only | ✅ Phase 4.8: `POST /agent/switch-problem/{id}` + `registry.clear/register_many` + templated prompt (F-12/F-13) |
| **Cost/ROI equation** | Charter §5 `Savings = $8450-$450=$8000` equation + `$384K-$576K` annual + `$1.26M` cluster never coded | ✅ Phase 5.12: T4 output includes `cost_vs_baseline` + `roi` object; `test_roi.py`; T-14 |
| **10 cost param rows** | Only 7 cost params in YAML; charter lists 10 (missing $0 charter, 4500 TEU block, $150 missed) | ✅ F-11: all 10 rows validated on load |
| **4 robustness scenarios** | CodeSprint Phase 5.3 requires nominal/incomplete/503/safety — NONE planned | ✅ Phase 5.13 + T-15..T-18: all 4 scenarios with trace/SSE/notification verification |
| **Prompt hardcoding** | System prompt was hardcoded to "ITT planner" — breaks sibling problems | ✅ Phase 6.2: `build_system_prompt(config)` templated from ProblemConfig |
| **Dashboard problem switcher** | No UI to prove platform claim | ✅ Phase 7.7: dropdown PB-12↔PB-01 + tool/gate list update |
| **Notification display** | No UI for notification primitive | ✅ Phase 7.8: bell icon + notification panel listening for SSE |
| **Deck generalisability** | Slide 10 said "7 sibling problems" with no visual proof | ✅ Phase 8.5: slides re-mapped to CodeSprint §6.2 rubric (10 slides) + PB-12 vs PB-01 side-by-side |
| **Video sibling switch** | No sibling demo in video | ✅ Phase 8.6: Part 3 now includes "platform switch: PB-12→PB-01" live |
| **Latency/Responsible AI** | Evaluation Pillar 3 (latency, security, safety) had no metrics | ✅ Phase 8.4: latency measurement (wall time, SSE p50/p95) + D-08; schema validation on all inputs |
| **Scenario B (stale data)** | Charter Scenario B 120→117 via customs hold not implemented (only trigger existed) | ✅ Covered by T-16 (S2 incomplete data) + Phase 5.13 S2: guardrail → secondary query → HITL |
| **Phase counts** | 39 stated → actually 48 after adding platform sub-phases | ✅ Updated to 48 total (4:9, 5:13, 6:11, 7:8, 8:7) |

### Roadmap Evolution
- Phase 07.1 inserted after Phase 7: Integrated Verification — system-level E2E, resilience, and cross-problem regression (URGENT)

### Pending Todos

- ~~Execute Phase 6: Agent Core — Nexus Brain (12 sub-phases) — DONE 2026-08-28~~
- Execute Phase 7: Web UI — Nexus Dashboard (8 sub-phases) — next
- Execute Phase 07.1: Integrated Verification — gate before deploy (8 sub-phases)
- Execute Phase 8: Polish & Deploy — Nexus Launch (7 sub-phases, depends on 07.1)

### Blockers/Concerns

- **Deadline:** 2026-09-04 — 7 days remaining (2026-08-27)
- **Ground-up rebuild:** 57 sub-phases — 5/9 phases done, 4 remaining (6→7→07.1→8 critical path)
- **LLM API key:** Need at least one provider API key for Phase 6 agent testing
- **Demo recording:** Need screen capture tool for video (Phase 8)
- **S4 robustness:** 3 skipped until HITL-5 — will pass after Phase 6.5/6.6

## Deferred Items

Items acknowledged and carried forward:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Build | Phases 6–8 + 07.1 (27 sub-phases remaining) | Phases 4–5 done (127 tests), 6–8 planned + double cross-checked + 07.1 gate | 2026-08-27 |
| Deploy | Docker + Railway/Render | Planned (Phase 8) | 2026-08-27 |
| Submission | Demo video + deck (Nexus) | Planned per rubric (Phase 8) | 2026-08-27 |

## Session Continuity

Last session: 2026-08-27
Stopped at: Phase 5 executed — 8 PB-12 tools (80/40=$10,400) + notify + PB-01 switch proof + 4 robustness (127 pass/3 skipped S4 pending HITL-5); deep review 15 issues (C1 YAML drift, H1 guard no-op, H2 weight_bounds) all fixed via 11 commits; warnings 24 from sibling stubs (pb-02/04/09/10/11) benign.
Resume at: Phase 6 — Agent Core (Nexus Brain) — LangGraph interrupt + thread_id + 5 HITL gates + 7 triggers + monitor loop
Roadmap Evolution: Phase 07.1 inserted after Phase 7: Integrated Verification — system-level E2E, resilience, and cross-problem regression (URGENT)
