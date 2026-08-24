# Phase 4: Mock API Server - Context

**Gathered:** 2026-08-24
**Status:** Ready for planning
**Source:** Master Problem Charter (03-03-master-charter.md) + Tech Stack (tech-stack.md)

<domain>
## Phase Boundary

Build the mock API server that simulates 5 PSA systems (CITOS PPT, CITOS Tuas, OptETruck, Feeder, PORTNET) with realistic data, plus a webhook endpoint to receive ITT_COORDINATION_REQUEST events. This is the foundation for the LangGraph agent demo — all agent tools will call these mock APIs.

</domain>

<decisions>
## Implementation Decisions

### D-01: FastAPI + uvicorn backend
- Single port 8000 serves mock APIs, webhook, and agent
- Per tech-stack.md: "FastAPI + uvicorn | Serves agent + mock APIs + webhook on one port"

### D-02: In-memory state, no database
- Mock data stored in Python dicts/JSON, loaded at startup
- Per tech-stack.md: "No database for the demo — in-memory state + YAML configs + log files"

### D-03: 5 mock system endpoints matching Master Charter Tool specs
Each mock API implements the exact request/response schemas from Master Charter Section 3:
1. `get_itt_candidates` → CITOS PPT mock
2. `check_road_itt_capacity` → OptETruck mock
3. `check_sea_itt_capacity` → PORTNET/Feeder mock
4. `compute_itt_split` → Internal computation (no external system)
5. `update_tuas_loading_sequence` → CITOS Tuas mock

### D-04: Webhook endpoint (Tool 6 / T6)
- `POST /webhook/itt-coordination` receives ITT_COORDINATION_REQUEST events
- Pydantic model `ITTCoordinationEvent` validates payload
- Returns `{"status": "accepted", "run_id": "..."}` 

### D-05: YAML config per problem
- configs/ directory already has pb-12-itt.yaml and 6 other problem configs
- Mock data parameters derived from config (cost_params, constraints)

### D-06: Realistic Singapore cost parameters
Per Master Charter Section 5:
- Road ITT: $150/trip
- Vessel demurrage: $2,500/hr
- Feeder charter: $800/hr
- Sea terminal handling: $35/lift-move
- Yard rehandle: $35/move

### D-07: Demo edge cases built into mock responses
- Feeder berth conflict (inject at step 8)
- Data staleness detection (25-min-old data)
- Configurable via edge_cases in YAML config

### D-08: Provider-agnostic LLM abstraction (separate concern)
- LLM provider layer is NOT part of this phase
- This phase focuses only on mock APIs + webhook
- Agent core and LLM abstraction are Phase 5+

### the agent's Discretion
- Exact Python file structure within prototype/mocks/
- Whether to use FastAPI sub-routers or single file
- Mock data seeding strategy (hardcoded vs JSON files)
- Error handling depth (basic validation vs full edge case simulation)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Master Charter — Mock API Tool Specs
- `buildplan/03-03-master-charter.md` Section 3 (lines 71-388) — Full tool signatures, sample outputs, Pydantic models

### Tech Stack — Architecture Decisions  
- `buildplan/tech-stack.md` Section 6-7 (lines 246-355) — Recommended stack, project structure

### Config Files
- `prototype/configs/pb-12-itt.yaml` — Flagship problem config (systems, tools, costs, constraints)
- `prototype/configs/pb-*.yaml` — 6 other problem configs for generalization

</canonical_refs>

<specifics>
## Specific Ideas

- Mock APIs should return data that matches the exact JSON schemas in Master Charter Section 3
- The `compute_itt_split` tool is an internal computation, not a mock API — it takes other tool outputs as input
- Webhook endpoint must accept the exact trigger event payload from Master Charter Section 7
- Demo script requires realistic response times (not instant) to feel authentic

</specifics>

<deferred>
## Deferred Ideas

- LangGraph agent core (Phase 5)
- LLM provider abstraction (Phase 5)
- HITL gate UI (Phase 5)
- Web UI / SSE streaming (Phase 6)
- Docker deployment (Phase 6)
- LangSmith tracing integration (Phase 5)

</deferred>

---

*Phase: 04-mock-api-server*
*Context gathered: 2026-08-24 from build_plan specs*
