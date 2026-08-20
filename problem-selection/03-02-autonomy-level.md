# 03-02: Autonomy Calibration & HITL Guardrails — PB-12

**Flagship Problem:** PB-12 — Multi-Party ITT Coordination Failure (Cross-Terminal)  
**Parent Cluster:** C2 — Manual Multi-Party Coordination  
**Last updated:** 2026-08-19

---

## Step 1: Stakeholder Authority & Governance Mapping

### Decision Ownership Matrix

| Decision | Owner | Authority Scope | Agent Role |
|----------|-------|----------------|------------|
| **Container release from PPT yard** | PSA Singapore (PPT Yard Planner) | Approve container readiness for ITT dispatch | Agent can verify readiness, cannot override yard hold |
| **Road ITT truck dispatch** | PSA Singapore (ITT Coordinator) via OptETruck | Authorise truck deployment from PPT | Agent can compute optimal dispatch, cannot commit without sign-off |
| **Sea ITT feeder departure** | Feeder Operator | Confirm berth availability, departure time | Agent can query schedule, cannot force departure |
| **Feeder vessel schedule hold** | Feeder Operator + Shipping Line | Commercial decision to hold or depart | Agent can simulate cost of hold vs. departure, cannot negotiate |
| **Tuas yard receiving capacity** | PSA Singapore (Tuas Yard Planner) | Approve incoming container allocation | Agent can recommend block assignment, cannot override |
| **QC loading sequence at Tuas** | PSA Singapore (Ship Planner) | Final loading order | Agent can propose re-sequence, cannot commit |
| **Cross-terminal inventory visibility** | PORTNET (shared inventory layer) | Real-time container status | Agent queries but does not modify PORTNET state |

### Governance Constraints

**PSA Singapore** controls the terminal operations at both PPT and Tuas. The agent operates within PSA's authority — it can query, simulate, and recommend, but state-mutating actions at both terminals require PSA operator approval.

**Feeder Operators** are external commercial entities. The agent cannot compel schedule changes. It can only present cost-benefit analysis and recommend actions to the ITT coordinator, who then contacts the feeder operator.

**Shipping Lines** own the cargo contracts. Decisions about cargo roll, priority, or SLA impact are commercial decisions outside the agent's authority.

---

## Step 2: Operational Risk Profiling

### Risk Vector Assessment

| Risk Vector | Rating | Rationale |
|-------------|--------|-----------|
| **Physical & Terminal Risk** | **Low** | ITT coordination is a logistics scheduling problem. No hazardous cargo handling, no crane proximity risk, no physical safety concern from the agent's recommendations. |
| **Demurrage & Charter Liability** | **High** | Vessel delay at Tuas costs $3,000–$5,000/hr. Feeder vessel hold costs $800–$1,500/hr. Incorrect ITT split can cascade to missed feeder connections and downstream demurrage. |
| **Downstream Cascade Risk** | **High** | A wrong split decision (too many containers by road, road blocked) or (too many by sea, feeder delayed) can cascade to vessel loading delays at Tuas, missed feeder departures, and cargo SLA breaches at destination ports. |
| **Contractual & Commercial Risk** | **Medium** | Rolling cargo or delaying feeders affects customer SLA. But the ITT coordination problem is primarily operational — the agent optimises transport mode split, not commercial terms. |

**Overall Risk Rating: HIGH** — driven by demurrage liability and cascade risk.

### Risk Justification for Autonomy Tier

The HIGH risk rating comes from financial exposure ($15K–$29K per incident) and downstream cascade potential, NOT from physical safety. This argues for a human-in-the-loop approach where the agent proposes and the operator commits — but does not argue for full advisory (the agent can handle low-risk simulation and read-only queries autonomously).

---

## Step 3: Autonomy Level Selection

### Selected Tier: Tier 2 — Human-in-the-Loop (HITL) Exception Solver

### Why Tier 2 Over Full Autonomy (Countering the "Autonomy Trap")

**The Autonomy Trap:** Higher autonomy is not automatically better. An agent that acts without human oversight on a HIGH-risk problem with $15K–$29K per-incident financial exposure creates unacceptable liability. One wrong recommendation (e.g., committing to a sea ITT split when the feeder is about to be delayed) can cascade to missed connections and customer SLA breaches.

**Why Tier 2 is optimal for PB-12:**

1. **Multi-party authority boundaries:** The agent cannot unilaterally commit feeder operators or shipping lines to schedule changes. It must present recommendations to the ITT coordinator, who then communicates with external parties. Tier 2 enforces this boundary by halting at the approval gate before any external commitment.

2. **Cross-terminal state asymmetry:** PPT and Tuas CITOS are separate instances with 30–60 min data latency. The agent operates on potentially stale data. Tier 2 ensures a human reviews the recommendation against current operational reality before execution.

3. **Financial cascade risk:** The wrong road/sea split can cascade to missed feeder connections, downstream port delays, and customer SLA breaches. The cost of a bad recommendation exceeds the cost of a 30-second human review. Tier 2 eliminates this risk.

4. **Competition evaluation alignment:** The competition's Evaluation Pillars include "Scalable & Responsible AI." A Tier 2 HITL design demonstrates responsible autonomy — the agent handles complexity and reasoning, but defers to humans for state-changing decisions. This is more defensible than full autonomy.

### Why Tier 2 Over Full Advisory (Tier 1)

The agent can do more than just present information. It can:
- Run simulations (road/sea cost models, capacity checks)
- Compute optimal splits (multi-constraint optimisation)
- Predict downstream impact (vessel loading sequence effects)
- Draft recovery proposals (pre-formatted for ITT coordinator review)

These are cognitively complex tasks that justify agent autonomy. Tier 1 (advisory only) would waste the agent's reasoning capability by reducing it to a data aggregator.

---

## Step 4: Automated vs. Human-Gated Actions

### Automated Actions (Read-Only / Low-Risk Simulation)

These actions execute without human approval. They are all read-only queries or simulation computations that produce recommendations but do not mutate any system state.

| Tool Call | Description | Risk Level | Justification |
|-----------|-------------|------------|---------------|
| `get_itt_candidates(cit_ppt, vessel_id)` | Query PPT CITOS for containers requiring cross-terminal transfer | None | Read-only inventory query |
| `check_road_itt_capacity(optetruck, terminal, time_window)` | Query OptETruck for available trucks, transit time, and road conditions | None | Read-only capacity check |
| `check_sea_itt_capacity(portnet, feeder_id)` | Query PORTNET for feeder vessel availability, berth status, and departure window | None | Read-only schedule query |
| `get_feeder_downstream_impact(feeder_id, hold_hours)` | Simulate downstream port impact of holding feeder | None | Simulation only — no commitment |
| `compute_itt_split(candidates, road_capacity, sea_capacity)` | Run multi-constraint optimisation for road/sea allocation | None | Computation only — output is a recommendation |
| `estimate_yard_to_qc_time(tuas_yard_block, qc_id)` | Estimate time from yard block to QC loading position | None | Read-only time estimate |

**Total automated action space: 6 tools** — all read-only or simulation.

### Mandatory Human Approval Gates (State-Mutating Actions)

These actions require ITT coordinator sign-off before execution. The agent presents a pre-formatted approval card with the recommended action, cost analysis, and risk assessment.

| Tool Call | Description | Risk Level | Approval Gate |
|-----------|-------------|------------|---------------|
| `dispatch_road_itt(optetruck, truck_count, route)` | Commit trucks to road ITT dispatch | High | ITT coordinator must approve truck count and route before dispatch |
| `request_feeder_hold(portnet, feeder_id, hold_hours)` | Request feeder operator to hold departure | High | ITT coordinator must review cost analysis before contacting feeder operator |
| `update_tuas_loading_sequence(cit_tuas, itt_eta, container_ids)` | Modify Tuas QC loading sequence to accommodate ITT arrivals | High | Ship planner must approve re-sequence before commit |
| `notify_yard_delay(cit_tuas, delayed_containers, new_eta)` | Notify Tuas yard planner of delayed container arrivals | Medium | Yard planner must acknowledge before re-allocation |
| `commit_itt_split(road_count, sea_count, container_ids)` | Finalise the road/sea ITT split for execution | Critical | ITT coordinator must sign off on final split — this is the single most consequential decision |

### HITL Approval Card Design

When the agent reaches a human approval gate, it presents a structured card:

```
┌─────────────────────────────────────────────────────────┐
│  ITT COORDINATION — APPROVAL REQUIRED                   │
├─────────────────────────────────────────────────────────┤
│  ACTION: Commit ITT split — 80 containers by road,     │
│          40 containers by sea                           │
│  VESSEL: [Vessel Name] — Tuas departure 2000           │
│  DEADLINE: ITT must arrive at Tuas by 1800             │
├─────────────────────────────────────────────────────────┤
│  COST ANALYSIS:                                         │
│  • Road ITT: 16 trucks × $150/trip = $2,400           │
│  • Sea ITT: Feeder hold 1 hr = $1,200                  │
│  • If NOT split (100% road): 25 trucks, road congestion│
│    risk, $3,750 + 40 min delay                         │
│  • If NOT split (100% sea): feeder departs, 40         │
│    containers missed connection, $12,000 SLA breach    │
├─────────────────────────────────────────────────────────┤
│  RISK: Feeder destination tidal window at 2300 —       │
│        hold cannot exceed 1.5 hrs                      │
├─────────────────────────────────────────────────────────┤
│  [APPROVE]  [MODIFY]  [REJECT]                         │
└─────────────────────────────────────────────────────────┘
```

---

## Step 5: Escalation Trigger Policies

These conditions force escalation to the Terminal Duty Manager (one level above ITT coordinator) regardless of ITT coordinator availability.

| Trigger | Threshold | Rationale |
|---------|-----------|-----------|
| **Model confidence below threshold** | Confidence score < 0.85 | Agent is uncertain about optimal split — requires senior judgment |
| **Feeder hold exceeds downstream tolerance** | Hold request > 1.5 hrs | Feeder may miss downstream tidal window — commercial risk escalation |
| **Financial recovery cost exceeds limit** | Recommended action cost > $10,000 | High single-action cost — requires duty manager sign-off |
| **Data latency exceeds freshness window** | PPT/Tuas CITOS data age > 30 min | Agent operating on stale cross-terminal data — human must verify current state |
| **Road ITT capacity below threshold** | Available trucks < 60% of requirement | Insufficient road capacity — requires emergency sea ITT coordination |
| **Feeder operator unresponsive** | No response within 15 min of query | Cannot confirm feeder availability — human must escalate via phone |
| **Conflict between PPT and Tuas planners** | PPT planner and Tuas planner recommend different splits | Cross-terminal disagreement — requires duty manager arbitration |

### Escalation Protocol

When an escalation trigger fires:

1. Agent halts current workflow
2. Agent presents escalation card to Terminal Duty Manager:
   ```
   ┌─────────────────────────────────────────────────────┐
   │  ESCALATION — DUTY MANAGER REVIEW REQUIRED          │
   ├─────────────────────────────────────────────────────┤
   │  TRIGGER: [reason]                                  │
   │  CURRENT STATE: [summary of ITT situation]          │
   │  AGENT RECOMMENDATION: [what agent would have done] │
   │  BLOCKER: [why agent cannot proceed]                │
   ├─────────────────────────────────────────────────────┤
   │  [OVERRIDE]  [DEFER]  [REASSIGN]                   │
   └─────────────────────────────────────────────────────┘
   ```
3. Agent does not proceed until duty manager responds

---

## Acceptance Criteria Verification

- [x] **Clear separation between PSA authority vs. Carrier/Feeder authority** — Step 1 decision ownership matrix defines 7 decision categories with explicit owners.
- [x] **Defensible justification against full autonomy** — Step 3 counters the Autonomy Trap with 4 arguments (multi-party boundaries, data asymmetry, cascade risk, competition alignment).
- [x] **Concrete table of Automated Tool Calls vs. Mandatory HITL Approval Gates** — Step 4 defines 6 automated tools and 5 human-gated actions with risk ratings.

---

## Risk Summary

| Dimension | Rating | Agent Mitigation |
|-----------|--------|-----------------|
| Physical & Terminal | Low | No physical actions — logistics scheduling only |
| Demurrage & Charter | High | HITL gate on all state-mutating actions; cost analysis on every approval card |
| Downstream Cascade | High | Escalation triggers for feeder hold tolerance and financial thresholds |
| Contractual & Commercial | Medium | Agent does not make commercial decisions — presents cost analysis for human judgment |

---

## Next Step

- **03-03:** Lock Master Problem Charter with mock API specifications, ROI model, and demo storyboard

---

## Sources

- `problems/02-03-problem-bank.md` — PB-12 problem charter and mock tools
- `problems/02-02-failure-modes.md` — D4 failure mode analysis
- `research/flows/critical-flows.md` — ITT coordination decision flow
- `research/systems/baseline-systems.md` — OptETruck, CITOS, PORTNET profiles
