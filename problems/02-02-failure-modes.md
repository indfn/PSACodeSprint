# 02-02: Operational Failure Modes & Friction Breakdown

**Status:** Draft  
**Sources:** Grounded in `problems/02-01-disruption-scenarios.md` and `research/`  
**Last updated:** 2026-08-17

---

## How to Read This Document

Each disruption scenario from 02-01 is analysed across 7 dimensions:

1. **Disruption Title & Sector**
2. **Trigger Event** — Initial alert, state change, EDI message, or sensor anomaly
3. **Primary Systems Involved** — Baseline platforms touched
4. **The System Handoff Gap** — Why automated rule engines cannot resolve this alone
5. **Current Manual Workaround** — How human operators currently resolve this
6. **Time-to-Criticality** — How long before impact becomes irreversible
7. **Business Consequence & Cost Drivers** — Financial, operational, and ESG impacts

**Time-to-Criticality Scale:**
| Level | Window | Description |
|-------|--------|-------------|
| 🔴 Critical | < 1 hour | Direct vessel movement, quay crane stoppage, or safety hazard |
| 🟠 High | 1–4 hours | Quay crane idling, gate queue spillover, missed flight window |
| 🟡 Medium | 4–24 hours | Yard re-handle accumulation, haulier schedule drift |

---

# Sector A: Berth & Marine Operations

---

## A1: Cascading Berth Delay & Tidal Window Lockout

**Sector:** Berth & Marine Operations  
**Time-to-Criticality:** 🟠 High (1–4 hours)

### Trigger Event

Vessel ETA slip notification received via VTIS/STRAITREP (VHF voice + digitalPORT@SG™ system update). OptEVoyage reports AIS-derived ETA change from 0600 to 1230. The berth allocation in CITOS was computed at T-72 hours based on original ETA.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| VTIS/STRAITREP | Vessel traffic management | VHF voice → MPA VTS → PORTNET notification |
| OptEVoyage | JIT ETA tracking | AIS data → ETA prediction → PORTNET/CITOS feed |
| CITOS | Berth allocation | Vessel particulars, tidal windows, crane split |
| PORTNET | Schedule coordination | Vessel call notice → shipping line, agent, terminal |
| A*STAR FMS | AGV scheduling | Berth plan → AGV dispatch queue |

### The System Handoff Gap

**Gap 1: Asynchronous ETA updates vs. synchronous berth allocation.**  
OptEVoyage receives AIS-derived ETA updates every 15 minutes. But CITOS berth allocation is computed once at T-72 hours and only re-optimised when a human planner triggers manual re-allocation. There is no automated trigger that says: "ETA slipped 6+ hours → re-run berth optimisation."

**Gap 2: Tidal window is a physical constraint that cannot be software-extended.**  
CITOS can flag that a vessel will miss its tidal window, but it cannot create a new tidal window. The decision to hold the berth (wasting QC capacity) or reallocate (risking the delayed vessel) requires human judgment weighing multiple conflicting objectives: vessel importance, downstream feeder connections, QC availability, and yard congestion.

**Gap 3: Feeder connection deadlines are not dynamically linked to mother vessel ETA.**  
PORTNET tracks feeder schedules separately. When the mother vessel slips, there is no automated system that recalculates which feeder connections are still achievable and which must be rolled. This requires manual coordination between ship planner, shipping line agent, and terminal duty manager.

### Current Manual Workaround

1. **Terminal duty manager** receives ETA slip notification (phone call from ship agent + PORTNET alert)
2. Duty manager opens CITOS berth planner screen and manually assesses: which berths are available at new ETA?
3. If no berth available: calls adjacent berth operators to negotiate crane re-deployment
4. If tidal window missed: contacts harbour pilot to confirm next available window
5. Contacts shipping line agent (phone/email) to discuss options: hold, re-route, or wait
6. Ship planner manually recalculates crane split for affected berths
7. Yard planner receives manual notification to adjust yard block assignments
8. Feeder coordination: ship agent contacts feeder operators to negotiate hold or rolling
9. All coordination happens via phone calls, WhatsApp groups, and email — no single system of record

**Resolution time:** 2–4 hours for initial assessment, 6–12 hours for full recovery plan.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Vessel demurrage | ~$3,000–$5,000/hr × 6.5 hr | ~$19,500–$32,500 |
| QC idle time | ~$350/hr × 4 cranes × 6.5 hr | ~$9,100 |
| Missed feeder connections | ~$200–$500/container × 150 TEUs | ~$30,000–$75,000 |
| Anchorage costs | ~$15,000–$25,000/day | ~$15,000–$25,000 |
| Operational friction | Phone-based coordination, manual replanning | 15–20 staff-hours |
| Carbon impact | Extended vessel idling at anchorage | ~5–10 tonnes CO2 |

---

## A2: Dual-Trolley Quay Crane (DTQC) Sudden Breakdown During Discharge

**Sector:** Berth & Marine Operations  
**Time-to-Criticality:** 🔴 Critical (< 1 hour)

### Trigger Event

DTQC gantry trolley motor failure detected by onboard sensors. ROCC (Remote Operations & Control Centre) operator receives alarm. QC automatically halts operations. A*STAR FMS detects AGV queue building at affected QC position.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| CITOS | QC scheduling, vessel plan | QC status update → re-optimisation request |
| ROCC | Remote crane operations | Alarm → operator alert → manual intervention |
| A*STAR FMS | AGV fleet management | QC offline → AGV rerouting |
| PORTNET | Vessel schedule | ETA update to shipping line |
| Ship planner | Vessel stability | Re-sequence discharge bays |

### The System Handoff Gap

**Gap 1: QC breakdown triggers are reactive, not predictive.**  
CITOS monitors QC status but does not predict failures. When a QC goes offline, the system must be manually told to re-optimise crane assignments across berths. There is no automated "crane failure → redistribute workload" pathway.

**Gap 2: AGV queue at QC is not automatically dissipated.**  
When a QC goes offline, A*STAR FMS has 12+ AGVs queued at the land-side pickup point. FMS can reroute new AGVs, but the already-queued AGVs must be manually redirected by the FMS operator. Each redirected AGV requires a new task assignment — this takes 2–5 minutes per AGV.

**Gap 3: Vessel stability constraints cannot be dynamically re-sequenced.**  
The ship planner must manually re-sequence discharge bays to maintain vessel trim. This requires checking the vessel's stability manual (physical document or PDF) and running manual calculations — CITOS does not have an integrated vessel stability calculator for emergency re-sequencing.

### Current Manual Workaround

1. **ROCC operator** acknowledges alarm, halts affected QC, notifies supervisor
2. **Supervisor** contacts maintenance crew (phone) for emergency repair assessment
3. **FMS operator** manually reroutes queued AGVs to adjacent QCs (2–5 min/AGV)
4. **Berth planner** opens CITOS and manually reassigns cranes from adjacent berths
5. **Ship planner** contacts vessel's chief officer (VHF) to discuss re-sequencing options
6. **Terminal duty manager** calls shipping line to provide updated ETA
7. **Maintenance crew** arrives, assesses repair time (30 min–8 hrs depending on failure)
8. All decisions logged in WhatsApp group (not in CITOS or any system of record)

**Resolution time:** 30 min for initial containment, 2–8 hours for full recovery.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| QC repair/downtime | ~$350/hr × 8 hr | ~$2,800 |
| Vessel delay extension | ~$3,000–$5,000/hr × 4 hr net | ~$12,000–$20,000 |
| AGV idle time | ~$50/hr × 12 AGVs × 2 hr | ~$1,200 |
| Cascade to next vessel | Berth window compression | Variable |
| Staff coordination | Phone/WhatsApp firefighting | 8–12 staff-hours |

---

## A3: Late Dangerous Goods (DG) Declaration & IMDG Compliance Hold

**Sector:** Berth & Marine Operations  
**Time-to-Criticality:** 🟠 High (1–4 hours)

### Trigger Event

PORTNET receives EDI DG amendment message (IMDG Code correction) from shipping line at T-6 hours before vessel arrival. CITOS stowage planner flags IMDG class conflict with existing plan.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| PORTNET | EDI DG declaration | DG amendment → CITOS stowage planner |
| CITOS | Stowage planning | IMDG conflict detection → manual resolution |
| MPA DGPE | Regulatory enforcement | Compliance check → potential penalties |
| Ship planner | Vessel stability | Re-stowage plan |
| Yard operations | DG yard management | Yard re-stack if stowage changes |

### The System Handoff Gap

**Gap 1: DG declaration timing vs. stowage plan finalisation.**  
Stowage plans are typically finalised 24 hours before arrival. DG declarations can be amended up to 12 hours before arrival (MPA requirement). This creates a 12-hour window where DG amendments can invalidate an already-finalised stowage plan. CITOS detects the conflict but cannot automatically resolve it — IMDG segregation rules are complex and vessel-specific.

**Gap 2: No automated re-stowage optimisation for DG conflicts.**  
When CITOS flags an IMDG conflict, the ship planner must manually identify compliant positions. The vessel may have limited positions that satisfy both IMDG segregation AND vessel stability constraints. This is a multi-constraint optimisation problem that CITOS does not solve for emergency re-stowage scenarios.

**Gap 3: MPA re-approval is a manual phone/email process.**  
After the ship planner develops a re-stowage plan, it must be submitted to MPA for re-approval. This is done via phone call and email — not through an automated system. Approval may take 1–4 hours depending on MPA officer availability.

### Current Manual Workaround

1. **CITOS** flags DG conflict in stowage plan notification
2. **Ship planner** manually reviews IMDG Code segregation tables (physical book or PDF)
3. Ship planner identifies 3–5 potential compliant positions on vessel
4. Ship planner runs manual stability check for each position
5. Ship planner selects optimal position, updates stowage plan in CITOS
6. **Terminal duty manager** calls MPA DGPE officer (phone) to request re-approval
7. MPA officer reviews re-stowage plan (email attachment)
8. **Yard planner** receives updated plan, adjusts yard DG block assignments if needed
9. **aRMG operator** re-handles affected containers to match new stowage sequence

**Resolution time:** 2–4 hours from amendment receipt to MPA re-approval.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Emergency re-stowage | ~$150–$300/container × 10 | ~$1,500–$3,000 |
| MPA penalty risk | Up to $100,000 (first conviction) | Variable |
| Vessel delay for re-approval | ~$3,000–$5,000/hr × 2–4 hr | ~$6,000–$20,000 |
| Yard re-handle | ~$30–$50/move × 5 | ~$150–$250 |
| Safety risk | Potential DG incident if mis-segregated | Incalculable |

---

## A4: Transhipment Missed-Connection Recovery (100+ Containers)

**Sector:** Berth & Marine Operations  
**Time-to-Criticality:** 🟠 High (1–4 hours)

### Trigger Event

OptEVoyage reports mother vessel ETA slip of 10 hours (Red Sea diversion). PORTNET shows 3 feeder vessels with departure times at 1800, 2000, 2200 tonight. CITOS berth allocation shows mother vessel will berth at 1600.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| CITOS | Berth allocation, ship planning | Vessel delay → re-optimise berth + crane split |
| PORTNET | Feeder schedules | Feeder departure times → connection feasibility |
| OptEVoyage | JIT tracking | AIS ETA → delay notification |
| Yard operations | Transhipment clustering | Yard block assignments → connection priority |

### The System Handoff Gap

**Gap 1: No automated connection risk assessment.**  
CITOS and PORTNET do not jointly calculate: "Given mother vessel delay of X hours, which feeder connections are still achievable?" This requires manual computation by the ship planner: discharge rate × time available = containers recoverable.

**Gap 2: Feeder hold vs. roll decision requires multi-party reasoning.**  
Holding a feeder vessel delays its entire schedule (downstream ports affected). Rolling containers to next sailing causes customer SLA breach and demurrage. No single system can reason over: vessel schedule, customer commitments, yard congestion, and downstream port impacts simultaneously.

**Gap 3: Yard-to-wharf transport time is not factored into connection risk.**  
Containers in yard blocks far from the wharf require 15–30 minutes of AGV transport. The ship planner must mentally account for this when computing whether containers can be loaded before feeder departure. CITOS does not provide a "time to load" estimate that includes yard-to-wharf transport.

### Current Manual Workaround

1. **Terminal duty manager** receives delay notification from ship agent
2. Duty manager contacts ship planner (phone) to discuss discharge options
3. Ship planner manually computes: 30 moves/hr × 2 hrs = 60 containers recoverable for Feeder 1
4. Ship planner contacts shipping line agent to discuss hold vs. roll
5. Shipping line agent contacts feeder operator to negotiate 2-hour hold
6. Feeder operator contacts downstream ports to assess impact
7. Decision made: hold Feeder 1 by 2 hours, roll 40 containers to next day
8. **Yard planner** receives manual notification to re-sequence transhipment blocks
9. **Ship planner** updates CITOS stowage plan for adjusted loading sequence
10. All parties notified via WhatsApp group and email

**Resolution time:** 3–6 hours for full recovery plan.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Feeder demurrage | ~$800–$1,500/hr × 2 hr | ~$1,600–$3,000 |
| Rolled containers | ~$100–$300/container/day × 40 | ~$4,000–$12,000/day |
| Customer SLA breach | Variable | ~$5,000–$20,000 |
| QC re-prioritisation | ~$30–$50/move × 30 | ~$900–$1,500 |
| Multi-party coordination | Phone/WhatsApp firefighting | 10–15 staff-hours |

---

# Sector B: Container Yard & Internal Transport

---

## B1: Reefer Cold-Chain Telemetry Excursion (High-Value Pharma Cargo)

**Sector:** Container Yard & Transport  
**Time-to-Criticality:** 🔴 Critical (< 1 hour)

### Trigger Event

ARMS detects temperature excursion (>2°C deviation from setpoint) on reefer container ONEU4567890. Alert generated to operations team via SMS and dashboard notification. Container is in reefer yard block R-07, power point #4521.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| ARMS | Reefer monitoring | Temperature alarm → operations team |
| CITOS | Yard assignment | Container position → M&R dispatch |
| Shipping line agent | Cargo owner | Spoilage assessment → insurance notification |
| Maintenance crew | Physical repair | Dispatch → repair → reconnection |

### The System Handoff Gap

**Gap 1: ARMS detects but cannot diagnose.**  
ARMS knows temperature is rising but cannot determine root cause: power plug fault? Compressor failure? Door seal breach? Power supply interruption? Each cause requires a different response (replug, repair, seal replacement, generator dispatch). ARMS alerts the operations team, but the diagnosis is manual.

**Gap 2: No automated escalation path based on cargo value.**  
Pharma cargo valued at $500,000 requires faster response than general reefer cargo. ARMS does not differentiate alert priority based on cargo value or spoilage risk. All reefer alerts are treated equally.

**Gap 3: M&R dispatch is phone-based.**  
Operations team must call maintenance crew (phone) to dispatch a technician. There is no automated dispatch system that routes the nearest available technician based on location, skill set, and spare parts inventory. At 0200, staff availability is limited.

### Current Manual Workaround

1. **ARMS** generates temperature alarm (auto)
2. **Operations team** acknowledges alarm, checks power supply status on dashboard
3. Operations team calls maintenance crew (phone) — 15–30 min response time
4. **Maintenance technician** arrives, diagnoses: power plug fault (visual inspection)
5. Technician replaces power plug (15 min)
6. Temperature stabilises within 30 min of repair
7. Operations team calls shipping line agent (phone) to report excursion
8. Shipping line agent contacts cargo owner and insurer
9. If cargo spoiled: insurance claim initiated (weeks-long process)
10. All events logged in ARMS but not in CITOS or any unified system of record

**Resolution time:** 30 min–4 hrs depending on cause and staff availability.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Cargo spoilage | If excursion >4 hrs, total loss | ~$500,000 |
| Emergency maintenance | Repair + parts | ~$500–$2,000 |
| Technician dispatch (OT) | After-hours callout | ~$200–$500 |
| Insurance claim admin | Processing + investigation | ~$5,000–$15,000 |
| Vessel loading delay | If container critical for vessel | ~$3,000–$5,000/hr |
| Carbon: wasted energy | Reefer running while malfunctioning | ~50–100 kWh |

---

## B2: Yard Block Buffer Overflow from Delayed Vessel

**Sector:** Container Yard & Transport  
**Time-to-Criticality:** 🟡 Medium (4–24 hours)

### Trigger Event

CITOS yard planner receives vessel delay notification. Export containers continue arriving at gate (OptETruck bookings confirmed). Yard blocks B-12 through B-15 (assigned for delayed vessel) approaching capacity.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| CITOS | Yard planning | Block utilisation → overflow detection |
| A*STAR FMS | AGV dispatch | Yard congestion → AGV routing adjustment |
| aRMG controllers | Yard crane operations | Block full → re-handle operations |
| Gate operations | Export arrivals | Container intake → yard assignment |

### The System Handoff Gap

**Gap 1: Yard block capacity is not dynamically linked to vessel ETA.**  
CITOS assigns yard blocks based on vessel schedule. When vessel delays, the yard plan is not automatically re-optimised. Export containers continue arriving because gate operations have no real-time signal to slow down. OptETruck bookings were made hours/days in advance and cannot be instantly cancelled.

**Gap 2: Overflow container routing requires manual planner intervention.**  
When blocks reach 95% utilisation, CITOS can suggest alternative blocks, but the planner must manually verify: (a) alternative block is not already committed, (b) AGV travel time increase is acceptable, (c) loading sequence is not disrupted. This is a multi-constraint decision with no automated solution.

**Gap 3: aRMG re-handle operations compete with loading operations.**  
Re-stacking containers to create space uses aRMG capacity that could otherwise be used for loading. The yard planner must manually schedule re-handles during a window that doesn't conflict with active QC loading. No system provides a "re-handle vs. loading trade-off" analysis.

### Current Manual Workaround

1. **Yard planner** notices block utilisation approaching 95% (CITOS dashboard)
2. Planner manually checks alternative blocks in CITOS
3. Planner calls gate operations (phone) to request slowing export arrivals
4. Gate operator contacts OptETruck to adjust slot availability
5. Planner schedules aRMG re-handles during a 2-hour window (no loading conflicts)
6. aRMG operator executes re-handles (~15–30 min for 20 containers)
7. **Ship planner** notified that containers may not be in optimal positions
8. Ship planner adjusts vessel loading sequence in CITOS
9. All decisions logged in planner's notebook (not in system)

**Resolution time:** 4–8 hours from detection to resolution.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Unproductive re-handles | ~$30–$50/move × 80 moves | ~$2,400–$4,000 |
| AGV efficiency loss | 40% longer travel × 15 AGVs × 2 hr | ~$1,500 |
| Extended vessel berthing | ~$3,000–$5,000/hr × 3 hr | ~$9,000–$15,000 |
| Downstream impact | Next vessel's yard assignment affected | Variable |

---

## B3: Post-Stacking IMDG Class Conflict Discovery

**Sector:** Container Yard & Transport  
**Time-to-Criticality:** 🟠 High (1–4 hours)

### Trigger Event

PORTNET receives DG amendment EDI message for Container B (Class 9 → Class 4.1). CITOS yard inventory system detects IMDG class conflict with adjacent Container A (Class 3). Alert generated to yard planner and DG compliance officer.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| PORTNET | DG declaration | Amendment → CITOS conflict detection |
| CITOS | Yard inventory | IMDG conflict flag → re-handle plan |
| aRMG | Yard crane | Re-handle execution |
| MPA DGPE | Regulatory compliance | Re-stowage plan approval |

### The System Handoff Gap

**Gap 1: DG amendments arrive after stacking — no pre-stacking validation against future amendments.**  
CITOS validates IMDG segregation at time of stacking based on current declarations. But DG amendments can arrive up to 12 hours before arrival (or later in emergency cases). There is no system that predicts: "What if Container B's classification changes?" The conflict is only discovered after the amendment arrives.

**Gap 2: Minimum-move relocation plan requires manual computation.**  
The yard planner must manually identify the minimum number of container moves to resolve the conflict. This requires checking: all adjacent containers' DG classes, available compliant positions, and aRMG scheduling. No automated optimisation exists for this.

**Gap 3: MPA re-approval for DG re-stowage is phone/email-based.**  
Same gap as A3 — regulatory approval is manual, time-consuming, and creates delay.

### Current Manual Workaround

1. **CITOS** flags IMDG class conflict (auto)
2. **Yard planner** manually reviews DG segregation tables (IMDG Code book)
3. Planner identifies 2–3 potential compliant positions in DG yard
4. Planner checks aRMG availability for re-handle window
5. Planner develops relocation plan (which containers to move, in what sequence)
6. **DG compliance officer** reviews plan for regulatory compliance
7. Officer calls MPA DGPE (phone) to request re-approval
8. **aRMG operator** executes re-handles during designated window
9. CITOS yard inventory updated after re-handles complete
10. All events logged in DG compliance register (paper or spreadsheet)

**Resolution time:** 2–6 hours from amendment receipt to re-approval.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| aRMG re-handle | ~$30–$50/move × 3–5 moves | ~$90–$250 |
| DG compliance risk | MPA penalty up to $100,000 | Variable |
| Yard disruption | aRMG downtime for DG block | ~$500–$1,000 |
| Emergency response standby | Safety team on standby | ~$300–$800 |
| Vessel loading delay | If DG container critical | ~$3,000–$5,000/hr |

---

## B4: 5G Network Outage Impacting AGV Fleet Coordination

**Sector:** Container Yard & Transport  
**Time-to-Criticality:** 🔴 Critical (< 1 hour)

### Trigger Event

Private 5G base station at Tuas Port fails. A*STAR FMS detects increased AGV communication latency (10ms → 20–40ms). FMS activates traffic de-rating protocols. QC operations slow as AGV pickup/delivery cycle time increases.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| 5G network (Singtel) | AGV communication | Latency spike → FMS degradation |
| A*STAR FMS | AGV fleet management | De-rating → throughput reduction |
| CITOS | QC scheduling | QC productivity drop → vessel delay |
| DTQC operations | Crane operations | AGV wait time increase |

### The System Handoff Gap

**Gap 1: No automated fallback for 5G dependency.**  
AGV fleet operations are designed for 5G latency (10ms). When 5G fails, the system falls back to 4G (20–40ms latency), but the FMS does not automatically adjust fleet parameters (spacing, speed, task assignment) for degraded communication. The de-rating is manual.

**Gap 2: QC operations are not aware of 5G status.**  
QC operators continue discharging containers at normal rate, but AGVs cannot keep up. The QC-to-AGV handoff becomes asynchronous — containers pile up at the transfer platform with no AGV to pick them up. No system alerts QC operators to slow down.

**Gap 3: Battery charging schedule is disrupted.**  
AGVs cannot receive updated charging instructions during 5G outage. Some AGVs may run low on battery and become stranded in the yard, requiring manual towing. No system provides battery status visibility to ground operators during communication degradation.

### Current Manual Workaround

1. **A*STAR FMS operator** detects latency spike, activates de-rating mode (manual toggle)
2. FMS operator contacts 5G network provider (Singtel, phone) to report outage
3. **QC operators** notified verbally (phone) to reduce discharge rate
4. **Yard supervisors** redirect AGVs to wider spacing manually
5. If AGV stranded: ground crew dispatches manual towing vehicle (~30 min)
6. Singtel technician dispatched to repair base station (1–4 hrs)
7. After repair: FMS operator manually restores normal operations
8. All events logged in operations log (paper or spreadsheet)

**Resolution time:** 30 min for initial containment, 1–4 hours for 5G restoration.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Lost QC productivity | ~$350/hr × 4 cranes × 1.5 hr | ~$2,100 |
| Vessel delay extension | ~$3,000–$5,000/hr × 2 hr | ~$6,000–$10,000 |
| AGV fleet efficiency loss | ~$50/hr × 40 AGVs × 1.5 hr | ~$3,000 |
| 5G restoration | Emergency maintenance | ~$10,000–$50,000 |
| Stranded AGV towing | Manual towing + crew | ~$500–$1,000 |

---

# Sector C: Gate & External Haulage Operations

---

## C1: eDO/VGM Discrepancy at Gate — Queue Cascade

**Sector:** Gate & Haulage Operations  
**Time-to-Criticality:** 🟠 High (1–4 hours)

### Trigger Event

AGS (Automated Gate System) detects eDO not found in PORTNET for arriving truck. Weighbridge shows VGM discrepancy >5% between declared and actual weight. AGS blocks entry, truck pulled to exception lane.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| AGS/OCR | Gate processing | Block entry → exception lane |
| PORTNET | eDO status | Delivery order check → not found |
| Weighbridge | VGM validation | Weight discrepancy → block |
| OptETruck | Slot management | Queue build-up → rebalancing |
| Yard operations | Container pickup | Container not released → hold |

### The System Handoff Gap

**Gap 1: eDO release timing is not coordinated with truck arrival.**  
Shipping lines release eDOs in PORTNET based on their own schedules, which may not align with haulier booking times. A haulier books a slot via OptETruck at 1800 for pickup at 2300, but the shipping line may not release the eDO until 2200 (or later). AGS checks eDO in real-time — if not yet released, entry is blocked. No system alerts the haulier that eDO is not yet available before they depart depot.

**Gap 2: VGM discrepancy resolution is time-constrained.**  
If VGM discrepancy >5%, haulier must re-advise VGM in PORTNET (>4 hrs before vessel ETB). At 2300, the 4-hour window may have already passed. The haulier cannot amend VGM — the container is stuck. No system provides a "VGM amendment feasibility check" before the haulier departs depot.

**Gap 3: Exception lane blocks OCR lane — no automated overflow.**  
When a truck is pulled to the exception lane, it physically blocks one of 4 OCR lanes. Queue builds rapidly (60% of trucks arrive in the 2300–0100 peak window). AGS does not automatically open overflow lanes or redirect trucks to alternate gates. Manual intervention is required to open additional lanes.

### Current Manual Workaround

1. **AGS** blocks entry, directs truck to exception lane (auto)
2. **Gate operator** checks PORTNET for eDO status (manual lookup)
3. Operator contacts shipping line agent (phone) to request eDO release
4. Shipping line agent checks internal system, releases eDO (15–60 min)
5. **Weighbridge operator** verifies VGM discrepancy, contacts haulier (phone)
6. Haulier contacts consignee to correct VGM (phone/email)
7. Consignee amends VGM in PORTNET (if within time window)
8. **Operations supervisor** opens overflow gate lane (manual)
9. Queue clears in 30–60 min after eDO/VGM resolved
10. All events logged in gate operations log (paper)

**Resolution time:** 30 min–3 hours depending on eDO/VGM resolution.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Gate processing delay | ~$50–$100/truck × 30 trucks × 30 min | ~$750–$1,500 |
| Queue spillover | Expressway approach blocked | LTA fine risk |
| Haulier TRT extension | ~$30–$50/hr × 2 hr × 5 hauliers | ~$300–$500 |
| VGM late amendment | $10/container | $10 |
| Staff firefighting | Phone/WhatsApp coordination | 3–5 staff-hours |

---

## C2: External Disruption to Haulier Pools (Weather/Fleet Shortage)

**Sector:** Gate & Haulage Operations  
**Time-to-Criticality:** 🟡 Medium (4–24 hours)

### Trigger Event

AYE expressway accident blocks 2 lanes for 3 hours. OptETruck GPS tracking shows 60% of booked hauliers delayed. SmartBooking slot system shows 45 trucks missed 0700–0800 window.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| OptETruck | TMS, routing | GPS delay detection → rebalancing |
| SmartBooking | Slot management | Missed slots → rebooking |
| PORTNET | Gate schedule | Delayed arrivals → gate plan update |
| CITOS | Yard planning | Late containers → loading sequence update |

### The System Handoff Gap

**Gap 1: OptETruck cannot dynamically re-route around expressway blockage.**  
OptETruck uses HERE Technologies for routing, which can detect traffic incidents. But re-routing 60 trucks in real-time requires: (a) each truck's current position, (b) alternative routes, (c) updated ETAs. The system provides recommendations but cannot force trucks to take alternate routes — drivers make their own decisions.

**Gap 2: SmartBooking slots are fixed once booked.**  
When hauliers book slots via SmartBooking, the slots are locked. If a haulier is delayed, the slot is wasted. SmartBooking does not have an automated "slot release and reassign" mechanism. The haulier must manually cancel and rebook — but at 0700, there are no available slots for the rest of the morning.

**Gap 3: Yard planner is not automatically notified of delayed containers.**  
CITOS yard plan assumes containers will arrive per schedule. When 60% are delayed, the yard plan becomes invalid. The yard planner learns about delays through phone calls from gate operations — not from any automated system. This delays the loading sequence re-planning.

### Current Manual Workaround

1. **OptETruck** detects traffic delay, sends route advisory to affected drivers (auto)
2. **SmartBooking** shows missed slots on dashboard (auto)
3. **Operations team** calls delayed hauliers (phone) to confirm ETAs
4. Operations team contacts gate operations to open overflow lanes for afternoon
5. **Gate operator** manually rebalances afternoon slot availability
6. Operations team calls yard planner (phone) to notify delayed container arrivals
7. **Yard planner** manually re-sequences loading plan in CITOS
8. Operations team contacts shipping line to discuss loading delay options
9. All events logged in operations WhatsApp group

**Resolution time:** 4–12 hours from incident to full recovery.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Haulier idle time | ~$50/hr × 60 trucks × 3 hr | ~$9,000 |
| Vessel loading delay | ~$3,000–$5,000/hr × 2 hr | ~$6,000–$10,000 |
| Yard re-sequencing | Planner overtime + re-handles | ~$500–$1,000 |
| Carbon impact | 60 trucks idling × 3 hr × 2.5 kg CO2/hr | ~450 kg CO2 |

---

## C3: Empty Container Rejection & Off-Dock Depot Defect Loop

**Sector:** Gate & Haulage Operations  
**Time-to-Criticality:** 🟡 Medium (4–24 hours)

### Trigger Event

AGS gate inspection detects structural damage to empty container corner post. Container flagged as "defective — requires M&R assessment." Haulier cannot drop off container at on-dock depot.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| AGS | Gate inspection | Damage detection → rejection |
| iBOX | Depot management | M&R slot availability |
| OptETruck | Haulier routing | Return job matching |
| Shipping line agent | Container ownership | M&R authorisation |

### The System Handoff Gap

**Gap 1: Damage detection at gate has no automated M&R routing.**  
AGS detects damage and flags the container, but it does not automatically find an available M&R facility. The haulier must manually search for available depots, call each to check M&R slot availability, and negotiate pricing. No integrated M&R marketplace exists.

**Gap 2: Haulier's OptETruck return job conflicts with M&R requirement.**  
OptETruck matched the haulier with a return job (empty pickup from another depot) based on the assumption the current container would be dropped off quickly. The M&R rejection creates a conflict: complete the return job (lose time) or divert to M&R (lose the return job incentive). OptETruck does not dynamically re-route for M&R scenarios.

**Gap 3: Shipping line M&R authorisation is phone-based.**  
The haulier or depot must contact the shipping line to authorise M&R. This is done via phone call. The shipping line may take 1–4 hours to respond (especially after hours). Without authorisation, the depot cannot proceed with repairs.

### Current Manual Workaround

1. **AGS** detects damage, flags container (auto)
2. **Gate operator** notifies haulier of rejection (phone/verbal)
3. Haulier calls depot (phone) to check M&R availability
4. Depot checks M&R schedule, offers slot in 2–4 hours
5. Haulier calls OptETruck support to re-route (phone)
6. OptETruck support manually cancels return job, assigns M&R route
7. Haulier drives to M&R depot (45 min)
8. Depot contacts shipping line (phone) for M&R authorisation
9. Shipping line responds in 1–4 hours
10. M&R completed in 2–8 hours
11. Haulier returns container to on-dock depot or proceeds to next job

**Resolution time:** 4–24 hours from rejection to M&R completion.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| M&R repair | Corner post repair | ~$200–$800 |
| Haulier deadhead | Fuel + time to M&R facility | ~$50–$100 |
| Missed return job | OptETruck incentive lost | ~$80–$150 |
| Chassis pool blocking | Chassis held during M&R | ~$30–$50/day |
| Carbon waste | 45 km deadhead × 2.5 kg CO2/km | ~112 kg CO2 |

---

## C4: Drop-and-Hook Bottleneck Under Tight Free-Time SLA

**Sector:** Gate & Haulage Operations  
**Time-to-Criticality:** 🟡 Medium (4–24 hours)

### Trigger Event

PORTNET demurrage tracking shows import container CMAU5678901 approaching free time expiry (midnight). Haulier's chassis pool is fully utilised. Earliest chassis available: 0200 tomorrow.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| PORTNET | Demurrage tracking | Free time expiry alert |
| OptETruck | Asset pooling | Chassis availability check |
| SmartBooking | Slot management | Pickup slot booking |
| iBOX | Depot operations | Chassis pool status |

### The System Handoff Gap

**Gap 1: Demurrage clock is not linked to chassis availability.**  
PORTNET tracks free time expiry but does not check whether the haulier has chassis available for pickup. The haulier learns about the demurrage risk only when they attempt to book a slot — and discovers no chassis available. No system proactively alerts: "Free time expires in 24 hours, chassis pool at 100% — book now."

**Gap 2: OptETruck asset pooling has stale data.**  
OptETruck shows partner haulier chassis availability, but the data may be 15–30 minutes old. By the time the haulier requests a chassis, it may already be assigned to another job. No real-time chassis reservation system exists.

**Gap 3: Free time extension is a manual negotiation.**  
Extending free time requires contacting the shipping line (phone/email). The shipping line may refuse or charge a fee. No automated system exists for requesting/accepting free time extensions.

### Current Manual Workaround

1. **PORTNET** shows free time expiry approaching (auto alert)
2. **Haulier** checks OptETruck for chassis availability — pool at 100%
3. Haulier calls partner hauliers (phone) to request chassis loan
4. Partner confirms 4 chassis available (15–30 min response)
5. Haulier calls shipping line (phone) to request free time extension
6. Shipping line offers 1-day extension for $50 fee
7. Haulier accepts, books chassis from partner via OptETruck
8. Books pickup slot via SmartBooking for tomorrow 0800
9. Container picked up on time — demurrage avoided
10. All events logged in haulier's system (not in PSA systems)

**Resolution time:** 4–12 hours of coordination.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Demurrage | ~$150/day × 1–3 days | ~$150–$450 |
| Emergency chassis rental | ~$200/day | ~$200 |
| Coordinator time | Phone/email firefighting | 2–4 staff-hours |
| Customer relationship | Demurrage passed to consignee | Reputational |
| Carbon | Additional truck trip if emergency rental | ~25 kg CO2 |

---

# Sector D: Multimodal Logistics & Supply Chain Adjacencies

---

## D1: Sea-to-Air Transhipment Flight Cut-Off Threat

**Sector:** Multimodal Logistics  
**Time-to-Criticality:** 🔴 Critical (< 1 hour)

### Trigger Event

OptEModal detects vessel arrival 8 hours late. AI calculates that 50 sea-air containers cannot reach Changi Airfreight Centre and clear customs before 2000 flight departure. Risk alert generated to operations team.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| OptEModal | Sea-air coordination | Delay detection → risk alert |
| CITOS | Terminal ops | Priority discharge request |
| CALISTA | Milestone tracking | Exception flag |
| TradeNet | Customs | Pre-clearance submission |
| SATS/dnata | Ground handling | Cargo acceptance slot |
| Airline | Flight operations | Rebooking decision |

### The System Handoff Gap

**Gap 1: No single system has authority to expedite all steps.**  
The 24-hour transfer requires: (a) priority QC discharge, (b) priority ITT dispatch, (c) express customs clearance, (d) priority SATS handling. Each step is controlled by a different system/operator. OptEModal can detect the risk and recommend actions, but it cannot force CITOS to assign extra QCs, or force TradeNet to expedite clearance, or force SATS to accept cargo outside normal hours.

**Gap 2: Customs pre-clearance requires documents that may not be ready.**  
TradeNet allows pre-clearance submission, but the customs broker may not have all documents ready (bill of lading, certificate of origin, etc.). OptEModal cannot automatically generate or validate customs documents — these come from the forwarder's system.

**Gap 3: Flight rebooking is a commercial decision, not a system decision.**  
OptEModal can suggest alternative flights, but the decision to rebook involves: cargo owner approval, airline availability, additional cost authorisation. No system can autonomously rebook a flight — it requires human judgment and commercial negotiation.

### Current Manual Workaround

1. **OptEModal** generates risk alert (auto)
2. **Operations team** assesses feasibility of 12-hour window (manual calculation)
3. Team calls CITOS terminal ops (phone) to request priority discharge
4. CITOS assigns 2 additional QCs (manual override)
5. Team calls customs broker (phone) to pre-lodge TradeNet clearance
6. Customs broker submits documents to TradeNet (15–30 min)
7. Team calls SATS (phone) to request expedited cargo acceptance
8. SATS confirms slot (if available) or suggests alternative
9. Team contacts airline (phone) to discuss rebooking options
10. If 12-hour window cannot be met: airline rebooks cargo (commercial negotiation)
11. All decisions logged in WhatsApp group and email chain

**Resolution time:** 1–6 hours from risk detection to resolution.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Flight rebooking | Cargo rebooking fee | ~$5,000–$15,000 |
| Customer SLA breach | Electronics manufacturing delay | ~$10,000–$50,000 |
| Priority discharge premium | Extra QC allocation | ~$2,000–$5,000 |
| SATS expedite | After-hours handling | ~$1,000–$3,000 |
| Carbon | Additional flight or extended trucking | Variable |

---

## D2: Cross-Border Customs / Regulatory Inspection Hold

**Sector:** Multimodal Logistics  
**Time-to-Criticality:** 🟠 High (1–4 hours)

### Trigger Event

TradeNet flags shipment for phytosanitary inspection (random HS code selection). CALISTA milestone tracker shows hold status. Cargo cannot proceed past Changi FTZ "In" gate.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| TradeNet | Customs | Inspection hold flag |
| CALISTA | Milestone tracking | Hold status → all parties |
| OptEModal | Transfer coordination | Delay notification → schedule recalculation |
| SATS/dnata | Ground handling | Cargo acceptance slot at risk |
| Forwarder | Documentation | Certificate of origin retrieval |

### The System Handoff Gap

**Gap 1: Inspection hold is binary — no partial release mechanism.**  
When TradeNet flags a shipment for inspection, the entire shipment is held. There is no mechanism to release the non-inspected portion while the inspection proceeds. All 50 containers are blocked, even if only 5 are flagged.

**Gap 2: Documentation retrieval requires cross-time-zone coordination.**  
The phytosanitary certificate is with the shipper in Mumbai (2.5 hours behind Singapore). The forwarder must contact the shipper, who must find the document, scan it, and email it. No digital document repository or blockchain-based document sharing exists for this scenario.

**Gap 3: Inspection timing is not coordinated with flight schedule.**  
The inspector is available at 1500, but the flight departs at 1600. There is no system that alerts the inspector: "This cargo has a flight at 1600 — please prioritise." The inspection queue is managed internally by the agency, not linked to OptEModal's timeline.

### Current Manual Workaround

1. **TradeNet** flags inspection hold (auto)
2. **CALISTA** notifies all parties of hold (auto)
3. **OptEModal** recalculates feasibility of making flight (auto suggestion)
4. **Operations team** calls customs broker (phone) to discuss inspection timeline
5. Customs broker contacts phytosanitary agency (phone) to check inspector availability
6. **Forwarder** contacts shipper in Mumbai (email/WhatsApp) to retrieve certificate
7. Shipper finds document, scans, emails (30–60 min across time zones)
8. Customs broker submits additional documents to TradeNet
9. Inspector completes inspection at 1500 (if all documents ready)
10. Cargo released at 1530 — race to Changi for 1600 flight
11. If missed: cargo rebooked on 2200 or next-day flight

**Resolution time:** 2–8 hours depending on documentation and inspection timeline.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Flight delay | Rebooking + demurrage | ~$3,000–$8,000 |
| Cargo hold | Storage at Changi FTZ | ~$500–$1,000/day |
| Customer impact | Manufacturing line delay (pharma) | ~$10,000–$50,000/day |
| Inspection fee | Agency charges | ~$200–$500 |
| Documentation coordination | Staff time across time zones | 4–8 staff-hours |

---

## D3: Cold-Chain Pharma Discrepancy at Regional Distribution Hub

**Sector:** Multimodal Logistics  
**Time-to-Criticality:** 🟠 High (1–4 hours)

### Trigger Event

PSCH warehouse ops detects temperature logger discrepancy during container devanning. Physical logger shows 3-hour excursion; digital telematics shows compliance. Roambee sensor confirms current temperature is within range.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| Roambee | Sensor data | Item-level tracking → historical data |
| PSA BDP Temp Guard | Cold chain monitoring | Discrepancy flag → control tower |
| CALISTA | Milestone tracking | Exception status update |
| PSCH warehouse | Devanning ops | Physical inspection |
| Insurer | Coverage decision | Excursion verification |

### The System Handoff Gap

**Gap 1: Two data sources disagree — no arbitration mechanism.**  
Physical logger (placed at origin) and digital telematics (installed on reefer) show different data. No system can determine which is correct. This requires: (a) checking logger calibration certificate, (b) lab analysis of cargo, (c) cross-referencing Roambee sensor data. The decision involves multiple parties with conflicting incentives (forwarder wants acceptance, consignee wants rejection, insurer wants verification).

**Gap 2: Insurer requires third-party verification — no integrated process.**  
The insurance policy requires independent lab analysis before coverage decision. No system integrates with lab services or provides automated sample collection scheduling. The forwarder must manually arrange lab testing (phone call to lab, sample courier, 24–48 hr turnaround).

**Gap 3: Accept/reject decision requires multi-party consensus.**  
The decision to accept, reject, or partially accept the cargo involves: forwarder, consignee, insurer, and PSA warehouse. No system facilitates this decision — it happens via email chain and phone calls. The cargo sits in cold storage ($2,000–$5,000/day) while the decision is made.

### Current Manual Workaround

1. **PSCH warehouse** detects logger discrepancy during devanning (manual observation)
2. Warehouse operator flags container in system (CITOS/PSCH inventory)
3. **PSA BDP Temp Guard** shows discrepancy on control tower dashboard (auto)
4. Warehouse operator calls operations manager (phone)
5. Manager calls forwarder (phone) to discuss discrepancy
6. Forwarder calls shipper (phone) to retrieve logger calibration certificate
7. Forwarder contacts insurer (phone/email) to report potential claim
8. Insurer requests third-party lab analysis (email)
9. Forwarder arranges lab sample collection (phone, 24–48 hr turnaround)
10. Meanwhile, cargo held in cold storage ($2,000–$5,000/day)
11. Lab results confirm or deny excursion
12. Multi-party decision: accept (with discount), reject (total loss), or partial acceptance

**Resolution time:** 24–72 hours for full resolution.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Cargo hold | Cold storage at PSCH | ~$2,000–$5,000/day |
| Lab testing | Third-party analysis | ~$1,000–$3,000 |
| Insurance claim | Processing + investigation | ~$5,000–$15,000 |
| Customer impact | Pharma supply chain disruption | ~$10,000–$100,000/day |
| Cargo degradation | If excursion confirmed | ~$500,000–$2M (total loss) |

---

## D4: Multi-Party ITT Coordination Failure (Cross-Terminal)

**Sector:** Multimodal Logistics  
**Time-to-Criticality:** 🟠 High (1–4 hours)

### Trigger Event

120 transhipment containers at Pasir Panjang Terminal must reach Tuas Port for 2000 vessel departure. Current time: 1000. Both road ITT and sea ITT options have coordination failures.

### Primary Systems Involved

| System | Role | Data Flow |
|--------|------|-----------|
| CITOS (PPT) | Yard operations | Container availability → ITT dispatch |
| CITOS (Tuas) | Yard receiving | ITT arrival → yard assignment |
| OptETruck | Road ITT | Truck dispatch → GPS tracking |
| Feeder vessel | Sea ITT | Berth availability → departure |
| PORTNET | Inventory tracking | Container status across terminals |

### The System Handoff Gap

**Gap 1: Road ITT and sea ITT are not coordinated.**  
OptETruck manages road ITT. Feeder vessels manage sea ITT. No system coordinates both options simultaneously to optimise the split. The decision of "send 80 containers by road and 40 by sea" requires manual computation and multi-party agreement.

**Gap 2: PPT and Tuas CITOS are separate instances.**  
CITOS at Pasir Panjang and CITOS at Tuas are not integrated. Container availability at PPT is not visible to Tuas yard planner in real-time. The Tuas planner must rely on PORTNET inventory updates, which may be 30–60 minutes delayed.

**Gap 3: ITT arrival timing is not linked to QC loading sequence.**  
Tuas yard planner expects containers at 1600 (road ITT estimate). But if sea ITT delivers at 1800, the QC loading sequence must be re-planned. No system provides a "containers in transit" view that updates the loading sequence in real-time.

### Current Manual Workaround

1. **PPT yard planner** identifies 120 containers ready for ITT (CITOS query)
2. Planner contacts Tuas yard planner (phone) to discuss receiving capacity
3. Tuas planner confirms yard blocks available, suggests 60/40 road/sea split
4. PPT planner contacts OptETruck (phone) to dispatch 15 trucks
5. OptETruck dispatches trucks (auto, but PPT gate congestion delays 5 trucks)
6. PPT planner contacts feeder vessel operator (phone) to confirm 1400 departure
7. Feeder operator reports berth conflict — departure delayed to 1600
8. Tuas planner learns of feeder delay (phone from PPT planner)
9. Tuas planner re-sequences QC loading for delayed sea ITT containers
10. Road ITT arrives at 1300 — Tuas yard processes 60 containers
11. Sea ITT arrives at 1800 — Tuas yard processes remaining 60 containers
12. QC loading delayed by 2 hours (waiting for sea ITT containers)

**Resolution time:** 4–8 hours of coordination.

### Business Consequence & Cost Drivers

| Category | Impact | Estimated Cost |
|----------|--------|---------------|
| Vessel delay | ~$3,000–$5,000/hr × 2 hr | ~$6,000–$10,000 |
| Road ITT cost | ~$100–$200/trip × 20 trucks × 2 trips | ~$4,000–$8,000 |
| Sea ITT cost | Feeder charter | ~$5,000–$10,000 |
| Yard re-handling | ~$30–$50/move × 20 re-handles | ~$600–$1,000 |
| Customer SLA | Missed connections at destination | Variable |

---

# Cross-System Failure Mode Summary

## System Handoff Gap Patterns

Across all 16 scenarios, three systemic patterns emerge:

### Pattern 1: Asynchronous State Updates
Multiple systems maintain separate state copies that are not synchronised in real-time:
- CITOS berth plan vs. OptEVoyage ETA updates (A1)
- PORTNET eDO vs. haulier arrival time (C1)
- PPT CITOS vs. Tuas CITOS (D4)
- Physical logger vs. digital telematics (D3)

**Root cause:** No unified event bus or real-time state synchronisation across PSA systems.

### Pattern 2: Manual Multi-Party Coordination
Every scenario requires phone calls, WhatsApp groups, or email chains to resolve:
- Vessel delay → phone calls to agents, pilots, shipping lines (A1, A4)
- QC breakdown → phone calls to maintenance, adjacent berths (A2)
- Gate exception → phone calls to shipping lines, hauliers (C1, C3)
- Customs hold → phone calls to brokers, inspectors, forwarders (D2)

**Root cause:** No multi-party workflow automation platform exists for exception resolution.

### Pattern 3: No Automated Escalation Based on Impact
All alerts are treated equally regardless of cargo value, customer importance, or time-criticality:
- Pharma reefer alarm treated same as general reefer (B1)
- Electronics sea-air cargo treated same as low-value cargo (D1)
- Demurrage-expiring container treated same as low-priority pickup (C4)

**Root cause:** No impact-based alert prioritisation or escalation engine.

---

## Acceptance Criteria Verification

- [x] **All 16+ scenarios have all 7 analysis fields fully documented** ✅
- [x] **System handoff gaps clearly explain the breakdown between baseline tools** ✅
- [x] **Cost drivers are grounded in standard Singapore port and maritime logistics economics** ✅

---

## Sources

All failure modes are grounded in the following Phase 1 research files:
- `research/sectors/berth-marine.md`
- `research/sectors/container-yard-transport.md`
- `research/sectors/gate-haulage.md`
- `research/sectors/multimodal-logistics.md`
- `research/systems/baseline-systems.md`
- `research/flows/critical-flows.md`
