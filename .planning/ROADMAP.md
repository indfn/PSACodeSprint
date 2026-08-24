# Roadmap: PSA Code Sprint

## Overview

Four-phase pipeline for the PSA Code Sprint: Agentic AI in Action competition. Phases 1–3 map PSA Singapore's operations, mine disruptions, and select the flagship problem. Phase 4 builds the mock API server that simulates 5 PSA systems for the agent demo.

## Phases

- [x] **Phase 1: Broad PSA Singapore Operations & Systems Mapping** - Map sectors, systems, and flows ✅
- [x] **Phase 2: Disruption Mining & Problem Bank Creation** - Identify frictions, build 10–15 problem bank ✅
- [x] **Phase 3: Problem Evaluation & Final Selection** - Litmus test, select, charter one problem ✅
- [ ] **Phase 4: Mock API Server** - Build FastAPI server simulating 5 PSA systems + webhook endpoint

## Phase Details

### Phase 1: Broad PSA Singapore Operations & Systems Mapping
**Goal**: Build a clear technical understanding of PSA Singapore's operations and existing digital infrastructure across all core sectors.
**Depends on**: Nothing (first phase)
**Requirements**: [P1-01, P1-02, P1-03]
**Success Criteria** (what must be TRUE):
  1. All 4 operational sectors documented with sector-specific topic depth
  2. All 7 baseline digital systems mapped with capabilities and integrations
  3. Physical, Information, and Decision flows documented for each sector
  4. A unified operations landscape exists as the foundation for disruption mining
**Status**: ✅ COMPLETE (2026-08-17)

Plans:
- [x] 01-01: Research the 4 operational sectors ✅ (`research/sectors/`)
- [x] 01-02: Map the 7 baseline digital systems ✅ (`research/systems/baseline-systems.md`)
- [x] 01-03: Document the 3 critical flows per sector ✅ (`research/flows/critical-flows.md`)

### Phase 2: Disruption Mining & Problem Bank Creation
**Goal**: Identify high-friction operational failure points where current software and manual processes struggle, and consolidate into a 10–15 problem bank spanning all 4 sectors.
**Depends on**: Phase 1
**Requirements**: [P2-01, P2-02, P2-03]
**Success Criteria** (what must be TRUE):
  1. "Something changed" disruption scenarios identified across all sectors
  2. Each disruption has Trigger Event, Current Workaround, and Business Consequence documented
  3. A clean list of 10–15 candidate problems spanning all 4 sectors exists
  4. Problems span different sectors (not clustered in one area)
**Status**: ✅ COMPLETE (2026-08-17)

Plans:
- [x] 02-01: Target "something changed" disruption scenarios ✅ (`problems/02-01-disruption-scenarios.md`)
- [x] 02-02: Document operational failure modes for each disruption ✅ (`problems/02-02-failure-modes.md`)
- [x] 02-03: Consolidate into the Problem Bank (10–15 problems) ✅ (`problems/02-03-problem-bank.md`)

### Phase 3: Problem Evaluation, Litmus Testing & Final Selection
**Goal**: Select the single best problem for an Agentic AI solution and quantify its impact via the 5-Point Litmus Test and Master Problem Charter.
**Depends on**: Phase 2
**Requirements**: [P3-01, P3-02, P3-03, COMP-01, COMP-02]
**Success Criteria** (what must be TRUE):
  1. Every candidate problem scored against all 5 litmus-test criteria
  2. Target autonomy level defined and justified against operational risk
  3. Single Master Problem Charter locked with persona, autonomy level, and business impact equation
  4. Selected problem passes Innovation & Originality and Scalability & Responsible AI evaluation gates
**Status**: ✅ COMPLETE (2026-08-19)

Plans:
- [x] 03-01: Apply 5-Point Agentic AI Litmus Test to each problem ✅ (`problem-selection/03-01-litmus-test-scores.md`)
- [x] 03-02: Define target autonomy level ✅ (`problem-selection/03-02-autonomy-level.md`)
- [x] 03-03: Lock ONE Master Problem Charter ✅ (`buildplan/03-03-master-charter.md`)

### Phase 4: Mock API Server
**Goal**: Build a FastAPI server that simulates 5 PSA systems (CITOS PPT, CITOS Tuas, OptETruck, Feeder, PORTNET) with realistic data and a webhook endpoint for ITT_COORDINATION_REQUEST events — the foundation for the LangGraph agent demo.
**Depends on**: Phase 3
**Requirements**: [COMP-02]
**Success Criteria** (what must be TRUE):
  1. All 5 mock system endpoints return data matching Master Charter Tool specs
  2. Webhook endpoint accepts ITT_COORDINATION_REQUEST and returns accepted status
  3. Mock data uses realistic Singapore cost parameters from Master Charter
  4. Server runs on single port (8000) with `uvicorn prototype.main:app`
  5. Edge case scenarios (feeder berth conflict, data staleness) configurable via YAML
**Status**: ○ PLANNED

Plans:
- [ ] 04-01: FastAPI scaffold + Pydantic schemas + project setup
- [ ] 04-02: 5 mock system API endpoints with realistic data
- [ ] 04-03: Webhook endpoint + edge case simulation + integration test

## Progress

**Execution Order:**
Phases execute in order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Broad PSA Singapore Operations & Systems Mapping | 3/3 | ✅ Complete | 2026-08-17 |
| 2. Disruption Mining & Problem Bank Creation | 3/3 | ✅ Complete | 2026-08-17 |
| 3. Problem Evaluation & Final Selection | 3/3 | ✅ Complete | 2026-08-19 |
| 4. Mock API Server | 0/3 | ○ Planned | — |
