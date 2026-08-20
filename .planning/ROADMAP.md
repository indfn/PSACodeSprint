# Roadmap: PSA Code Sprint

## Overview

Three-phase deep research and problem evaluation pipeline for the PSA Code Sprint: Agentic AI in Action competition. Phase 1 maps PSA Singapore's 4 operational sectors, 7 baseline digital systems, and 3 critical flows. Phase 2 mines disruptions and builds a 10–15 problem bank. Phase 3 litmus-tests every candidate, selects the single best problem, and locks a Master Problem Charter — all before the team commits to architecture or agent development.

## Phases

- [x] **Phase 1: Broad PSA Singapore Operations & Systems Mapping** - Map sectors, systems, and flows ✅
- [x] **Phase 2: Disruption Mining & Problem Bank Creation** - Identify frictions, build 10–15 problem bank ✅
- [x] **Phase 3: Problem Evaluation & Final Selection** - Litmus test, select, charter one problem ✅

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
- [x] 03-03: Lock ONE Master Problem Charter ✅ (`problem-selection/03-03-master-charter.md`)

## Progress

**Execution Order:**
Phases execute in order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Broad PSA Singapore Operations & Systems Mapping | 3/3 | ✅ Complete | 2026-08-17 |
| 2. Disruption Mining & Problem Bank Creation | 3/3 | ✅ Complete | 2026-08-17 |
| 3. Problem Evaluation & Final Selection | 3/3 | ✅ Complete | 2026-08-19 |
