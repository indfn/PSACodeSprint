# Phase 2: Disruption Mining & Problem Bank Creation — PLAN

**Status:** ✅ COMPLETE (2026-08-17)
**Depends on:** Phase 1 Deliverables in `research/`
**Requirements:** P2-01 (Disruption Scenarios), P2-02 (Operational Failure Modes), P2-03 (Problem Bank)

---

## 0. Context Ingestion & Upstream Rules (MANDATORY)

Before executing any task below, the agent **MUST**:
1. **Read All Phase 1 Files:** Ingest and parse all markdown and data files located in `research/`.
2. **Ground in Mapped Baseline Systems:** Ensure all disruption analyses reference the specific PSA systems documented in Phase 1 (CITOS, PORTNET, OptETruck, SmartBooking/iBOX, OptEModal, CALISTA, PSA BDP).
3. **Ground in Mapped Flows:** Pull directly from the Physical, Information, and Decision flow maps generated in Phase 1.
4. **Research Restriction:** DO NOT run open-ended general web searches. Rely on `research/` as the primary ground truth. Only perform targeted queries if a specific quantitative cost parameter or API schema is missing from Phase 1.

---

## 1. Adaptive Scenario & Checklist Protocol

* The disruption items listed in Task 02-01 are **Seed Archetypes & Quality Benchmarks**.
* **Dynamic Adaptation:** If your Phase 1 research in `research/` contains richer, more specific, or novel operational failure points (e.g., specific Tuas 5G telemetry drops, Pasir Panjang terminal phase-out bottlenecks, or TradeNet clearance quirks), **you are explicitly instructed to append, refine, or replace the seed items with your Phase 1 findings**.
* **Quality Constraint:** Every final scenario must be non-deterministic, involve cross-system handoffs, and have measurable operational cost.

---

## Tasks

### 02-01: Mine Cross-System Disruption Scenarios

Synthesize Phase 1 research to identify dynamic operational disruptions where static business logic, rule engines, or simple optimizers fail due to asynchronous updates, unstructured communication, or multi-party friction.

**Deliverable:** `problems/02-01-disruption-scenarios.md`

**Step 1: Ingest Phase 1 Findings & Match Against Seed Archetypes:**
Verify which of the following disruption patterns were surfaced in `research/`, and append any additional sector-specific failure modes discovered:

#### Sector A: Berth & Marine Operations
- [ ] **Cascading Berth Delay & Tidal/Draft Window Lockout:** Mother vessel ETA slips, missing high tide; CITOS berth reallocation causes downstream crane-split conflicts and feeder connection misses.
- [ ] **Late Dangerous Goods (DG) / IMDG Compliance Hold:** Hazardous container declared incorrectly or held by MPA/Customs while planned in the stowage sequence, forcing emergency re-stowage.
- [ ] **Dual-Trolley Quay Crane (QC) Sudden Breakdown:** QC goes offline during discharge, creating quay-side AGV queues and requiring dynamic redistribution of discharge bays.
- [ ] **Transhipment Missed-Connection Recovery:** Inbound vessel delay risks 100+ transhipment containers missing outbound connecting vessel; requires trade-off reasoning between vessel hold vs. rolling cargo.
- [ ] *(Dynamic Slot)* **[Append any Phase 1 Marine Disruption finding here]**

#### Sector B: Container Yard & Internal Transport
- [ ] **Reefer Cold-Chain Telemetry Excursion:** Reefer container triggers temperature threshold alarms; requires verifying power plug, technician dispatch, cargo value check, and emergency repacking.
- [ ] **Yard Block Buffer Overflow from Delayed Vessel:** Vessel delay causes export containers to pile up in yard blocks, forcing unproductive container re-handles and blocking aRMG crane corridors.
- [ ] **Post-Stacking DG Physical Segregation Violation:** Manifest amendment received after container stacking reveals an IMDG class conflict with an adjacent container; requires minimum-move yard relocation plan.
- [ ] **Pasir Panjang ↔ Tuas Inter-Terminal Transfer (ITT) Rush Balancing:** Priority transhipment containers must move across terminals via public expressway/dedicated corridors during peak traffic without delaying vessel loading.
- [ ] *(Dynamic Slot)* **[Append any Phase 1 Yard Disruption finding here]**

#### Sector C: Gate & External Haulage Operations
- [ ] **Manifest & Electronic Delivery Order (eDO) Discrepancy at Gate:** Haulier arrives with invalid eDO or container weight (VGM) mismatch; gate kiosk halts entry, causing queue backup across OCR lanes.
- [ ] **External Disruption to Haulier Pools (Traffic / Weather / Fleet Shortage):** Expressway congestion causes 40% of booked hauliers to miss time-slots; requires dynamic slot re-balancing between OptETruck and SmartBooking.
- [ ] **Empty Container Rejection & Off-Dock Depot Defect Loop:** Haulier arrives with damaged empty box rejected by terminal inspection; requires real-time routing to depot M&R without deadhead trucking miles.
- [ ] **Drop-and-Hook Bottleneck under Tight Free-Time SLA:** Demurrage/detention clock expiring on import cargo while haulier chassis availability is constrained; requires cross-haulier asset-pooling coordination.
- [ ] *(Dynamic Slot)* **[Append any Phase 1 Haulage Disruption finding here]**

#### Sector D: Multimodal Logistics & Supply Chain Adjacencies (OptEModal / CALISTA)
- [ ] **Sea-to-Air Transhipment Flight Cut-Off Threat:** Vessel berthing delay jeopardizes a tight 12-hour transfer window to Changi Airport for scheduled flight departure; requires priority discharge, express customs clearance, and airline flight rebooking.
- [ ] **Cross-Border Customs / Regulatory Inspection Hold:** Singapore Customs or phytosanitary agency places an unexpected inspection hold on multimodal cargo mid-transit; requires multi-party notification and partial manifest release.
- [ ] **Cold-Chain Pharma Discrepancy in Regional Distribution Hub:** Temperature logger mismatch during container devanning at Supply Chain Hub @ Tuas (PSCH); requires coordination between forwarder, insurer, and terminal.
- [ ] *(Dynamic Slot)* **[Append any Phase 1 Multimodal Disruption finding here]**

**Acceptance Criteria for 02-01:**
- [ ] Minimum 12 disruption scenarios cataloged (at least 3 per sector).
- [ ] Every scenario explicitly identifies the data/event source documented in `research/`.
- [ ] Every scenario involves at least two interacting entities (e.g., Vessel ↔ Yard, Terminal ↔ Haulier, Sea ↔ Air).
- [ ] Excludes out-of-scope/pre-solved problems (e.g., microsecond AGV pathing, standard gate barcode scans).

---

### 02-02: Map Operational Failure Modes & Friction Breakdown

For each scenario cataloged in `02-01`, analyze why existing software fails and document the manual workaround currently used by operators.

**Deliverable:** `problems/02-02-failure-modes.md`

**Required Structure per Disruption Scenario:**
1. **Disruption Title & Sector**
2. **Trigger Event:** Initial alert, state change, EDI message (e.g., BAPLIE, CODECO, IFTMIN), or sensor anomaly.
3. **Primary Systems Involved:** Baseline platforms touched (e.g., CITOS ↔ PORTNET ↔ OptETruck ↔ MPA Marinet).
4. **The System Handoff Gap:** Why automated rule engines cannot resolve this alone (e.g., unstructured communications, conflicting stakeholder incentives, asynchronous data lag).
5. **Current Manual Workaround:** Step-by-step description of how human operators currently resolve this (phone calls, spreadsheets, manual emails).
6. **Time-to-Criticality:**
   - *Critical (< 1 hour):* Direct impact on vessel movement, quay crane stoppage, or physical safety hazard.
   - *High (1–4 hours):* Quay crane idling, gate queue spillover, missed flight window.
   - *Medium (4–24 hours):* Yard re-handle accumulation, haulier schedule drift.
7. **Business Consequence & Cost Drivers:**
   - Financial penalties (vessel demurrage: ~$1,500–$3,500/hr; QC idle: ~$350/hr; yard re-handle: ~$30–$50/move; airfreight SLA breach: ~$5–$10/kg).
   - Operational friction (gate queue spillover, yard congestion, haulier TRT degradation).
   - Carbon / ESG impacts (excess diesel idling, wasted truck trips).

**Acceptance Criteria for 02-02:**
- [ ] All 12+ scenarios have all 7 analysis fields fully documented.
- [ ] System handoff gaps clearly explain the breakdown between baseline tools.
- [ ] Cost drivers are grounded in standard Singapore port and maritime logistics economics.

---

### 02-03: Consolidate & Quantify the Problem Bank (10–15 Problems)

Select the most compelling scenarios and formalize them into a structured problem bank ready for Phase 3 Litmus Testing.

**Deliverable:** `problems/02-03-problem-bank.md`

**Required Schema per Problem Bank Entry:**

### PB-XX: [Problem Title]
- **Sector:** [Berth & Marine | Yard & Transport | Gate & Haulage | Multimodal]
- **Problem Statement:** [1–2 concise sentences detailing the core operational failure]
- **Trigger & Data Source:** [Specific alert, telemetry data, EDI message from Phase 1 research]
- **Systems & Stakeholders Involved:**
  - *Systems:* [e.g., CITOS Berth Module, PORTNET eDO, OptETruck TMS]
  - *Stakeholders:* [e.g., Terminal Duty Manager, Shipping Line Agent, Prime Mover Driver]
- **The Information & Coordination Gap:** [Why current software leaves a blindspot]
- **Current Resolution Workflow:** [Current manual firefighting steps]
- **Quantified Impact Formula:**
  - *Metric:* [e.g., Avoided Vessel Delays (hrs × $/hr) + Avoided Re-handles (moves × $/move)]
  - *Estimated Scale:* [e.g., ~$35,000 per incident; occurs ~3 times/week across Pasir Panjang/Tuas]
- **Agentic AI Value Hypothesis:** [Why an Agent is required: Multi-tool orchestration, reasoning over conflicting objectives, unstructured data extraction, dynamic recovery planning]
- **Candidate Action Space (Mock Tools):** [List 3–5 specific API tools the agent would orchestrate, e.g., `get_berth_schedule()`, `query_reefer_telemetry()`, `reroute_itt_truck()`, `request_customs_override()`]
- **Initial Autonomy Level:** [Advisory | Human-in-the-Loop | Supervised Autonomous]

**Acceptance Criteria for 02-03:**
- [ ] 10–15 fully completed problem entries following the exact schema above.
- [ ] Balanced distribution across all 4 sectors (minimum 2 per sector).
- [ ] Cross-system integration: Minimum 4 problems involving coordination across multiple sectors or platforms.
- [ ] Every entry contains a concrete cost formula and a candidate mock-tool action space.

---

## Deliverables Summary

| Task | Deliverable File | Target Output |
| :--- | :--- | :--- |
| **02-01** | `problems/02-01-disruption-scenarios.md` | 12+ real-world disruption scenarios across 4 sectors grounded in `research/` |
| **02-02** | `problems/02-02-failure-modes.md` | Detailed failure mode, handoff gap, and manual workaround analysis |
| **02-03** | `problems/02-03-problem-bank.md` | 10–15 structured, quantified problem charters ready for Litmus Testing |

---

## Exit Gate Checklist

Phase 2 is complete when:
- [ ] All 3 markdown deliverables exist in `problems/`.
- [ ] Phase 1 artifacts in `research/` have been fully integrated (no ungrounded hallucinations).
- [ ] Every problem in `problems/02-03-problem-bank.md` contains an explicit mathematical cost formula and mock tool action space.
- [ ] Ready for immediate scoring in **Phase 3 (Agentic AI Litmus Test & Final Selection)**.
