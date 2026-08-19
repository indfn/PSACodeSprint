# 03-02: Autonomy Level & HITL Guardrails — PB-04

**Status:** Complete  
**Flagship Problem:** PB-04 — Transhipment Missed-Connection Recovery  
**Parent Cluster:** Cluster 2 — Manual Multi-Party Coordination  
**Last updated:** 2026-08-19

---

## Step 1: Operational Risk & Hazard Profiling

**Method:** Evaluate PB-04 across 4 risk vectors. Rated: Low / Medium / High / Critical.

---

### 1.1 Physical Safety & Terminal Equipment

**Rating: LOW**

PB-04 involves container loading/re-sequencing decisions — no direct physical safety risk. The agent's recommendations affect:
- QC loading sequence changes (paperwork, not physical crane movement)
- Yard block re-sequencing (container position changes, no hazardous materials involved)
- Feeder departure timing (advisory only — the agent cannot order a vessel to sail)

**Risk factors:**
- No dangerous goods involved (transhipment containers are general cargo)
- No crane movement recommendations — only loading sequence adjustments
- No direct interaction with physical equipment

**Mitigation:** Agent operates in advisory mode for all physical operations. No direct equipment control.

---

### 1.2 Financial & Demurrage Liability

**Rating: HIGH**

The decisions recommended by the agent have direct financial consequences:
- **Hold Feeder 2 hours:** Costs ~$1,600–$3,000 in feeder demurrage
- **Roll 40 containers:** Costs ~$4,000–$12,000 in customer SLA penalties + $100–$300/container/day demurrage
- **Re-prioritise QC:** Costs ~$900–$1,500 in re-handle operations + potential cascade to next vessel
- **Wrong decision:** Could result in missed connections worth $30K–$75K

**Risk factors:**
- Hold vs. roll decision has irreversible financial impact within 2–4 hours
- Customer SLA penalties are contractual and cannot be reversed
- QC re-prioritisation affects multiple vessels — wrong priority cascades

**Mitigation:** Mandatory human approval gate before any financial commitment. Agent presents cost comparison, human decides.

---

### 1.3 Operational Cascade Risk

**Rating: HIGH**

Wrong decisions propagate across multiple systems:
- **Feeder hold:** Delays downstream ports, affects other vessels' schedules, may cause port congestion at destination
- **Container roll:** Customer must be notified, cargo owner may need to adjust manufacturing/shipping schedule
- **QC re-prioritisation:** Adjacent berth vessels affected, yard planner must re-sequence, AGV dispatch changes

**Risk factors:**
- Decision at T=0 affects vessel schedules 12–24 hours downstream
- Yard planner re-sequencing takes 4–8 hours to fully stabilise
- Shipping line negotiations involve commercial relationships — agent cannot make binding commitments

**Mitigation:** Agent presents cascading impact analysis. Human approves each major step. Agent does not commit to downstream vessels without explicit duty manager approval.

---

### 1.4 Stakeholder & Regulatory Exposure

**Rating: MEDIUM**

- No direct regulatory implications (no DG, no customs, no MPA)
- Stakeholder exposure: shipping line relationships, feeder operator negotiations, cargo owner SLA
- Commercial negotiations (hold terms, demurrage allocation) require human authority

**Risk factors:**
- Agent cannot make binding commercial commitments on behalf of PSA
- Feeder operator hold negotiations involve multi-party commercial terms
- Customer SLA breach notification requires human judgment on messaging and timing

**Mitigation:** Agent drafts notification templates and negotiation positions. Human reviews and sends. Agent does not represent PSA in commercial negotiations.

---

### Risk Profile Summary

| Risk Vector | Rating | Key Concern |
|-------------|:------:|-------------|
| Physical Safety & Terminal Equipment | LOW | No direct physical risk |
| Financial & Demurrage Liability | HIGH | Irreversible hold/roll decisions |
| Operational Cascade Risk | HIGH | Downstream vessel and port impact |
| Stakeholder & Regulatory Exposure | MEDIUM | Commercial negotiation authority |
| **Overall** | **MEDIUM-HIGH** | Financial and cascade risks dominate |

---

## Step 2: Autonomy Level Selection & Justification

### Three Tiers

| Tier | Description | Risk Fit |
|------|-------------|----------|
| **Tier 1: Advisory Copilot** | Agent synthesises data and presents ranked recovery options; human manually executes all actions | High Risk |
| **Tier 2: HITL Exception Solver** | Agent diagnoses, queries tools, runs simulations, drafts API payloads, but halts at Approval Gate for human verification before committing state changes | Medium Risk |
| **Tier 3: Supervised Autonomous** | Agent executes actions autonomously and logs results; only triggers human intervention when confidence is low or API error occurs | Low Risk |

### Selected Tier: Tier 2 — Human-in-the-Loop Exception Solver

**Justification:**

1. **Financial risk demands human gate.** The hold vs. roll decision costs $1,600–$12,000+. An agent committing this without human approval exposes PSA to irreversible financial loss. The agent must present the cost comparison and recommendation, but a human must click "Approve."

2. **Cascade risk requires human awareness.** Holding a feeder vessel delays its entire downstream schedule. The agent can model this impact, but the duty manager must understand and accept the cascade before it happens.

3. **Commercial negotiations require human authority.** The agent cannot commit PSA to hold terms with feeder operators or negotiate SLA breach settlements with shipping lines. These require human judgment and authority.

4. **Countering the Autonomy Trap:** Higher autonomy (Tier 3) is not chosen because:
   - The problem involves irreversible financial commitments
   - Downstream cascade impact extends beyond PSA's direct control
   - Commercial relationships with shipping lines and cargo owners require human judgment
   - Competition judges will appreciate defensible HITL design over reckless autonomy

5. **Why not Tier 1 (Advisory)?** The agent's value is in diagnosis, multi-tool orchestration, and plan generation — not just data presentation. Tier 2 allows the agent to do the heavy lifting (query 4 systems, simulate scenarios, draft plans) while keeping human control at the decision point. This maximises the agentic AI demonstration.

---

## Step 3: HITL Trigger Policies & Safety Guardrails

---

### 3.1 Automated Action Space (No Human Approval Required)

These read-only and low-risk tool calls execute without human approval:

| Tool | Why Safe | Risk Level |
|------|----------|:----------:|
| `get_transhipment_connections(vessel_id)` | Read-only query — no state mutation | None |
| `calculate_discharge_rate(vessel_id, qc_count)` | Computation only — no action | None |
| `query_feeder_flexibility(feeder_id)` | Read-only query to PORTNET | None |
| `estimate_yard_to_wharf_time(yard_block, wharf_position)` | Computation only | None |
| `simulate_hold_vs_roll(scenario)` | Simulation — no commitment | None |
| `notify_stakeholders(event_type, parties, message)` | Informational alerts only — no action requests | Low |

**Total: 6 automated tools** (all read-only or informational)

---

### 3.2 Human Approval Gates (Mandatory Sign-Off)

These state-mutating actions require mandatory human verification:

| Tool | Gate | UI Card | Why Required |
|------|------|---------|--------------|
| `request_feeder_hold(feeder_id, hold_hours, reason)` | Duty Manager Approval | "Hold Feeder [X] for [Y] hours? Cost: $[Z]. Cascade: [summary]" | Commercial commitment — feeder operator must agree, financial impact irreversible |
| `roll_containers(container_ids, next_sailing, reason)` | Duty Manager + Shipping Line Approval | "Roll [N] containers to [next sailing]? SLA impact: $[X]. Customer notification: [draft]" | Customer SLA breach — requires shipping line authority |
| `reprioritise_qc(vessel_id, new_qc_count, reason)` | Berth Planner Approval | "Reduce QCs for [vessel A] from 4→2, add 2 to [vessel B]? Impact: [delay summary]" | Affects multiple vessels — berth planner must confirm no safety/stability conflicts |
| `update_yard_plan(block_ids, new_assignments)` | Yard Planner Approval | "Re-sequence yard blocks [X,Y,Z]? Re-handle count: [N]. Cost: $[Z]" | Yard plan change — affects loading sequence and AGV routing |
| `commit_recovery_plan(plan_id, approved_by)` | Final Commit | "Execute full recovery plan? Total cost: $[X]. Hold: [Y]. Roll: [Z]. QC: [W]" | Final state change — irreversible commitment |

**Total: 5 human approval gates** (each with cost summary and cascade preview)

---

### 3.3 Escalation Trigger Thresholds

Conditions that force escalation to the Terminal Duty Manager (bypassing agent autonomy):

| Threshold | Condition | Action |
|-----------|-----------|--------|
| **Model Confidence < 0.85** | Agent's confidence in hold vs. roll recommendation is below 85% | Escalate: "I'm not confident in this recommendation. Please review manually." |
| **Data Latency > 30 min** | Feeder schedule data or vessel ETA is older than 30 minutes | Escalate: "Feeder schedule data is [X] minutes stale. Recommendation may be outdated." |
| **Financial Recovery Cost > $10,000** | Total cost of recommended action exceeds $10,000 | Escalate with full cost breakdown + alternative scenarios |
| **Cascade Impact > 2 Vessels** | Recommended action affects more than 2 downstream vessels | Escalate with cascade diagram |
| **Feeder Operator Non-Responsive** | Feeder operator does not respond within 15 minutes | Escalate: "Feeder operator non-responsive. Manual contact required." |
| **Conflicting Priority Vessels** | Recommended QC re-prioritisation affects a vessel with higher priority | Escalate: "Conflict: vessel [X] has higher priority. Manual resolution required." |

**Escalation UI:** Agent pauses execution, presents full context summary, and waits for human instruction. No autonomous fallback.

---

### 3.4 Safety Guardrails

| Guardrail | Description |
|-----------|-------------|
| **No Commercial Commitment** | Agent never commits PSA to financial terms, hold agreements, or SLA settlements. All commercial decisions require human authority. |
| **No Irreversible Actions Without Gate** | Any action that cannot be undone (QC reassignment, container roll, feeder hold) requires human approval. |
| **Stale Data Detection** | Agent checks data freshness before every recommendation. If data >30 min old, agent flags staleness and pauses. |
| **Cost Ceiling** | If total recommended action cost > $10,000, agent escalates regardless of other factors. |
| **Cascade Limit** | If recommended action affects >2 downstream vessels, agent escalates with cascade diagram. |
| **Audit Trail** | Every agent action (tool call, recommendation, notification) is logged with timestamp, input, output, and approval status. Full traceability for post-incident review. |

---

## Acceptance Criteria Verification

- [x] Risk profiles documented across all 4 risk vectors (Physical: LOW, Financial: HIGH, Cascade: HIGH, Stakeholder: MEDIUM)
- [x] Explicit justification countering the "Autonomy Trap" (Step 2, justification point 4)
- [x] Concrete HITL policies established: 6 automated tools, 5 approval gates, 6 escalation triggers

---

## Sources

- `problems/02-03-problem-bank.md` — PB-04 problem charter
- `problems/02-02-failure-modes.md` — A4 failure mode analysis
- `research/flows/critical-flows.md` — Information and decision flows
- `research/systems/baseline-systems.md` — CITOS, PORTNET, OptEVoyage system profiles
