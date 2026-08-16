# Phase 3: Problem Evaluation, Litmus Testing & Final Selection — PLAN

**Created:** 2026-08-17
**Status:** Ready to execute
**Depends on:** Phase 2
**Requirements:** P3-01, P3-02, P3-03, COMP-01, COMP-02

## Goal

Select the single best problem for an Agentic AI solution and quantify its impact via the 5-Point Litmus Test and Master Problem Charter.

## Tasks

### 03-01: Apply the 5-Point Agentic AI Litmus Test

Score every Problem Bank candidate against all 5 litmus-test criteria.

**Deliverable:** `deliverables/03-01-litmus-test-scores.md` — scored matrix of all candidates

**For each problem in the Problem Bank, evaluate:**

| # | Test Criterion | Requirement for Passing |
|---|---------------|----------------------|
| 1 | **Non-Deterministic** | Cannot be solved by a simple database query, rule script, or basic linear optimizer. Requires situational reasoning over dynamic context. |
| 2 | **Multi-Tool Calling** | Needs to interact with at least 3 distinct systems or data sources (e.g., PORTNET, CITOS, Haulier TMS, Weather/AIS). |
| 3 | **Multi-Step Execution** | Requires a sequence: Ingest → Diagnose → Plan → Execute Tool A → Verify → Execute Tool B. |
| 4 | **Uncertainty Handling** | Involves incomplete data, conflicting inputs, or operational latency where an agent must make safe judgments. |
| 5 | **Measurable ROI** | The outcome directly reduces vessel dwell time, container re-handles, haulier wait times, or demurrage costs. |

**Scoring per criterion:** PASS / PARTIAL / FAIL

**Research fields per problem:**
- [ ] Non-Deterministic: Can a rule/script solve this? (PASS if no)
- [ ] Multi-Tool: Does it need 3+ distinct system calls? (PASS if yes)
- [ ] Multi-Step: Does it require 3+ sequential steps? (PASS if yes)
- [ ] Uncertainty Handling: Does it involve incomplete/conflicting data? (PASS if yes)
- [ ] Measurable ROI: Can we put a dollar/time figure on the outcome? (PASS if yes)

**Acceptance:**
- [ ] Every Problem Bank problem scored against all 5 criteria
- [ ] Problems with any FAIL are eliminated from consideration
- [ ] Remaining problems ranked by total PASS count

---

### 03-02: Define the Target Autonomy Level

For the top-ranking problems, determine the appropriate autonomy level.

**Deliverable:** `deliverables/03-02-autonomy-level.md` — autonomy recommendation with justification

**Autonomy levels (from CodeSprint.md):**

- [ ] **Advisory (Copilot):** High physical risk; agent suggests plans, human manually triggers actions
- [ ] **HITL Exception Solver (Recommended):** Medium risk; agent autonomously gathers data, runs recovery simulations, drafts API updates, and waits for 1-click human confirmation before executing
- [ ] **Supervised Autonomous:** Low risk; agent executes actions directly and notifies the human, escalating only when an error occurs

**Research fields:**
- [ ] For each top candidate: assess operational risk level (High / Medium / Low)
- [ ] Map risk level to autonomy level
- [ ] Identify which HITL gates are needed (what actions require human approval?)
- [ ] Apply the "Autonomy Trap" warning: "Higher autonomy is not automatically better"

**Acceptance:**
- [ ] Top 3 problems each have an autonomy level assigned
- [ ] Autonomy level justified against operational risk for each
- [ ] HITL gates identified for recommended problem

---

### 03-03: Lock ONE Master Problem Charter

Select the single best problem and write the charter.

**Deliverable:** `deliverables/03-03-master-charter.md` — final problem selection document

**Charter fields:**
- [ ] **Problem Statement:** One clear sentence
- [ ] **Sector:** Which of the 4 sectors
- [ ] **Systems Affected:** Which baseline systems involved
- [ ] **Target User Persona:** e.g., Terminal Duty Manager, ITT Coordinator, Haulier Dispatcher
- [ ] **Autonomy Level:** Advisory / HITL Exception Solver / Supervised Autonomous
- [ ] **HITL Gates:** Specific actions requiring human approval
- [ ] **Business Impact Equation:** Exact formula (e.g., *Estimated Annual Savings = Avoided Vessel Delays × Hourly Port Cost + Avoided Yard Re-handles × Move Cost*)
- [ ] **Expected ROI:** Quantified estimate with assumptions
- [ ] **Agentic Capabilities Required:** Which of the 6 mandatory capabilities are exercised
- [ ] **Why Agentic:** Why this cannot be solved by rules/scripts (litmus test evidence)

**Acceptance:**
- [ ] One problem selected (not two, not a tie)
- [ ] All 10 charter fields completed
- [ ] Business impact equation uses specific variables (not vague)
- [ ] Target user persona is a specific role (not "operations team")
- [ ] Charter passes Innovation & Originality and Scalability & Responsible AI evaluation gates

---

## Deliverables Summary

| Task | Deliverable | Output |
|------|-------------|--------|
| 03-01 | `deliverables/03-01-litmus-test-scores.md` | Scored matrix of all candidates |
| 03-02 | `deliverables/03-02-autonomy-level.md` | Autonomy recommendation with justification |
| 03-03 | `deliverables/03-03-master-charter.md` | Final problem selection charter |

## Success Criteria

1. Every candidate problem scored against all 5 litmus-test criteria
2. Target autonomy level defined and justified against operational risk
3. Single Master Problem Charter locked with persona, autonomy level, and business impact equation
4. Selected problem passes Innovation & Originality and Scalability & Responsible AI evaluation gates
5. Business impact equation uses quantified variables

## Exit Gate

Phase 3 is complete when:
- [ ] All 3 deliverables exist in `deliverables/`
- [ ] Every checkbox in every task is checked
- [ ] Master Problem Charter is finalized and signed off
- [ ] The team knows exactly what problem they are solving, for whom, and what the ROI is
- [ ] The charter can be handed to Phase 4 (architecture) without ambiguity
