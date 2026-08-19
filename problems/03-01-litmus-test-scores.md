# 03-01: 5-Point Litmus Test & Cluster-Weighted Scoring Matrix

**Status:** Complete  
**Source:** Problem bank `problems/02-03-problem-bank.md` (16 candidates, 6 clusters)  
**Last updated:** 2026-08-19

---

## Stage 1: Individual Problem 5-Point Litmus Filter

**Method:** Each candidate scored PASS/FAIL against 5 mandatory criteria.  
**Disqualification Rule:** Single FAIL eliminates standalone consideration.  
**Scoring Rationale:** Grounded in problem statement, failure mode analysis (02-02), and candidate action space (02-03).

---

### Filter Results

| ID | Problem | L1 Reasoning | L2 Multi-Tool | L3 Multi-Step | L4 Uncertainty | L5 ROI | Result |
|----|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| PB-01 | Cascading Berth Delay & Tidal Window Lockout | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-02 | DTQC Breakdown & Cascading Terminal Disruption | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-03 | Late DG Declaration & IMDG Compliance Hold | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-04 | Transhipment Missed-Connection Recovery | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-05 | Reefer Cold-Chain Telemetry Excursion | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-06 | Yard Block Buffer Overflow from Delayed Vessel | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-07 | 5G Network Outage Degrading AGV Fleet | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-08 | eDO/VGM Discrepancy Gate Queue Cascade | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-09 | External Disruption to Haulier Pools | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-10 | Sea-to-Air Flight Cut-Off Threat | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-11 | Cross-Border Customs Inspection Hold | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-12 | Multi-Party ITT Coordination Failure | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-13 | Multiship QC Scheduling Conflict | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-14 | iWX Container Reuse Marketplace Failure | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-15 | QC-to-aRMG Synchronisation Failure | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-16 | System-Wide Empty Container Imbalance | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |

**Result:** 16/16 PASS. No disqualifications. All 16 candidates advance to Stage 2.

---

### Detailed Rationale Per Criterion

#### L1: Non-Deterministic Reasoning

All 16 problems require reasoning that goes beyond rule engines or SQL queries:

| Problem | Why L1 Passes |
|---------|---------------|
| PB-01 | Trade-off reasoning across vessel priority, tidal windows, QC capacity, and feeder connections — optimal solution depends on real-time context |
| PB-02 | Reasoning over which adjacent berths can spare QCs without disrupting their own vessels — contextual judgment under time pressure |
| PB-03 | Multi-constraint optimisation (IMDG segregation + vessel stability + crane access) — combinatorial complexity exceeds rule engines |
| PB-04 | Multi-objective reasoning: minimise total cost across demurrage, feeder delays, SLA, and yard congestion — requires qualitative judgment |
| PB-05 | Diagnostic reasoning (power fault vs. compressor vs. seal breach) from sensor patterns — not deterministic without cross-referencing data |
| PB-06 | Dynamic overflow routing balancing re-handle cost, AGV travel time, and loading sequence — predictive reasoning over downstream impact |
| PB-07 | Graceful degradation planning that preserves maximum throughput — requires adaptive reasoning across multiple affected systems |
| PB-08 | Predictive eDO availability check before haulier departs — reasoning over uncertain timing across shipping line schedules |
| PB-09 | Predicting delay propagation from expressway to gate to yard — requires real-time GPS analysis and slot rebalancing judgment |
| PB-10 | Commercial judgment (rebooking cost vs. customer SLA value) — not optimisable by pure math solver |
| PB-11 | Partial release reasoning (which containers proceed while others are inspected) — requires document completeness assessment |
| PB-12 | Real-time split optimisation across road and sea modes — requires reasoning over both transport constraints simultaneously |
| PB-13 | Multiship QC scheduling is NP-hard — requires heuristic search over combinatorial solution space with safety constraints |
| PB-14 | Routing decision under prediction uncertainty (wait vs. reroute vs. skip) — requires probabilistic reasoning |
| PB-15 | Real-time synchronisation across three independent systems — requires dynamic coupling reasoning |
| PB-16 | System-wide supply/demand optimisation across depots — requires cross-depot visibility and truck routing constraints |

#### L2: Multi-Tool Orchestration (≥3 systems)

| Problem | Systems Required | Count |
|---------|-----------------|-------|
| PB-01 | VTIS, OptEVoyage, CITOS, PORTNET, FMS | 5 |
| PB-02 | ROCC, CITOS, FMS, PORTNET | 4 |
| PB-03 | PORTNET, CITOS, MPA DGPE | 3 |
| PB-04 | CITOS, PORTNET, OptEVoyage, Yard Ops | 4 |
| PB-05 | ARMS, CITOS, Shipping Line, Maintenance | 4 |
| PB-06 | CITOS, FMS, Gate, aRMG | 4 |
| PB-07 | 5G, FMS, CITOS, DTQC Ops | 4 |
| PB-08 | AGS, PORTNET, Weighbridge, OptETruck | 4 |
| PB-09 | OptETruck, SmartBooking, PORTNET, CITOS | 4 |
| PB-10 | OptEModal, CITOS, TradeNet, SATS, Airline | 5 |
| PB-11 | TradeNet, CALISTA, OptEModal | 3 |
| PB-12 | CITOS×2, OptETruck, Feeder, PORTNET | 5 |
| PB-13 | CITOS, FMS, ROCC, PORTNET | 4 |
| PB-14 | iWX, CITOS, PORTNET, OptETruck, iBOX | 5 |
| PB-15 | CITOS, FMS, ROCC, aRMG | 4 |
| PB-16 | iWX, OptETruck, iBOX, CITOS, PORTNET | 5 |

All problems require ≥3 systems. Average: 4.2 systems per problem.

#### L3: Multi-Step Dynamic Plan

Every problem follows the Ingest → Diagnose → Formulate → Execute → Evaluate loop. No single-turn prompt-response. Example trace for PB-04:

```
1. INGEST: OptEVoyage ETA slip notification received
2. DIAGNOSE: Mother vessel delayed 10 hrs, 3 feeders at risk
3. FORMULATE: Compute recoverable containers per feeder (discharge rate × time)
4. EXECUTE A: Query feeder flexibility (PORTNET)
5. EVALUATE: Feeder 1 can hold 2 hrs, Feeder 2 cannot hold
6. EXECUTE B: Simulate hold vs. roll cost (CITOS + yard)
7. EVALUATE: Hold Feeder 1 saves $12K vs. rolling 40 containers
8. EXECUTE C: Draft approval gate for duty manager
9. HUMAN GATE: Duty manager approves hold decision
10. EXECUTE D: Update yard plan (CITOS) + notify shipping line (PORTNET)
```

#### L4: Uncertainty & Latency

| Problem | Key Uncertainty |
|---------|----------------|
| PB-01 | Vessel ETA updates every 15 min — may slip further after rebalancing |
| PB-02 | Maintenance repair time is unpredictable — not communicated to planning systems |
| PB-03 | MPA re-approval turnaround 1–4 hrs — depends on officer availability |
| PB-04 | Feeder operator responsiveness — downstream port impact unknown |
| PB-05 | Technician response time 15–30 min — spare parts availability uncertain |
| PB-06 | Gate arrivals cannot be instantly cancelled — bookings made hours/days in advance |
| PB-07 | 5G restoration time unknown — Singtel provides ETA but may slip |
| PB-08 | eDO release timing uncoordinated — shipping lines release on own schedule |
| PB-09 | Driver re-routing decisions are autonomous — cannot force trucks to take alternate routes |
| PB-10 | Customs pre-clearance document readiness — forwarder may not have documents |
| PB-11 | Cross-time-zone document retrieval — shipper in Mumbai 2.5 hrs behind |
| PB-12 | Feeder berth conflicts — departure time may shift |
| PB-13 | Real-time vessel priority changes — new disruptions during re-optimisation |
| PB-14 | Container availability prediction has 15–30 min uncertainty window |
| PB-15 | QC rate changes are sudden and unpredictable |
| PB-16 | Future demand patterns uncertain — shipping line preferences change |

#### L5: Quantifiable ROI & Impact

| Problem | Primary Cost Metric | Estimated Per-Incident Cost |
|---------|--------------------|-----------------------------|
| PB-01 | Demurrage + QC idle + missed feeders | $58,600–$131,600 |
| PB-02 | QC downtime + vessel delay + AGV idle | $16,000–$24,000 |
| PB-03 | Emergency re-stowage + delay + penalty risk | $7,650–$23,250 |
| PB-04 | Feeder demurrage + rolled containers + SLA | $6,500–$36,500 |
| PB-05 | Cargo spoilage + emergency maintenance | $505,700–$517,500 |
| PB-06 | Re-handles + AGV efficiency + berthing | $12,900–$20,500 |
| PB-07 | QC productivity + vessel delay + fleet loss | $21,100–$65,100 |
| PB-08 | Gate delay + TRT extension + spillover | $1,050–$2,000 |
| PB-09 | Haulier idle + vessel delay + re-sequencing | $15,500–$20,000 |
| PB-10 | Flight rebooking + SLA + priority premiums | $18,000–$73,000 |
| PB-11 | Flight delay + cargo hold + customer impact | $3,700–$59,500 |
| PB-12 | Vessel delay + ITT cost + re-handles | $15,600–$29,000 |
| PB-13 | QC idle + vessel delay + yard cascade | $20,000–$55,000 |
| PB-14 | Wasted trips + idle time + missed bookings | $200–$800 |
| PB-15 | AGV queue + aRMG idle + transfer blockage | $3,000–$8,000 |
| PB-16 | Repositioning + empty trips + carbon | $50K–$150K/month |

---

## Stage 2: Root-Cause Cluster Evaluation Matrix

**Method:** Each of 6 clusters scored 1–5 across 4 weighted dimensions.  
**Weights:** Agentic AI Sweet Spot (30%), Cluster Multiplier (25%), Demo Drama (25%), Feasibility (20%).

---

### Cluster 1: Stale Data & Async State Updates

**Problems:** PB-01, PB-04, PB-06, PB-08, PB-10, PB-14 (6 problems)

| Dimension | Score | Weight | Weighted | Justification |
|-----------|:-----:|:------:|:--------:|---------------|
| Agentic AI Sweet Spot | 4 | 0.30 | 1.20 | Reconciling conflicting state across async systems is a strong LLM use case — semantic understanding of which state is "correct" when sources disagree. However, some resolution paths are deterministic (e.g., "if ETA slipped >6 hrs, re-run berth optimisation"). |
| Cluster Multiplier | 4 | 0.25 | 1.00 | 6 problems, ~$250K–$500K annual addressable. Covers all 4 sectors. High coverage but some problems (PB-14) have low per-incident cost. |
| Demo Drama | 4 | 0.25 | 1.00 | Watching an agent propagate a state change across 5 systems and prevent downstream failure is compelling. The "before/after" comparison (stale data cascade vs. agent-driven synchronisation) is clear. |
| Feasibility | 3 | 0.20 | 0.60 | Mocking real-time event buses across 5 systems is technically complex. Requires simulating async state drift convincingly. Moderate hackathon feasibility. |
| **TOTAL** | | | **3.80** | |

---

### Cluster 2: Manual Multi-Party Coordination

**Problems:** PB-01, PB-02, PB-03, PB-04, PB-05, PB-09, PB-10, PB-11, PB-12 (9 problems)

| Dimension | Score | Weight | Weighted | Justification |
|-----------|:-----:|:------:|:--------:|---------------|
| Agentic AI Sweet Spot | 5 | 0.30 | 1.50 | Multi-party exception resolution is the strongest agentic AI use case in this bank. Requires: natural language understanding (phone/WhatsApp messages), multi-step reasoning (diagnose → coordinate → resolve), and structured workflow generation from unstructured inputs. Cannot be solved by rule engines or optimisers. |
| Cluster Multiplier | 5 | 0.25 | 1.25 | 9 of 16 problems (56%). ~$350K–$750K annual addressable. Largest coverage. PB-01 alone is $58K–$132K per incident. |
| Demo Drama | 5 | 0.25 | 1.25 | Highest drama potential. Demo shows: (1) agent receives disruption alert, (2) reasons over which parties to notify, (3) drafts recovery plan, (4) sends structured notifications, (5) collects approvals, (6) executes — all while a "phone call" counter shows calls eliminated. The human operator watches the agent coordinate 4–6 parties in 2 minutes vs. 2–6 hours manually. |
| Feasibility | 4 | 0.20 | 0.80 | Mock APIs are straightforward: notification service, approval workflow, schedule query, cargo lookup. Most tools are CRUD + notification patterns. Good hackathon feasibility. |
| **TOTAL** | | | **4.80** | |

---

### Cluster 3: Equipment & Infrastructure Dependency

**Problems:** PB-02, PB-07, PB-15 (3 problems)

| Dimension | Score | Weight | Weighted | Justification |
|-----------|:-----:|:------:|:--------:|---------------|
| Agentic AI Sweet Spot | 2 | 0.30 | 0.60 | Equipment failure response is largely deterministic: detect failure → reroute AGVs → notify QC → wait for repair. The reasoning is mostly rule-based ("if QC offline, redistribute to adjacent berths"). LLM adds limited value over traditional rule engines. |
| Cluster Multiplier | 2 | 0.25 | 0.50 | 3 problems, ~$100K–$200K annual. Smallest cluster. Limited scaling potential. |
| Demo Drama | 3 | 0.25 | 0.75 | Equipment failure scenarios are dramatic but predictable. Demo would show agent managing AGV rerouting — visually interesting but not novel. |
| Feasibility | 3 | 0.20 | 0.60 | Mocking physical sensor data (5G latency, QC motor failure) is moderately complex. Requires simulating hardware telemetry. |
| **TOTAL** | | | **2.45** | |

---

### Cluster 4: DG & Regulatory Compliance Workflow

**Problems:** PB-03, PB-11 (2 problems)

| Dimension | Score | Weight | Weighted | Justification |
|-----------|:-----:|:------:|:--------:|---------------|
| Agentic AI Sweet Spot | 4 | 0.30 | 1.20 | Regulatory interpretation and document reasoning are strong NLU use cases. IMDG Code segregation rules require semantic understanding. Cross-time-zone document coordination requires multi-step agent reasoning. |
| Cluster Multiplier | 2 | 0.25 | 0.50 | 2 problems, ~$50K–$150K annual. Smallest addressable coverage. |
| Demo Drama | 4 | 0.25 | 1.00 | Agent coordinating document retrieval across time zones while racing against a flight deadline is compelling. The "agent in Mumbai, agent in Singapore" narrative is strong. |
| Feasibility | 3 | 0.20 | 0.60 | Mocking TradeNet and MPA DGPE APIs is moderately complex. Regulatory compliance workflows require careful mock data design. |
| **TOTAL** | | | **3.30** | |

---

### Cluster 5: Cross-Terminal Visibility Gap

**Problems:** PB-12, PB-16 (2 problems)

| Dimension | Score | Weight | Weighted | Justification |
|-----------|:-----:|:------:|:--------:|---------------|
| Agentic AI Sweet Spot | 3 | 0.30 | 0.90 | Cross-terminal data aggregation is more of a data engineering problem than an agentic AI problem. The reasoning (optimise ITT split, balance empty containers) is largely mathematical — a linear programming solver could handle most of it. |
| Cluster Multiplier | 2 | 0.25 | 0.50 | 2 problems, ~$60K–$140K annual. Limited coverage. |
| Demo Drama | 3 | 0.25 | 0.75 | Dashboard visibility across terminals is useful but not visually dramatic. The agent's value is in data aggregation, not dynamic reasoning. |
| Feasibility | 3 | 0.20 | 0.60 | Mocking two separate CITOS instances with delayed synchronisation is moderately complex. |
| **TOTAL** | | | **2.75** | |

---

### Cluster 6: QC-to-Yard Flow Synchronisation

**Problems:** PB-06, PB-13, PB-15 (3 problems)

| Dimension | Score | Weight | Weighted | Justification |
|-----------|:-----:|:------:|:--------:|---------------|
| Agentic AI Sweet Spot | 3 | 0.30 | 0.90 | QC-AGV-aRMG synchronisation involves real-time rate matching — more of a control systems problem than an agentic AI problem. The reasoning is largely mathematical (rate matching, queue balancing). Agent adds value in edge cases but core logic is deterministic. |
| Cluster Multiplier | 3 | 0.25 | 0.75 | 3 problems, ~$35K–$83K annual. Moderate coverage. |
| Demo Drama | 3 | 0.25 | 0.75 | Visual showing AGV flow balancing across yard blocks is interesting. But the core problem (rate matching) is not dramatic. |
| Feasibility | 3 | 0.20 | 0.60 | Mocking QC sensors, AGV positions, and aRMG job queues is moderately complex. Requires simulating real-time telemetry. |
| **TOTAL** | | | **3.00** | |

---

### Cluster Ranking Summary

| Rank | Cluster | Problems | Addressable Annual | Weighted Score |
|:----:|---------|:--------:|:------------------:|:--------------:|
| **1** | **Cluster 2: Manual Multi-Party Coordination** | **9** | **$350K–$750K** | **4.80** |
| 2 | Cluster 1: Stale Data & Async State Updates | 6 | $250K–$500K | 3.80 |
| 3 | Cluster 4: DG & Regulatory Compliance | 2 | $50K–$150K | 3.30 |
| 4 | Cluster 6: QC-to-Yard Flow Sync | 3 | $35K–$83K | 3.00 |
| 5 | Cluster 5: Cross-Terminal Visibility | 2 | $60K–$140K | 2.75 |
| 6 | Cluster 3: Equipment & Infrastructure | 3 | $100K–$200K | 2.45 |

---

## Stage 3: Solution Capability Check, Selection of Winning Cluster & Flagship Anchor

### Winning Cluster: Cluster 2 — Manual Multi-Party Coordination

**Why Cluster 2 Wins:**

1. **Highest Agentic AI Sweet Spot (5/5):** Multi-party exception resolution is the canonical use case for agentic AI — it requires understanding unstructured inputs, reasoning over conflicting objectives, and coordinating structured workflows across multiple independent parties. No rule engine or optimiser can replicate this.

2. **Largest Cluster Multiplier (9/16 problems, 56%):** A single agent architecture addressing this root cause would resolve the majority of the problem bank. This is the strongest platform generalisation story for the competition.

3. **Highest Demo Drama (5/5):** The "before vs. after" comparison is stark: current state = phone calls, WhatsApp, 2–6 hours; agent state = automated coordination, 2–6 minutes. The execution trace shows the agent reasoning, drafting plans, sending notifications, collecting approvals, and executing — all visible in a 10-minute video.

4. **Strong Feasibility (4/5):** Mock APIs for notification, approval workflow, schedule query, and cargo lookup are straightforward CRUD + messaging patterns. Within hackathon reach.

---

### Mandatory 4-Point Solution Capability Check (Top Candidates)

| Check | PB-01 | PB-04 | PB-02 | PB-10 |
|-------|:-----:|:-----:|:-----:|:-----:|
| **Event Trigger** | AIS ETA slip webhook | AIS ETA slip + PORTNET feeder schedule | DTQC sensor alarm via ROCC | OptEModal vessel delay detection |
| **Execution Trace** | 10-step trace (see L3 rationale above) | 10-step trace (see L3 rationale above) | 8-step trace from alarm to resolution | 8-step trace from risk alert to rebooking |
| **HITL Gate** | Berth reassignment requires duty manager approval | Hold vs. roll decision requires duty manager + shipping line approval | QC redistribution requires berth planner approval | Flight rebooking requires cargo owner approval |
| **Failure Recovery** | Handles ETA further slip during recovery plan | Handles feeder operator rejection of hold request | Handles repair time extension (longer than estimated) | Handles flight unavailability (no alternative flights) |

All 4 top candidates pass the Solution Capability Check.

---

### Flagship Anchor Selection: PB-04 — Transhipment Missed-Connection Recovery

**Selected over PB-01 because:**

| Factor | PB-04 Advantage | PB-01 Disadvantage |
|--------|----------------|-------------------|
| Demo narrative clarity | Simple story: "100 containers will miss their flight — agent saves them" | Complex story: "vessel delay + tidal window + feeder cascade — agent resolves" |
| HITL gate drama | Hold vs. roll decision has clear financial trade-off ($1,600 hold vs. $12K roll) | Berth reassignment is less visually dramatic |
| Multi-party visibility | 4 distinct parties (duty manager, ship planner, shipping line, feeder operator) — each with clear role | 5+ parties but roles overlap (duty manager, harbour pilot, shipping line, ship planner) |
| Cluster membership | Member of Cluster 2 (Manual Multi-Party Coordination) | Also member of Cluster 1 (Stale Data) — dilutes cluster story |
| Quantified impact | $6,500–$36,500 per incident, 3–5/month = $234K–$2.19M annual | Higher per-incident ($58K–$132K) but lower frequency (2–3/month) |
| Tool orchestration | 4 clean tools (get connections, calculate rate, query flexibility, simulate) | 5 tools but some overlap (get berth schedule + query vessel ETA are similar) |

**PB-04 delivers the strongest demo narrative:** The agent receives an alert that a mother vessel is 10 hours late, reasons over which of 3 feeder connections are still achievable, drafts a hold vs. roll recommendation, presents it to the duty manager for approval, and executes the decision — all in under 3 minutes. The "before" state is 3–6 hours of phone calls.

---

## Acceptance Criteria Verification

- [x] All 16 candidate problems scored in Stage 1 (16/16 PASS)
- [x] All 6 Root-Cause Clusters scored in Stage 2 with explicit justifications
- [x] Exactly ONE Winning Cluster identified (Cluster 2: Manual Multi-Party Coordination)
- [x] Exactly ONE Flagship Anchor Problem selected (PB-04: Transhipment Missed-Connection Recovery)
- [x] 4-Point Solution Capability Check completed for top candidates

---

## Sources

- `problems/02-03-problem-bank.md` — 16 candidate problems, 6 root-cause clusters
- `problems/02-02-failure-modes.md` — 7-dimension failure mode analysis per scenario
- `research/sectors/berth-marine.md` — Berth & Marine operational context
- `research/sectors/container-yard-transport.md` — Container Yard operational context
- `research/sectors/gate-haulage.md` — Gate & Haulage operational context
- `research/sectors/multimodal-logistics.md` — Multimodal Logistics operational context
- `research/systems/baseline-systems.md` — 7 baseline system profiles
- `research/flows/critical-flows.md` — Physical, Information, Decision flows
