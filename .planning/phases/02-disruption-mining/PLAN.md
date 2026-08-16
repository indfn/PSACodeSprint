# Phase 2: Disruption Mining & Problem Bank Creation — PLAN

**Created:** 2026-08-17
**Status:** Ready to execute
**Depends on:** Phase 1
**Requirements:** P2-01, P2-02, P2-03

## Goal

Identify high-friction operational failure points where current software and manual processes struggle, and consolidate into a 10–15 Problem Bank spanning all 4 sectors.

## Tasks

### 02-01: Target "Something Changed" Disruption Scenarios

Using Phase 1 sector research and system maps, identify dynamic disruptions where static rules fail.

**Deliverable:** `deliverables/02-01-disruption-scenarios.md` — disruption catalog by sector

**Research fields per sector (apply to all 4):**

- [ ] **Berth & Marine:** Vessel arrival delays causing cascading berth and yard conflicts
- [ ] **Berth & Marine:** DG or customs clearance holds detected late in the loading sequence
- [ ] **Berth & Marine:** Equipment breakdowns (crane failures, tug unavailability)
- [ ] **Berth & Marine:** Transhipment connection misses (feeder vessel departs before mother vessel discharge completes)
- [ ] **Container Yard:** AGV path deadlocks or battery depletion mid-transport
- [ ] **Container Yard:** Reefer power failures or temperature excursions
- [ ] **Container Yard:** Yard block saturation causing re-handles and stacking conflicts
- [ ] **Container Yard:** DG segregation violations detected post-stacking
- [ ] **Gate & External Haulage:** Haulier misses gate slot, causing queue backup
- [ ] **Gate & External Haulage:** Missing export documentation discovered at gate
- [ ] **Gate & External Haulage:** ITT imbalance between Pasir Panjang and Tuas
- [ ] **Gate & External Haulage:** Empty container return logistics breakdown
- [ ] **Multimodal:** Feeder connection missed due to sea-to-air transfer delay
- [ ] **Multimodal:** Customs clearance holds on cross-border cargo
- [ ] **Multimodal:** Manifest discrepancies discovered mid-transfer
- [ ] **Cross-sector:** Multi-party coordination failures (any disruption spanning 2+ sectors)

**Acceptance:**
- [ ] At least 3 disruption scenarios identified per sector (12+ total)
- [ ] Each scenario describes the trigger event and why current systems fail to handle it automatically

---

### 02-02: Document Operational Failure Modes

For each disruption scenario, document the failure mode in structured format.

**Deliverable:** `deliverables/02-02-failure-modes.md` — structured failure mode catalog

**For each disruption, document:**

- [ ] **Trigger Event:** What alert or state change starts the issue?
- [ ] **Current Workaround:** What manual, slow, or fragmented process (phone calls, emails, spreadsheets) is currently used to resolve it?
- [ ] **Business Consequence:** Demurrage fees, vessel idle time, extra yard crane moves (re-handles), missed delivery SLAs, or carbon waste
- [ ] **Systems Involved:** Which of the 7 baseline systems are touched during resolution?
- [ ] **Time Sensitivity:** How quickly must this be resolved before consequences escalate?

**Acceptance:**
- [ ] Every disruption from 02-01 has Trigger Event, Current Workaround, and Business Consequence documented
- [ ] Systems Involved field references the 7 baseline systems from Phase 1
- [ ] Time Sensitivity rated as Critical (< 1 hour) / High (< 4 hours) / Medium (< 24 hours) / Low (> 24 hours)

---

### 02-03: Consolidate the Problem Bank (10–15 Problems)

Select the best disruption scenarios and formalize them as candidate problems.

**Deliverable:** `deliverables/02-03-problem-bank.md` — ranked list of 10–15 candidate problems

**Research fields per problem:**

- [ ] **Problem Statement:** One clear sentence describing what goes wrong
- [ ] **Sector:** Which of the 4 sectors this belongs to
- [ ] **Systems Affected:** Which baseline systems are involved
- [ ] **Disruption Type:** Equipment failure / coordination breakdown / data gap / scheduling conflict / regulatory hold
- [ ] **Current Resolution:** How it's handled today (manual process)
- [ ] **Business Impact:** Quantified estimate where possible (hours lost, cost per incident, frequency)
- [ ] **Agentic Potential:** Why this is hard for static rules but tractable for an agentic AI

**Selection criteria for Problem Bank inclusion:**
- [ ] Spans at least one of the 4 sectors
- [ ] Involves at least 2 of the 7 baseline systems
- [ ] Has a quantifiable business impact
- [ ] Cannot be solved by a simple rule or database query
- [ ] Involves uncertainty, multi-step reasoning, or multi-party coordination

**Acceptance:**
- [ ] 10–15 problems in the bank
- [ ] Problems span all 4 sectors (not clustered in one)
- [ ] Each problem has all 7 fields above completed
- [ ] At least 5 problems involve cross-system or cross-sector coordination

---

## Deliverables Summary

| Task | Deliverable | Output |
|------|-------------|--------|
| 02-01 | `deliverables/02-01-disruption-scenarios.md` | 12+ disruption scenarios by sector |
| 02-02 | `deliverables/02-02-failure-modes.md` | Structured failure mode catalog |
| 02-03 | `deliverables/02-03-problem-bank.md` | 10–15 ranked candidate problems |

## Success Criteria

1. "Something changed" disruption scenarios identified across all 4 sectors
2. Each disruption has Trigger Event, Current Workaround, and Business Consequence documented
3. A clean list of 10–15 candidate problems spanning all 4 sectors exists
4. Problems span different sectors and involve multiple baseline systems
5. Each problem has quantified business impact where possible

## Exit Gate

Phase 2 is complete when:
- [ ] All 3 deliverables exist in `deliverables/`
- [ ] Every checkbox in every task is checked
- [ ] Problem Bank contains 10–15 problems spanning all 4 sectors
- [ ] Each problem passes the inclusion criteria checklist
