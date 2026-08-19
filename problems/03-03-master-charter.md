# Master Problem Charter: Transhipment Missed-Connection Recovery Agent

**Status:** Locked  
**Flagship Problem:** PB-04 — Transhipment Missed-Connection Recovery (100+ Containers)  
**Parent Cluster:** Cluster 2 — Manual Multi-Party Coordination (9/16 problems)  
**Last updated:** 2026-08-19  
**Phase 4 Ready:** Yes

---

## 1. Executive Summary & Problem Definition

- **Sector:** Berth & Marine
- **Target User Persona:** Terminal Duty Manager (primary), Ship Planner (secondary)
- **Parent Root-Cause Cluster:** Cluster 2 — Manual Multi-Party Coordination
- **Core Operational Friction:** When a mother vessel ETA slips 8+ hours, 100+ transhipment containers threaten to miss outbound feeder connections. No system jointly calculates which feeders are still achievable. Resolution requires 3–6 hours of phone calls, WhatsApp messages, and email chains between duty manager, ship planner, shipping line agent, and feeder operator — each making decisions with incomplete information. The hold vs. roll decision (hold feeder = $1,600–$3,000 demurrage; roll containers = $4,000–$12,000 SLA breach) is made under extreme time pressure with no cost-modelling tool.
- **Selected Autonomy Level:** Tier 2 — Human-in-the-Loop (HITL) Exception Solver

---

## 2. As-Is vs. To-Be Workflow Comparison

### As-Is Baseline (Current Manual Process)

```
T+0 min    Duty manager receives delay notification (phone + PORTNET alert)
T+5 min    Opens CITOS berth planner to assess affected vessel
T+10 min   Calls ship planner (phone) for discharge options
T+20 min   Ship planner manually computes: discharge rate × time = containers recoverable
T+30 min   Contacts shipping line agent (phone) to discuss hold vs. roll
T+40 min   Shipping line contacts feeder operator (phone) for hold feasibility
T+50 min   Feeder operator assesses downstream port impact
T+60 min   Decision discussion between duty manager, shipping line, feeder operator
T+70 min   If hold: shipping line confirms hold terms (commercial negotiation)
T+80 min   If roll: shipping line confirms which containers to roll
T+90 min   Yard planner notified (phone) to re-sequence transhipment blocks
T+100 min  Ship planner updates CITOS stowage plan for adjusted loading sequence
T+120 min  Recovery plan stabilised, execution begins
T+180 min  Full recovery complete (if no further complications)
```

**Total time: 2–6 hours.** 8–12 staff-hours of phone/WhatsApp coordination. 4–6 independent phone calls. No single system of record.

### To-Be Agentic Workflow

```
T+0 min    Agent receives OptEVoyage ETA slip event (webhook)
T+1 min    Agent queries PORTNET for dependent feeder connections
T+2 min    Agent queries CITOS for discharge rate and QC availability
T+3 min    Agent calculates: containers recoverable per feeder (discharge rate × time available)
T+4 min    Agent queries feeder flexibility (PORTNET: can feeder hold? downstream impact?)
T+5 min    Agent runs hold vs. roll simulation (cost model: $1,600 hold vs. $12K roll)
T+6 min    Agent generates recommendation with cost comparison
T+7 min    AGENT HALTS → Presents recommendation to Duty Manager for approval
T+8 min    Duty Manager reviews cost comparison, cascade diagram, and recommendation
T+9 min    Duty Manager clicks "Approve Hold Feeder 1" or "Approve Roll 40 Containers"
T+10 min   Agent executes approved plan: sends hold request to feeder operator
T+12 min   Agent updates yard plan (CITOS) and notifies yard planner
T+14 min   Agent updates stowage plan (CITOS) and notifies ship planner
T+15 min   Agent sends status summary to all affected parties
T+16 min   Recovery plan executing. Agent monitors for further ETA slips.
```

**Total time: 10–16 minutes.** 0.5 staff-hours. 1 human approval gate. Full audit trail in agent log.

---

## 3. Systems Integration & Mock API Specifications

### Baseline Systems Interfaced

| System | Role | Data Direction |
|--------|------|:--------------:|
| OptEVoyage | Vessel ETA tracking | Read |
| CITOS | Berth allocation + ship planning | Read/Write |
| PORTNET | Feeder schedules + EDI coordination | Read/Write |
| A*STAR FMS | AGV dispatch (indirect — yard plan affects AGV routing) | Read |

### Required Mock API Toolset (5 Tools)

#### Tool 1: `get_transhipment_connections`

```json
{
  "name": "get_transhipment_connections",
  "description": "Query all dependent feeder connections for a mother vessel, including departure times, container counts, and connection risk status.",
  "input": {
    "vessel_id": "string —母 vessel call sign or IMO number",
    "terminal": "string — 'PPT' or 'Tuas'"
  },
  "output": {
    "connections": [
      {
        "feeder_id": "string",
        "feeder_name": "string",
        "departure_time": "ISO 8601 datetime",
        "containers_onboard": "integer — transhipment containers assigned",
        "destination_port": "string",
        "connection_status": "enum: 'AT_RISK' | 'SAFE' | 'MISSED'"
      }
    ],
    "total_at_risk": "integer",
    "total_containers_affected": "integer"
  }
}
```

**Source system:** PORTNET feeder schedule API + CITOS berth allocation

---

#### Tool 2: `calculate_discharge_rate`

```json
{
  "name": "calculate_discharge_rate",
  "description": "Estimate recoverable containers per hour based on QC count, vessel crane configuration, and current discharge progress.",
  "input": {
    "vessel_id": "string",
    "qc_count": "integer — number of QCs assigned (may differ from original plan)",
    "time_available_hours": "float — hours until feeder departure"
  },
  "output": {
    "moves_per_hour": "integer — estimated discharge rate",
    "containers_recoverable": "integer — total containers that can be discharged in time_available",
    "confidence": "float — 0.0 to 1.0 based on historical discharge data",
    "constraints": ["string — any stability or access constraints limiting rate"]
  }
}
```

**Source system:** CITOS ship planning + historical discharge data

---

#### Tool 3: `query_feeder_flexibility`

```json
{
  "name": "query_feeder_flexibility",
  "description": "Check if a feeder vessel can delay departure, including downstream port impact and estimated hold cost.",
  "input": {
    "feeder_id": "string",
    "requested_hold_hours": "float"
  },
  "output": {
    "hold_feasible": "boolean",
    "hold_cost_usd": "integer — estimated demurrage for hold period",
    "downstream_impact": [
      {
        "port": "string",
        "delay_hours": "float",
        "estimated_cost_usd": "integer"
      }
    ],
    "operator_response": "enum: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'COUNTER_OFFER'",
    "response_deadline_minutes": "integer — time operator has to respond"
  }
}
```

**Source system:** PORTNET + feeder operator API (mocked)

---

#### Tool 4: `simulate_hold_vs_roll`

```json
{
  "name": "simulate_hold_vs_roll",
  "description": "Model total cost of hold vs. roll scenarios across all affected parties.",
  "input": {
    "scenario": {
      "hold_feeder_ids": ["string — feeders to hold"],
      "hold_hours": "float",
      "roll_container_count": "integer",
      "roll_to_sailing": "string — next available feeder ID"
    }
  },
  "output": {
    "total_cost_usd": "integer — sum of all cost components",
    "cost_breakdown": {
      "feeder_demurrage_usd": "integer",
      "container_demurrage_usd": "integer",
      "sla_penalty_usd": "integer",
      "rehandle_cost_usd": "integer",
      "cascade_cost_usd": "integer"
    },
    "alternative_scenarios": [
      {
        "description": "string",
        "total_cost_usd": "integer"
      }
    ]
  }
}
```

**Source system:** Cost model (built-in) + CITOS + PORTNET data

---

#### Tool 5: `commit_recovery_plan`

```json
{
  "name": "commit_recovery_plan",
  "description": "Execute approved recovery plan: update CITOS berth/yard plans, send notifications to affected parties, log actions.",
  "input": {
    "plan_id": "string — generated by agent",
    "approved_actions": ["string — list of approved action IDs"],
    "approved_by": "string — duty manager ID",
    "approval_timestamp": "ISO 8601 datetime"
  },
  "output": {
    "execution_status": "enum: 'EXECUTING' | 'COMPLETED' | 'PARTIAL' | 'FAILED'",
    "actions_executed": [
      {
        "action": "string",
        "system": "string",
        "status": "enum: 'SUCCESS' | 'FAILED' | 'PENDING'",
        "timestamp": "ISO 8601 datetime"
      }
    ],
    "notifications_sent": ["string — party notified"],
    "audit_log_id": "string — unique ID for full trace"
  }
}
```

**Source system:** CITOS + PORTNET + notification service

---

## 4. Operational Risk, Safety Guardrails & Fallbacks

### Mandatory HITL Gate

**Gate trigger:** After agent completes tool calls 1–4 (diagnose + simulate) and before executing any state-mutating action.

**UI Card presented to Duty Manager:**

```
┌─────────────────────────────────────────────────────────────┐
│  RECOVERY PLAN RECOMMENDATION                               │
│  Mother Vessel: [NAME] — ETA delayed [X] hours              │
│                                                             │
│  RECOMMENDATION: HOLD FEEDER 1 by 2 hours                   │
│                                                             │
│  Cost Comparison:                                           │
│  ┌──────────────────────┬───────────────┐                   │
│  │ Option               │ Total Cost    │                   │
│  ├──────────────────────┼───────────────┤                   │
│  │ Hold Feeder 1 (2hr)  │ $2,400        │                   │
│  │ Roll 40 containers   │ $12,000       │                   │
│  │ Hybrid (hold + roll) │ $5,600        │                   │
│  └──────────────────────┴───────────────┘                   │
│                                                             │
│  Cascade Impact:                                            │
│  • Feeder 1 downstream: Singapore → Port Klang delayed 2hr  │
│  • 40 rolled containers: next sailing Thursday              │
│                                                             │
│  [APPROVE HOLD]  [APPROVE ROLL]  [APPROVE HYBRID]  [REJECT]│
└─────────────────────────────────────────────────────────────┘
```

### Data Validation Guardrails

| Guardrail | Description |
|-----------|-------------|
| **Vessel ID format check** | Reject if vessel_id does not match IMO/ call sign pattern |
| **Time window sanity** | Reject if time_available_hours < 0 or > 168 (1 week) |
| **Container count bounds** | Reject if containers_onboard > 500 (likely data error for single vessel) |
| **Cost ceiling** | If total_cost_usd > $10,000, escalate regardless of other factors |
| **Data freshness** | If feeder schedule data > 30 min old, flag staleness and pause |

### Fallback / Exception Protocol

| Failure Mode | Agent Response |
|--------------|----------------|
| **Tool timeout (>10s)** | Retry once. If still failing, notify duty manager: "Unable to query [system]. Manual check required." Pause execution. |
| **Tool returns error (500)** | Log error. Notify duty manager with error details. Do not proceed with affected recommendation. |
| **Feeder operator non-responsive (>15 min)** | Escalate: "Feeder operator has not responded. Manual contact required." Pause execution. |
| **Conflicting data sources** | Present both data sources to duty manager. Flag discrepancy. Do not proceed until resolved. |
| **ETA further slip during execution** | Re-run diagnosis with updated ETA. Present revised recommendation. If plan was already approved, present revised plan for re-approval. |

---

## 5. Dual-Layer Quantified Business Impact & ROI Model

### Anchor Mathematical Impact Formula (PB-04 — The Flagship Problem)

```
Anchor Annual Savings = (Δ Vessel Dwell Hrs × C_vessel)
                      + (Δ Rolled Containers × C_roll)
                      + (Δ QC Re-handles × C_move)
                      + (Δ Staff Hours × C_staff)
```

### Cost Parameters & Assumptions

| Parameter | Value | Source |
|-----------|-------|--------|
| Vessel Demurrage / Charter Rate (C_vessel) | $3,000–$5,000/hr | Standard panamax feeder charter rate |
| Container Demurrage / Roll Cost (C_roll) | $100–$300/container/day | Industry standard demurrage rate |
| QC Re-handle Cost (C_move) | $30–$50/move | PSA terminal operating cost |
| Staff Hour Cost (C_staff) | $50–$80/hr | Terminal operations staff rate |
| Incident Frequency | 3–5/month | Phase 1 research: berth-marine.md |
| Average Delay | 8–12 hours | Phase 1 research: berth-marine.md |
| Average Containers at Risk | 80–150 | Phase 1 research: berth-marine.md |
| Average Rolled Containers (as-is) | 30–50 | Phase 2 failure mode analysis |
| Recovery Time Reduction (agent vs. manual) | 2–6 hrs → 10–16 min | Phase 2 failure mode analysis |
| Staff Hours Eliminated per Incident | 8–12 hrs | Phase 2 failure mode analysis |

### Single-Incident Savings (As-Is vs. To-Be)

| Cost Component | As-Is (Manual) | To-Be (Agent) | Δ Savings |
|----------------|:--------------:|:-------------:|:---------:|
| Feeder Demurrage (2hr hold) | $1,600–$3,000 | $1,600–$3,000 | $0 (same cost) |
| Rolled Containers (40 × $150/day × 1 day) | $4,000–$12,000 | $0–$2,000 (reduced rolls via faster decision) | $2,000–$10,000 |
| QC Re-prioritisation (30 moves) | $900–$1,500 | $300–$500 (faster, fewer re-handles) | $600–$1,000 |
| Vessel Delay Extension (from slow coordination) | $6,000–$15,000 | $0–$1,000 (faster resolution) | $5,000–$14,000 |
| Staff Hours (8–12 hrs × $65/hr) | $520–$780 | $30–$50 (1 approval gate) | $490–$730 |
| **Total per Incident** | **$13,020–$32,280** | **$1,930–$6,550** | **$8,090–$25,730** |

### Annual Flagship Savings (PB-04)

```
Low estimate:  3 incidents/month × 12 months × $8,090  = $291,240/year
High estimate: 5 incidents/month × 12 months × $25,730 = $1,543,800/year
Midpoint:      ~$917,520/year
```

### Cluster Generalization Impact Formula (Cluster 2 — Total Addressable Scaling)

```
Total Cluster Impact = Anchor Annual Savings + Σ Annual Savings(Sibling Problem_i)
```

### Cluster 2 Sibling Problems (9 total, PB-04 is anchor)

| Problem | Annual Incident Freq | Per-Incident Savings | Annual Savings |
|---------|:--------------------:|:--------------------:|:--------------:|
| **PB-04 (Anchor)** | 3–5/month | $8,090–$25,730 | $291K–$1.54M |
| PB-01 (Berth Delay) | 2–3/month | $15,000–$40,000 | $360K–$1.44M |
| PB-02 (DTQC Breakdown) | 4–6/month | $4,000–$8,000 | $192K–$576K |
| PB-03 (DG Compliance) | 1–2/month | $2,000–$6,000 | $24K–$144K |
| PB-05 (Reefer Excursion) | 5–8/month | $10,000–$25,000 | $600K–$2.4M |
| PB-09 (Haulier Disruption) | 2–4/month | $4,000–$7,000 | $96K–$336K |
| PB-10 (Sea-Air Cut-Off) | 1–2/month | $5,000–$15,000 | $60K–$360K |
| PB-11 (Customs Hold) | 2–4/month | $1,000–$3,000 | $24K–$144K |
| PB-12 (ITT Coordination) | 4–6/month | $4,000–$8,000 | $192K–$576K |

```
Total Cluster Annual Addressable: $1.84M–$7.52M
```

### Projected Net ROI

| Metric | Low | Mid | High |
|--------|:---:|:---:|:----:|
| Anchor Annual Savings (PB-04) | $291K | $918K | $1.54M |
| Total Cluster Addressable (9 problems) | $1.84M | $4.68M | $7.52M |
| Estimated Build Cost (hackathon) | $0 (sunk) | $0 (sunk) | $0 (sunk) |
| Estimated Operating Cost (mock) | $0 | $0 | $0 |
| **Net ROI** | **$1.84M** | **$4.68M** | **$7.52M** |

---

## 6. Cluster Scalability Blueprint (Platform Generalization)

### Sibling Problems Addressed by Same Core Architecture

| Problem | Shared Agentic Primitives | Customisation Needed |
|---------|--------------------------|---------------------|
| PB-01 (Berth Delay) | Multi-party notification, cost simulation, approval workflow | Add tidal window tool, QC sharing tool |
| PB-02 (DTQC Breakdown) | Multi-party notification, cost simulation, cascade prediction | Add AGV rerouting tool, maintenance prediction tool |
| PB-03 (DG Compliance) | Multi-party notification, regulatory workflow, cost simulation | Add IMDG segregation tool, MPA submission tool |
| PB-05 (Reefer Excursion) | Multi-party notification, diagnostic reasoning, resource dispatch | Add reefer telemetry tool, technician routing tool |
| PB-09 (Haulier Disruption) | Multi-party notification, cost simulation, slot rebalancing | Add GPS tracking tool, traffic prediction tool |
| PB-10 (Sea-Air Cut-Off) | Multi-party notification, temporal reasoning, cost simulation | Add customs pre-clearance tool, flight availability tool |
| PB-11 (Customs Hold) | Multi-party notification, document coordination, partial release | Add inspection scheduling tool, document verification tool |
| PB-12 (ITT Coordination) | Multi-party notification, mode optimisation, cost simulation | Add cross-terminal visibility tool, feeder scheduling tool |

### Shared Agentic Primitives

The same core architecture solves all 9 problems with minimal customisation:

| Primitive | Description | Reused Across |
|-----------|-------------|:-------------:|
| **Event Ingestion** | Webhook receiver for OptEVoyage, ARMS, ROCC, TradeNet alerts | All 9 |
| **Multi-Tool Orchestrator** | Reasoning loop: Ingest → Diagnose → Formulate → Execute → Evaluate | All 9 |
| **Cost Simulation Engine** | Financial impact modelling for hold/roll/reassign/rehandle decisions | All 9 |
| **Multi-Party Notification** | Structured notifications to duty manager, shipping line, feeder operator, customs | All 9 |
| **Approval Workflow** | HITL gate with cost comparison UI, approval tracking, audit log | All 9 |
| **Stale Data Detection** | Data freshness checks, staleness flagging, escalation triggers | All 9 |
| **Cascade Impact Predictor** | Downstream effect modelling across vessels, ports, and parties | PB-01, PB-02, PB-04, PB-09, PB-12 |

**Customisation per problem:** 1–2 problem-specific tools (e.g., IMDG segregation for PB-03, reefer diagnostics for PB-05). The core 7 primitives remain identical.

---

## 7. Execution Trace & Demo Storyboard

### Trigger Event Payload (Simulated Input)

```json
{
  "event_type": "VESSEL_ETA_UPDATE",
  "source": "OptEVoyage",
  "timestamp": "2026-09-01T08:00:00+08:00",
  "data": {
    "vessel_id": "EVERGREEN_GLORY",
    "vessel_name": "EVERGREEN GLORY",
    "imo_number": "9876543",
    "original_eta": "2026-09-01T10:00:00+08:00",
    "updated_eta": "2026-09-01T20:00:00+08:00",
    "delay_hours": 10,
    "delay_reason": "Weather diversion — Red Sea route",
    "terminal": "PPT",
    "berth": "B-12"
  },
  "affected_feeders": [
    {
      "feeder_id": "PIL_ASIANA",
      "feeder_name": "PIL Asiana",
      "departure_scheduled": "2026-09-01T18:00:00+08:00",
      "containers_assigned": 85,
      "destination": "Port Klang"
    },
    {
      "feeder_id": "SITC_SHANGHAI",
      "feeder_name": "SITC Shanghai",
      "departure_scheduled": "2026-09-01T22:00:00+08:00",
      "containers_assigned": 42,
      "destination": "Shanghai"
    },
    {
      "feeder_id": "ONE TOKYO",
      "feeder_name": "ONE Tokyo",
      "departure_scheduled": "2026-09-02T06:00:00+08:00",
      "containers_assigned": 28,
      "destination": "Tokyo"
    }
  ]
}
```

### Step-by-Step Expected Trace (Happy Path)

```
AGENT THOUGHT: Mother vessel delayed 10 hours. Original ETA 1000, new ETA 2000.
  3 feeders at risk. Need to determine: (1) which connections are still achievable,
  (2) cost of hold vs. roll per feeder, (3) recommend optimal recovery plan.

ACTION 1: get_transhipment_connections("EVERGREEN_GLORY", "PPT")
OBSERVATION: 155 total transhipment containers. PIL Asiana (85, dep 1800) = AT_RISK.
  SITC Shanghai (42, dep 2200) = AT_RISK. ONE Tokyo (28, dep 0600+1) = SAFE.

AGENT THOUGHT: PIL Asiana departs 2 hours after new vessel ETA (2000 vs. 1800).
  Container transport time = 30 min. So containers must be on wharf by 1730.
  Vessel arrives 2000 → cannot discharge by 1730 → PIL Asiana CONNECTION MISSED.
  SITC Shanghai departs 2200 → vessel arrives 2000, 2 hours to discharge.
  At 30 moves/hr × 2 hrs = 60 containers recoverable. 42 assigned → ALL RECOVERABLE.
  ONE Tokyo departs 0600+1 → vessel arrives 2000, 10 hours → ALL RECOVERABLE.

ACTION 2: calculate_discharge_rate("EVERGREEN_GLORY", 4, 8)
OBSERVATION: 30 moves/hr, 240 containers recoverable in 8 hrs. Confidence: 0.92.

ACTION 3: query_feeder_flexibility("PIL_ASIANA", 4)
OBSERVATION: Hold feasible. Cost: $2,400 (4hr × $600/hr). Downstream: Port Klang
  delayed 4hr. Cost: $1,800. Operator response: PENDING.

AGENT THOUGHT: PIL Asiana missed connection unless held. Hold cost = $2,400.
  Roll cost = 85 containers × $150/day = $12,750. Hold is cheaper by $10,350.
  But hold cascades to Port Klang ($1,800). Total hold cost = $4,200.
  Still cheaper than roll ($12,750). RECOMMENDATION: HOLD PIL Asiana.

ACTION 4: simulate_hold_vs_roll({
  hold_feeder_ids: ["PIL_ASIANA"],
  hold_hours: 4,
  roll_container_count: 0,
  roll_to_sailing: null
})
OBSERVATION: Total cost $4,200. Alternative scenarios:
  - Hybrid (hold PIL 2hr + roll 30): $5,600
  - Roll all 85: $12,750

AGENT: RECOMMENDATION READY. Presenting to Duty Manager.

╔══════════════════════════════════════════════════════════════╗
║  RECOVERY PLAN: EVERGREEN GLORY (delayed 10 hrs)            ║
║                                                              ║
║  RECOMMENDATION: HOLD PIL Asiana by 4 hours                  ║
║                                                              ║
║  ┌──────────────────────┬───────────────┐                    ║
║  │ Option               │ Total Cost    │                    ║
║  ├──────────────────────┼───────────────┤                    ║
║  │ Hold PIL Asiana 4hr  │ $4,200        │ ◄── RECOMMENDED   ║
║  │ Roll 85 containers   │ $12,750       │                    ║
║  │ Hybrid (hold+roll)   │ $5,600        │                    ║
║  └──────────────────────┴───────────────┘                    ║
║                                                              ║
║  Cascade: Port Klang delayed 4hr ($1,800)                    ║
║  SITC Shanghai: OK (42 containers recoverable)               ║
║  ONE Tokyo: OK (28 containers recoverable)                   ║
║                                                              ║
║  [APPROVE HOLD]  [APPROVE ROLL]  [APPROVE HYBRID]  [REJECT] ║
╚══════════════════════════════════════════════════════════════╝

DUTY MANAGER: Clicks [APPROVE HOLD]

ACTION 5: commit_recovery_plan("PLAN-001", ["HOLD_PIL_ASIANA"], "DM-CHEN", "2026-09-01T08:12:00+08:00")
OBSERVATION:
  - Hold request sent to PIL Asiana operator: SUCCESS
  - CITOS berth plan updated: PIL Asiana departure → 2200: SUCCESS
  - Yard planner notified (re-sequence 85 containers): SUCCESS
  - Ship planner notified (discharge sequence): SUCCESS
  - Audit log created: PLAN-001

AGENT: Recovery plan executed. Monitoring for further updates.
```

### Injected Failure / Edge Case Test

**Scenario: Feeder Operator Rejects Hold Request**

```
ACTION 3 (retry): query_feeder_flexibility("PIL_ASIANA", 4)
OBSERVATION: Hold feasible. Cost: $2,400. Operator response: REJECTED.
  Reason: "Downstream contract — cannot delay Port Klang arrival."

AGENT THOUGHT: Hold rejected. Must revise plan.
  Option A: Roll all 85 containers → $12,750
  Option B: Partial hold (PIL departs on time) + roll 85 → same as A
  Option C: Re-prioritise QC to maximise discharge before 1800
    At 30 moves/hr, time = 1000→1800 = 8 hrs → 240 containers
    But vessel arrives 2000, not 1000. Can't discharge before arrival.
  Option C is impossible (vessel not yet berthed).
  RECOMMENDATION: Roll 85 containers to SITC Shanghai (departs 2200).
  Cost: 85 × $150 = $12,750. But avoids $12,750 demurrage anyway.

AGENT: HOLD REJECTED. Revised recommendation presented.
  [APPROVE REVISED PLAN]  [ESCALATE TO DUTY MANAGER]
```

This edge case demonstrates:
1. Agent handles operator rejection gracefully
2. Agent re-runs simulation with revised constraints
3. Agent presents revised recommendation (not the same one)
4. Agent escalates when original plan fails

---

## Acceptance Criteria Verification

- [x] Single winning Flagship Problem locked with zero ambiguity (PB-04)
- [x] Clear Platform Generalization Blueprint linking back to Cluster 2 (8 sibling problems mapped)
- [x] Mathematical impact model contains both Anchor ROI ($291K–$1.54M) and Total Cluster ROI ($1.84M–$7.52M)
- [x] Defines 5 mock tool signatures with full input/output JSON specifications
- [x] Provides exact demo storyboard (happy path + edge case failure scenario)

---

## Sources

- `problems/02-03-problem-bank.md` — PB-04 problem charter, Cluster 2 analysis
- `problems/02-02-failure-modes.md` — A4 failure mode analysis
- `problems/03-01-litmus-test-scores.md` — Litmus test and cluster scoring
- `problems/03-02-autonomy-level.md` — Risk profiling and HITL guardrails
- `research/sectors/berth-marine.md` — Berth & Marine operational context
- `research/systems/baseline-systems.md` — CITOS, PORTNET, OptEVoyage profiles
- `research/flows/critical-flows.md` — Information and decision flows
