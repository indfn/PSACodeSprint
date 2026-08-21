# 03-01: Discriminative Litmus Test & Cluster-Weighted Scoring Matrix

**Status:** Complete  
**Source:** `problems/02-03-problem-bank.md` (16 candidates, 6 clusters)  
**Last updated:** 2026-08-19

---

## Stage 1: Individual 5-Point Litmus Filter

### Scoring Criteria

| # | Criterion | Pass Condition | Strict Fail Condition |
|---|---|---|---|
| **L1** | Non-Deterministic Reasoning | Unstructured communications, fuzzy trade-offs, dynamic multi-party negotiation | Solvable by standard SQL, deterministic `if/else` rules, or pure MILP/math solvers |
| **L2** | Multi-Tool Calling (≥3 Systems) | Dynamically queries/mutates ≥3 distinct PSA platforms | Operates within 1–2 isolated databases |
| **L3** | Multi-Step Dynamic Loop | Ingest → Diagnose → Simulate → Coordinate → Verify → Execute | Single-turn prompt-response or single API call |
| **L4** | Uncertainty & Latency | Noisy telemetry, unconfirmed replies, delayed manifest data | All inputs 100% complete, synchronous, static |
| **L5** | Significant Macro ROI | ≥$5,000 per incident in demurrage, crane idling, re-handles, or SLA penalties | < $1,000/incident with negligible macro impact |

### Results

---

#### PB-01: Cascading Berth Delay & Tidal Window Lockout

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | Requires reconciling conflicting objectives: vessel priority vs. QC capacity vs. feeder reliability vs. tidal windows. OptEVoyage ETA updates are fuzzy (AIS-derived,±2 hrs); tidal windows are physical constraints; feeder hold vs. roll is a multi-party trade-off. No single formula produces the optimal answer — depends on real-time context. |
| **L2** | **PASS** | VTIS/STRAITREP (vessel traffic), OptEVoyage (JIT tracking), CITOS (berth allocation), PORTNET (feeder schedules) — 4 distinct PSA platforms. |
| **L3** | **PASS** | 8-step resolution workflow: receive ETA slip → assess berth alternatives → negotiate crane redeployment → confirm tidal window → contact shipping line → recalculate crane split → adjust yard plan → coordinate feeders. |
| **L4** | **PASS** | OptEVoyage ETAs shift ±2 hrs; tidal windows are physically non-delayable; harbour pilot availability uncertain; feeder operator responsiveness variable. |
| **L5** | **PASS** | $58,600–$131,600 per incident (vessel demurrage + QC idle + missed feeders + anchorage). 2–3 incidents/month during monsoon. |

**Result: PASS (5/5)**

---

#### PB-02: DTQC Breakdown & Cascading Terminal Disruption

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | Requires reasoning over which adjacent berths can spare QCs without disrupting their own vessels — a context-dependent judgment. Emergency re-sequencing must account for vessel stability constraints (physical document/PDF) that CITOS cannot compute. Repair time is unpredictable and affects all downstream planning. |
| **L2** | **PASS** | ROCC (crane ops), CITOS (QC scheduling), A*STAR FMS (AGV dispatch), PORTNET (vessel schedule) — 4 systems. |
| **L3** | **PASS** | Containment → AGV rerouting → QC reassignment → vessel re-sequencing → shipping line notification → recovery monitoring. |
| **L4** | **PASS** | Maintenance repair time is unpredictable (30 min–8 hrs). QC status transitions are sudden. AGV queue builds in real-time during containment. |
| **L5** | **PASS** | $16,000–$24,000 per incident (QC downtime + vessel delay + AGV idle + cascade). 4–6 incidents/month across terminals. |

**Result: PASS (5/5)**

---

#### PB-03: Late DG Declaration & IMDG Compliance Hold

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **FAIL** | IMDG segregation rules are deterministic — defined by class, UN number, and vessel-specific segregation table. Re-stowage under IMDG + stability constraints is a constraint satisfaction problem solvable by MILP. The ship planner's manual work is time-consuming but not cognitively ambiguous: identify compliant positions → check stability → select optimal. A rule engine with the IMDG table and vessel stability model can solve this. |
| **L2** | **PASS** | PORTNET (EDI DG declaration), CITOS (stowage planning), MPA DGPE (regulatory) — 3 systems. |
| **L3** | **PASS** | Multi-step: receive DG amendment → review IMDG tables → identify compliant positions → stability check → update stowage → MPA re-approval → yard adjustment. |
| **L4** | **PASS** | MPA re-approval turnaround is uncertain (1–4 hrs). DG amendment timing is unpredictable (up to 12 hrs before arrival). |
| **L5** | **PASS** | $7,650–$23,250 per incident + regulatory penalty risk (up to $100,000). 1–2 incidents/month. |

**Result: FAIL on L1** — Deterministic constraint satisfaction. Rule engine with IMDG table + stability model can resolve without LLM reasoning.

---

#### PB-04: Transhipment Missed-Connection Recovery (100+ Containers)

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | Multi-objective trade-off: minimise total cost across vessel demurrage, feeder delays, customer SLA, and yard congestion. Requires reasoning over customer relationships and shipping line negotiations — qualitative judgment that cannot be captured in an objective function. Dynamic replanning as new ETA information arrives. |
| **L2** | **PASS** | CITOS (berth + ship planning), PORTNET (feeder schedules), OptEVoyage (JIT tracking), yard operations (transhipment clustering) — 4 systems. |
| **L3** | **PASS** | Delay notification → compute recoverable containers → assess feeder flexibility → simulate hold vs. roll → negotiate with shipping line → update CITOS → re-sequence yard. |
| **L4** | **PASS** | Feeder flexibility is unknown until assessed. Downstream port tidal windows constrain feeder hold decisions. Customer SLA terms vary per shipment. |
| **L5** | **PASS** | $6,500–$36,500 per incident (feeder demurrage + rolled containers + SLA penalties + QC re-prioritisation). 3–5 incidents/month. |

**Result: PASS (5/5)**

---

#### PB-05: Reefer Cold-Chain Telemetry Excursion (Pharma Cargo)

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **FAIL** | Diagnosis follows deterministic fault trees: temperature pattern + power status + compressor telemetry → root cause. Each cause (power fault, compressor failure, seal breach) maps to a specific response. Priority escalation based on cargo value is a simple if/then rule. M&R dispatch is nearest-available routing — a classical optimisation problem. No fuzzy reasoning required. |
| **L2** | **FAIL** | ARMS (reefer monitoring) + CITOS (yard assignment) + maintenance crew (dispatch). Maintenance is a phone-based service, not a software platform. Only 2 distinct PSA software systems are dynamically queried. |
| **L3** | **PASS** | Alarm → diagnose root cause → prioritise by cargo value → dispatch technician → notify shipping line → log excursion. |
| **L4** | **PASS** | Spoilage window is time-critical (2–4 hrs). Technician availability is uncertain. Root cause is ambiguous until technician arrives. |
| **L5** | **PASS** | $505,700–$517,500 per incident for pharma total loss scenario. 5–8 incidents/month (all reefer types). |

**Result: FAIL on L1 and L2** — Deterministic fault tree diagnosis; insufficient distinct PSA software platforms.

---

#### PB-06: Yard Block Buffer Overflow from Delayed Vessel

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | Dynamic overflow routing requires real-time capacity assessment across multiple yard blocks. Re-handle vs. loading trade-off requires predicting downstream impact on vessel loading sequence — a temporal reasoning problem. Anticipatory action (slowing gate arrivals before overflow) requires prediction, not reaction. |
| **L2** | **PASS** | CITOS (yard planning), A*STAR FMS (AGV dispatch), gate operations, aRMG controllers — 4 systems. |
| **L3** | **PASS** | Detect overflow risk → assess alternative blocks → verify constraints → schedule re-handles → adjust gate rate → update ship planner. |
| **L4** | **PASS** | Vessel delay duration uncertain. Gate arrival rate fluctuates. Alternative block availability changes in real-time. |
| **L5** | **PASS** | $12,900–$20,500 per incident (re-handles + AGV efficiency loss + extended berthing). 6–10 incidents/month during peak. |

**Result: PASS (5/5)**

---

#### PB-07: 5G Network Outage Degrading AGV Fleet

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | While 5G→4G fallback is a network event, the operational response requires: predicting which AGVs are at risk of stranding based on battery level and position, deciding which QCs to slow first based on vessel priority, and coordinating graceful degradation that preserves maximum throughput. These are operational judgment calls, not network failover logic. |
| **L2** | **PASS** | 5G network (Singtel), A*STAR FMS (AGV fleet), CITOS (QC scheduling), DTQC operations — 4 systems. |
| **L3** | **PASS** | Detect latency spike → activate de-rating → predict stranded AGVs → adjust fleet parameters → notify QC operators → coordinate with Singtel → monitor restoration. |
| **L4** | **PASS** | 5G restoration time uncertain (1–4 hrs). Battery depletion rates vary. AGV positions change during outage. |
| **L5** | **PASS** | $21,100–$65,100 per incident (QC productivity + vessel delay + AGV fleet loss + restoration). 1–2 incidents/month. |

**Result: PASS (5/5)**

---

#### PB-08: eDO/VGM Discrepancy Gate Queue Cascade

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | Predictive check before haulier departs depot requires reasoning over eDO release probability and VGM amendment feasibility — uncertain outcomes. Real-time queue management requires dynamic overflow lane activation and slot rebalancing. Multi-party coordination (shipping line, haulier, consignee) under time pressure involves unstructured phone/email communication. |
| **L2** | **PASS** | AGS/OCR (gate processing), PORTNET (eDO status), weighbridge (VGM), OptETruck (slot management) — 4 systems. |
| **L3** | **PASS** | Pre-departure check → detect queue build → contact shipping line → resolve eDO → verify VGM → open overflow → rebalance slots → clear queue. |
| **L4** | **PASS** | eDO release timing is shipping-line-dependent and unpredictable. VGM amendment window is time-constrained (>4 hrs before ETB). Queue build-up rate varies with peak arrival patterns. |
| **L5** | **PASS** | $1,050–$2,000 per incident × 8–12 incidents/month = ~$8,400–$24,000/month. Per-incident below $5,000 threshold but aggregate is significant. |

**Result: PASS (5/5)**

---

#### PB-09: External Disruption to Haulier Pools (Expressway Blockage)

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | Real-time GPS data analysis to predict which hauliers will miss slots requires dynamic reasoning. Slot rebalancing across OptETruck and SmartBooking involves multi-party coordination with hauliers who make independent routing decisions. Yard planner notification must anticipate cascade to vessel loading — temporal prediction. |
| **L2** | **PASS** | OptETruck (TMS), SmartBooking (slot management), PORTNET (gate schedule), CITOS (yard planning) — 4 systems. |
| **L3** | **PASS** | Detect delay → predict slot misses → rebalance slots → notify yard planner → adjust vessel loading → monitor recovery. |
| **L4** | **PASS** | Haulier routing decisions are autonomous (OptETruck cannot force routes). Traffic conditions evolve. Slot availability changes in real-time. |
| **L5** | **PASS** | $15,500–$20,000 per incident (haulier idle + vessel delay + re-sequencing + carbon). 2–4 incidents/month. |

**Result: PASS (5/5)**

---

#### PB-10: Sea-to-Air Flight Cut-Off Threat (OptEModal)

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | Multi-system orchestration with no single system having authority. Commercial judgment required: rebooking cost vs. customer SLA value. Document pre-clearance coordination with forwarders across time zones. Temporal reasoning over 12-hour window with fixed deadlines. |
| **L2** | **PASS** | OptEModal (sea-air platform), CITOS (terminal ops), CALISTA (milestone tracking), TradeNet (customs), SATS/dnata (ground handling) — 5 systems. |
| **L3** | **PASS** | Detect delay → list affected containers → request priority discharge → pre-lodge customs → check flight availability → estimate feasibility → rebook if necessary. |
| **L4** | **PASS** | Vessel ETA may continue slipping. Customs broker document readiness uncertain. SATS slot availability variable. Flight rebooking depends on airline capacity. |
| **L5** | **PASS** | $18,000–$73,000 per incident (flight rebooking + SLA + priority premiums + carbon). 1–2 incidents/month. |

**Result: PASS (5/5)**

---

#### PB-11: Cross-Border Customs Inspection Hold (Sea-Air)

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | Partial release reasoning: which containers can proceed while others are inspected — requires judgment about shipment dependencies. Cross-time-zone document retrieval involves coordination with parties in different time zones. Inspection prioritisation based on flight schedule urgency requires temporal reasoning. |
| **L2** | **PASS** | TradeNet (customs), CALISTA (milestone tracking), OptEModal (transfer coordination) — 3 systems. |
| **L3** | **PASS** | Detect hold → assess inspection requirements → retrieve documents cross-time-zone → request partial release → prioritise inspection → coordinate cargo release. |
| **L4** | **PASS** | Inspector availability uncertain. Document retrieval across time zones involves latency (shipper in Mumbai, 2.5 hrs behind). Inspection completion time variable. |
| **L5** | **PASS** | $3,700–$59,500 per incident (flight delay + cargo hold + customer impact + inspection fee). 2–4 incidents/month. |

**Result: PASS (5/5)**

---

#### PB-12: Multi-Party ITT Coordination Failure (Cross-Terminal)

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | Real-time split optimisation across road and sea modes requires reasoning over cost, time, and capacity simultaneously. Cross-terminal visibility gap (PPT and Tuas CITOS are separate instances) creates genuine information asymmetry. Dynamic re-routing when one mode is delayed requires multi-constraint judgment. |
| **L2** | **PASS** | CITOS (PPT), CITOS (Tuas) — separate instances, OptETruck (road ITT), feeder vessels (sea ITT), PORTNET (inventory tracking) — 5 systems. |
| **L3** | **PASS** | Identify candidates → assess road capacity → assess sea capacity → optimise split → dispatch → monitor arrivals → update Tuas loading sequence. |
| **L4** | **PASS** | PPT container availability not visible to Tuas in real-time (PORTNET delayed 30–60 min). Feeder berth availability uncertain. Road ITT affected by traffic. |
| **L5** | **PASS** | $15,600–$29,000 per incident (vessel delay + road ITT + sea ITT + re-handles). 4–6 incidents/month. |

**Result: PASS (5/5)**

---

#### PB-13: Multiship QC Scheduling Conflict Under Disruption

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | Multiship QC scheduling is NP-hard — requires heuristic search over combinatorial solution space. Reasoning over conflicting multi-vessel objectives with safety constraints and yard congestion prediction. Real-time re-optimisation as new information arrives (vessel updates, QC status changes). |
| **L2** | **PASS** | CITOS (QC scheduling + berth allocation), A*STAR FMS (AGV dispatch), ROCC (crane operations), PORTNET (vessel schedules) — 4 systems. |
| **L3** | **PASS** | Detect QC conflict → assess vessel priorities → predict yard congestion → run heuristic re-allocation → negotiate QC sharing → update CITOS → notify parties. |
| **L4** | **PASS** | Multiple vessels updating simultaneously. QC maintenance status changes. Yard block capacity fluctuates. |
| **L5** | **PASS** | $20,000–$55,000 per incident (QC idle + vessel delay + yard cascade). 3–5 incidents/month. |

**Result: PASS (5/5)**

---

#### PB-14: iWX Container Reuse Marketplace Coordination Failure

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | Real-time container availability verification requires cross-referencing iWX prediction, CITOS gate status, and shipping line approval — three asynchronous data sources. Routing decision must account for prediction uncertainty (wait vs. reroute vs. skip). Learning from prediction errors requires adaptive reasoning. |
| **L2** | **PASS** | iWX (reuse marketplace), CITOS (gate data), PORTNET (shipping line approvals), OptETruck (haulier routing), iBOX (depot management) — 5 systems. |
| **L3** | **PASS** | Get candidates → verify availability → check approval → route haulier → handle failure → reroute or skip. |
| **L4** | **PASS** | iWX predictions have 15–30 min uncertainty window. Shipping line approval timing is asynchronous. Container availability changes between prediction and dispatch. |
| **L5** | **FAIL** | $200–$800 per failed reuse match. 15–25 incidents/month = $3,000–$20,000/month. Per-incident cost is micro-ROI (<$1,000). Aggregate monthly impact is moderate but does not meet the ≥$5,000 per-incident threshold for macro significance. |

**Result: FAIL on L5** — Micro-ROI per incident ($200–$800). Insufficient macro impact per occurrence.

---

#### PB-15: QC-to-aRMG Synchronisation Failure

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **PASS** | Dynamic load balancing across multiple yard blocks requires real-time flow computation. Feedback loop between yard congestion and QC productivity creates coupled dynamics. Predictive buffering (anticipate QC rate changes and pre-adjust) requires temporal reasoning. |
| **L2** | **PASS** | CITOS (QC scheduling + yard planning), A*STAR FMS (AGV dispatch), ROCC (crane operations), aRMG controllers — 4 systems. |
| **L3** | **PASS** | Get QC productivity → check AGV queue → check aRMG job queue → compute balanced flow → redirect AGVs → monitor synchronisation. |
| **L4** | **PASS** | QC rate changes are sudden (breakdown, weather). AGV arrivals are continuous and variable. aRMG job completion times are stochastic. |
| **L5** | **PASS** | $3,000–$8,000 per incident × 8–12 incidents/day = $24,000–$96,000/day during peak. Per-incident is borderline but daily aggregate is significant. |

**Result: PASS (5/5)**

---

#### PB-16: System-Wide Empty Container Imbalance

| Criterion | Verdict | Justification |
|-----------|---------|---------------|
| **L1** | **FAIL** | Core problem is depot-to-depot repositioning — a classic transportation/assignment problem solvable by MILP. Supply/demand matching across depots with truck routing constraints is a deterministic optimisation. Coordination with shipping line preferences adds some complexity but does not require LLM reasoning. |
| **L2** | **PASS** | iWX (container reuse), OptETruck (haulier routing), iBOX (depot management), CITOS (container inventory), PORTNET (import/export data) — 5 systems. |
| **L3** | **PASS** | Get depot inventory → predict demand → optimise repositioning → coordinate with shipping lines → track execution. |
| **L4** | **PASS** | Depot inventory levels change in real-time. Shipping line preferences are variable. Truck fleet availability fluctuates. |
| **L5** | **FAIL** | $50,000–$150,000/month across all depots (200–400 trips/month). Per-trip repositioning cost is $100–$200. Micro-ROI per action (<$1,000). Systemic issue, not incident-based. |

**Result: FAIL on L1 and L5** — Deterministic MILP optimisation; micro-ROI per action.

---

### Stage 1 Summary

| ID | Problem | L1 | L2 | L3 | L4 | L5 | Result |
|----|---------|----|----|----|----|----|----|
| PB-01 | Cascading Berth Delay & Tidal Window Lockout | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-02 | DTQC Breakdown & Cascading Terminal Disruption | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-03 | Late DG Declaration & IMDG Compliance Hold | ❌ | ✅ | ✅ | ✅ | ✅ | **FAIL** |
| PB-04 | Transhipment Missed-Connection Recovery | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-05 | Reefer Cold-Chain Telemetry Excursion | ❌ | ❌ | ✅ | ✅ | ✅ | **FAIL** |
| PB-06 | Yard Block Buffer Overflow | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-07 | 5G Network Outage Degrading AGV Fleet | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-08 | eDO/VGM Discrepancy Gate Queue Cascade | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-09 | External Disruption to Haulier Pools | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-10 | Sea-to-Air Flight Cut-Off Threat | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-11 | Cross-Border Customs Inspection Hold | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-12 | Multi-Party ITT Coordination Failure | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-13 | Multiship QC Scheduling Conflict | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-14 | iWX Container Reuse Marketplace Failure | ✅ | ✅ | ✅ | ✅ | ❌ | **FAIL** |
| PB-15 | QC-to-aRMG Synchronisation Failure | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| PB-16 | System-Wide Empty Container Imbalance | ❌ | ✅ | ✅ | ✅ | ❌ | **FAIL** |

**Filter Result: 12 PASS / 4 FAIL**

Eliminated candidates:
- **PB-03** (L1): Deterministic IMDG constraint satisfaction — rule engine with IMDG table + vessel stability model solves this.
- **PB-05** (L1, L2): Deterministic fault tree diagnosis + only 2 PSA software systems (ARMS, CITOS).
- **PB-14** (L5): Micro-ROI ($200–$800/incident) — insufficient macro impact per occurrence.
- **PB-16** (L1, L5): Classic MILP transportation/assignment problem; micro-ROI per repositioning action.

---

## Stage 2: Root-Cause Cluster Evaluation Matrix

### Cluster Definitions (from 02-03-problem-bank.md)

| Cluster | Root Cause | Problems (Pre-Filter) | Passing Problems |
|---------|-----------|----------------------|-----------------|
| **C1: Stale Data & Async State** | Separate state copies not synchronised | PB-01, PB-04, PB-06, PB-08, PB-10, PB-14 | PB-01, PB-04, PB-06, PB-08, PB-10 (5) |
| **C2: Manual Multi-Party Coordination** | Phone/WhatsApp/email exception workflows | PB-01, PB-02, PB-03, PB-04, PB-05, PB-09, PB-10, PB-11, PB-12 | PB-01, PB-02, PB-04, PB-09, PB-10, PB-11, PB-12 (7) |
| **C3: Equipment & Infrastructure Dependency** | Physical equipment fails without warning | PB-02, PB-07, PB-15 | PB-02, PB-07, PB-15 (3) |
| **C4: DG & Regulatory Compliance** | Manual government agency workflows | PB-03, PB-11 | PB-11 (1) |
| **C5: Cross-Terminal Visibility Gap** | PPT and Tuas as separate instances | PB-12, PB-16 | PB-12 (1) |
| **C6: QC-to-Yard Flow Synchronisation** | Rate mismatches across QC→AGV→aRMG | PB-06, PB-13, PB-15 | PB-06, PB-13, PB-15 (3) |

### Scoring Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Agentic AI Sweet Spot** | 30% | Degree of unstructured data, semantic ambiguity, and multi-party negotiation vs. simple math solvers |
| **Cluster Multiplier / Coverage** | 25% | Number of passing problems resolved and total aggregate monthly impact across PSA |
| **Demo Drama & Trace Visibility** | 25% | How visually clear and impressive the execution trace will be in a 10-minute video |
| **Feasibility & API Mockability** | 20% | Practicality of building high-fidelity mock environments within hackathon timelines |

### Cluster Scoring Matrix

| Cluster | Agentic Sweet Spot (30%) | Coverage (25%) | Demo Drama (25%) | Feasibility (20%) | Weighted Score |
|---------|--------------------------|----------------|-------------------|--------------------|----------------|
| **C2: Manual Multi-Party Coordination** | 5 | 5 | 5 | 4 | **4.80** |
| **C6: QC-to-Yard Flow Synchronisation** | 3 | 3 | 4 | 4 | **3.40** |
| **C3: Equipment & Infrastructure Dependency** | 3 | 3 | 3 | 4 | **3.15** |
| **C1: Stale Data & Async State** | 3 | 4 | 3 | 4 | **3.35** |
| **C4: DG & Regulatory Compliance** | 3 | 1 | 3 | 3 | **2.45** |
| **C5: Cross-Terminal Visibility Gap** | 2 | 1 | 3 | 3 | **2.20** |

### Cluster-by-Cluster Justification

#### C2: Manual Multi-Party Coordination — Score: 4.80

**Agentic Sweet Spot (5/5):** The root cause is unstructured multi-party communication — phone calls, WhatsApp, email. An agent that can parse unstructured notifications, reason over conflicting stakeholder interests, draft recovery proposals, and coordinate multi-party workflows directly addresses the root cause. This is the quintessential agentic use case: not solving equations, but mediating between humans with conflicting objectives.

**Coverage (5/5):** 7 passing problems — the highest of any cluster. Aggregate monthly impact: ~$316,000/month ($187K from PB-01/PB-04 + $16K from PB-02 + $35.5K from PB-09 + $91K from PB-10 + $130K from PB-11 + $107K from PB-12).

**Demo Drama (5/5):** Maximum visibility. The execution trace shows: agent receives disruption → parses email/VHF notification → queries tools across multiple systems → reasons over options → drafts recovery proposal → presents HITL card to operator → operator approves → agent executes. Each step is visible, auditable, and compelling.

**Feasibility (4/5):** Mock endpoints for PORTNET, CITOS, OptETruck, and email parsing are straightforward. The main challenge is simulating realistic multi-party response timing.

#### C6: QC-to-Yard Flow Synchronisation — Score: 3.40

**Agentic Sweet Spot (3/5):** Dynamic flow balancing across QC→AGV→aRMG is a control systems problem. An agent adds value in predicting downstream impact and coordinating responses, but the core balancing logic could partially be handled by a PID controller or classical control system.

**Coverage (3/5):** 3 passing problems. Aggregate monthly impact: ~$84K–$264K/day during peak for PB-15 alone, plus PB-06 ($77K–$123K/month) and PB-13 ($60K–$165K/month).

**Demo Drama (4/5):** Visual flow synchronisation across three systems (QC rate → AGV dispatch → aRMG jobs) with real-time balancing is compelling.

**Feasibility (4/5):** Mock QC productivity data, AGV queue status, and aRMG job queues are straightforward to simulate.

#### C3: Equipment & Infrastructure Dependency — Score: 3.15

**Agentic Sweet Spot (3/5):** Equipment failure response involves coordination and prediction, but some responses follow predictable patterns (activate de-rating, slow QCs, reroute AGVs). The agent adds value in prediction and graceful degradation, but the core response is partially rule-based.

**Coverage (3/5):** 3 passing problems. Aggregate monthly impact: ~$50K–$95K.

**Demo Drama (3/5):** Equipment failure scenarios are dramatic but the response is less visually compelling than multi-party coordination.

**Feasibility (4/5):** Mock sensor data and status endpoints are straightforward.

#### C1: Stale Data & Async State — Score: 3.35

**Agentic Sweet Spot (3/5):** Real-time state synchronisation is fundamentally an event-driven architecture problem. An agent can add value in detecting stale data and triggering updates, but the core synchronisation layer is middleware, not reasoning.

**Coverage (4/5):** 5 passing problems. High aggregate impact.

**Demo Drama (3/5):** State synchronisation is infrastructure — less visually compelling than multi-party workflows.

**Feasibility (4/5):** Mock event webhooks and state queries are straightforward.

#### C4: DG & Regulatory Compliance — Score: 2.45

**Agentic Sweet Spot (3/5):** Regulatory workflows involve manual coordination but the actual rules are deterministic (IMDG segregation, customs procedures).

**Coverage (1/5):** Only 1 passing problem (PB-11) after PB-03 was eliminated. Low cluster multiplier.

**Demo Drama (3/5):** Document coordination across time zones has moderate visual appeal.

**Feasibility (3/5):** Mock TradeNet and MPA endpoints require regulatory domain knowledge.

#### C5: Cross-Terminal Visibility Gap — Score: 2.20

**Agentic Sweet Spot (2/5):** The core problem is data integration — creating a unified view across separate CITOS instances. This is an integration/middleware challenge, not an agentic reasoning problem.

**Coverage (1/5):** Only 1 passing problem (PB-12) after PB-16 was eliminated. Lowest cluster multiplier.

**Demo Drama (3/5):** Cross-terminal visibility is important but the demo trace is less dramatic.

**Feasibility (3/5):** Mock cross-terminal queries require simulating two separate CITOS instances.

---

## Stage 3: Flagship Anchor Selection

### Winning Cluster: C2 — Manual Multi-Party Coordination

**Score: 4.80 / 5.00**

Cluster C2 dominates across all four dimensions. It has the highest agentic sweet spot (multi-party exception resolution is the canonical agentic use case), the broadest coverage (7 passing problems, ~$316K/month aggregate), the most compelling demo trace (visible tool calls, HITL gates, multi-party notifications), and high feasibility.

### Flagship Anchor Candidate Evaluation

Three candidates from C2 are the strongest:

| Candidate | Financial Impact | Systems | Multi-Party Complexity | Demo Drama |
|-----------|-----------------|---------|----------------------|------------|
| **PB-01** | $58.6K–$131.6K/incident | 4 (VTIS, OptEVoyage, CITOS, PORTNET) | Duty manager, pilot, shipping line, ship planner, feeder operators | Highest — tidal windows, feeder cascades |
| **PB-12** | $15.6K–$29K/incident | 5 (CITOS×2, OptETruck, feeder, PORTNET) | PPT planner, Tuas planner, ITT coordinator, feeder operator, gate | High — cross-terminal gap is systemic |
| **PB-04** | $6.5K–$36.5K/incident | 4 (CITOS, PORTNET, OptEVoyage, yard) | Duty manager, ship planner, shipping line, feeder operator | High — hold vs. roll trade-off |

### Selected Flagship: PB-12 — Multi-Party ITT Coordination Failure (Cross-Terminal)

**Rationale:**

1. **Systemic Architecture Gap:** PB-12 exposes the most fundamental infrastructure limitation — PPT and Tuas CITOS are separate instances with no real-time integration. This is not a process problem that better phone calls could solve; it is a systems architecture gap that requires an intelligent coordination layer.

2. **Highest System Count (5):** PB-12 involves more distinct PSA platforms than any other C2 candidate: CITOS (PPT), CITOS (Tuas), OptETruck (road ITT), feeder vessels (sea ITT), PORTNET (inventory tracking). This maximises the multi-tool orchestration showcase.

3. **Dual Transport Mode Optimisation:** The road/sea ITT split decision is a genuinely multi-objective problem — cost, time, capacity, and downstream loading impact must be balanced simultaneously. This is more complex than single-mode coordination.

4. **Demo Compelling for Competition:** The execution trace shows: agent receives container readiness notification → queries PPT yard status → queries road ITT capacity → queries sea ITT capacity → computes optimal split → dispatches trucks → monitors feeder departure → updates Tuas loading sequence. A clear, multi-step, multi-system story.

5. **Cluster Leverage:** PB-12 sits at the intersection of C2 (manual coordination) and C5 (cross-terminal visibility). Solving PB-12 addresses both root causes simultaneously, providing platform generalisation to the broader cross-terminal coordination problem.

### 4-Point Capability Check (PB-12)

| Check | Requirement | Evidence |
|-------|-------------|----------|
| **Event Trigger Ingestion** | Can receive and parse structured/unstructured disruption events | Container readiness notification from CITOS PPT + ITT dispatch request from coordinator |
| **Observable Multi-Step Trace** | Execution produces visible thought → action → observation chain | 7-step workflow: identify → check road → check sea → optimise → dispatch → monitor → update |
| **HITL Risk Gate** | At least one state-changing action requires human approval | Committing to road/sea split and dispatching 15 trucks requires ITT coordinator sign-off |
| **Injected Failure Recovery** | Demonstrates graceful handling of a failure scenario | Feeder vessel berth conflict → agent dynamically shifts from 60/40 sea/road to 30/70 split, reroutes trucks |

**All 4 capability checks satisfied.**

---

## Acceptance Criteria Verification

- [x] **At least 2–4 candidates objectively failed in Stage 1 with clear technical justification** — 4 problems failed (PB-03, PB-05, PB-14, PB-16) with specific L1/L2/L5 justifications.
- [x] **All 6 clusters scored with mathematical weighting in Stage 2** — 4 dimensions × weighted scores documented.
- [x] **Exactly ONE Winning Cluster and ONE Flagship Anchor Problem selected** — C2 (Manual Multi-Party Coordination) and PB-12 (Multi-Party ITT Coordination Failure).

---

## Next Steps

- **03-02:** Calibrate autonomy levels and HITL guardrails for PB-12
- **03-03:** Lock Master Problem Charter with mock API specifications, ROI model, and demo storyboard

---

## Sources

All evaluations grounded in:
- `problems/02-03-problem-bank.md` — 16 candidate problems with mock tool action spaces
- `problems/02-02-failure-modes.md` — 7-dimension failure analysis per scenario
- `research/flows/critical-flows.md` — Physical, Information, Decision flows
- `research/systems/baseline-systems.md` — 7 baseline system profiles
