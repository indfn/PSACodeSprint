# 02-01: Cross-System Disruption Scenarios

**Status:** Draft  
**Sources:** Synthesised from `research/` Phase 1 deliverables  
**Last updated:** 2026-08-17

---

## Methodology

Each scenario is grounded in specific Phase 1 research findings. Scenarios are marked with verification status:
- ✅ Grounded in multiple Phase 1 research files
- ⚠️ Grounded in single research file, needs cross-verification
- 🔍 Inferred from friction points, needs targeted validation

Every scenario satisfies three quality constraints:
1. **Non-deterministic** — outcome depends on timing, weather, equipment state, or human decision
2. **Cross-system handoff** — involves 2+ interacting PSA systems or entities
3. **Measurable cost** — quantifiable financial, operational, or ESG impact

---

# Sector A: Berth & Marine Operations

## A1: Cascading Berth Delay & Tidal Window Lockout

**Trigger:** Mother vessel ETA slips 6+ hours due to weather or congestion in Singapore Strait; misses pre-booked high tide window at deep-water berth.

**Systems involved:** VTIS/STRAITREP → CITOS (berth allocation) → PORTNET (vessel schedules) → OptEVoyage (JIT ETA updates) → A*STAR FMS (AGV scheduling).

**Scenario:**  
A 14,000 TEU mother vessel on OptEVoyage JIT tracker reports ETA slip from 0600 to 1230 due to monsoon swell in the Malacca Strait. The berth allocated at Pasir Panjang (23m draft, tidal-restricted) requires high tide at 0800 for safe berthing. CITOS must now decide: (a) hold berth and waste QC capacity, (b) reallocate berth to another vessel, or (c) re-sequence crane splits across adjacent berths to accommodate both vessels.

Simultaneously, 3 feeder vessels scheduled for transhipment connections have cut-off deadlines tied to the mother vessel's original berthing. The delay cascades: if the mother vessel misses the 1800 cut-off for outbound feeders, 150+ transhipment containers miss connections, requiring rolling to next sailing or emergency feeder rerouting.

**Cost impact:**
- Vessel demurrage: ~$3,000–$5,000/hr × 6.5 hr delay = ~$19,500–$32,500
- QC idle time: ~$350/hr × 4 cranes × 6.5 hr = ~$9,100
- Missed feeder connections: ~$200–$500/container × 150 TEUs = ~$30,000–$75,000
- Anchorage costs for waiting vessels: ~$15,000–$25,000/day

**Research grounding:**
- JIT 72-hr berth allocation notification: `berth-marine.md:75-80`
- CITOS berth allocation considers draft, tidal windows, crane split: `berth-marine.md:113-120`
- Transhipment connection scheduling: `berth-marine.md:229-254`
- Known friction: vessel arrival timing mismatch, tidal window constraints: `berth-marine.md:260-268`
- Decision flow — disruption path: `critical-flows.md:110-131`

---

## A2: Dual-Trolley Quay Crane (DTQC) Sudden Breakdown During Discharge

**Trigger:** DTQC main trolley or gantry trolley fails mid-operation; QC goes offline during active discharge of a mother vessel.

**Systems involved:** CITOS (QC scheduling) → A*STAR FMS (AGV dispatch) → ROCC (remote crane operations) → PORTNET (vessel schedule updates).

**Scenario:**  
At Tuas Port, a DTQC servicing an 18,000 TEU vessel suffers a gantry trolley motor failure at 1400 during peak discharge operations. The vessel has 4 QCs assigned with a 36-hour berth window. Losing one QC reduces throughput by 25%. CITOS must immediately:

1. Redeploy QCs from adjacent berths (if available) — but those vessels also have tight schedules
2. Reschedule AGV dispatch sequences — the QC's yard-side buffer queue now has 12 AGVs waiting with no pickup point
3. Update vessel ETA to shipping line — potential downstream connection misses
4. Notify ROCC operators to reconfigure remaining 3 QCs for optimised bay coverage

The breakdown creates a quay-side AGV traffic jam. A*STAR FMS attempts rerouting but the yard blocks assigned to this vessel are now receiving containers at 75% rate, causing yard-side buffer saturation. Meanwhile, the ship planner must re-sequence remaining discharge bays to maintain vessel stability constraints.

**Cost impact:**
- QC repair/downtime: ~$350/hr × 8 hr (typical repair) = ~$2,800
- Vessel delay extension: ~$3,000–$5,000/hr × 4 hr (net delay after recovery) = ~$12,000–$20,000
- AGV idle time: ~$50/hr × 12 AGVs × 2 hr = ~$1,200
- Cascade to next vessel: berth window compression for subsequent call

**Research grounding:**
- QC breakdowns cascade into vessel delays: `berth-marine.md:263`
- DTQC operations at Tuas: `berth-marine.md:124-129`
- QC sequencing constraints: `berth-marine.md:135-142`
- AGV fleet management and deadlock: `container-yard-transport.md:108-116`
- Decision flow — crane breakdown path: `critical-flows.md:110-131`

---

## A3: Late Dangerous Goods (DG) Declaration & IMDG Compliance Hold

**Trigger:** Shipping line submits DG declaration amendments 6 hours before vessel arrival; containers already planned in stowage sequence have IMDG class conflicts with adjacent containers.

**Systems involved:** PORTNET (EDI DG declaration) → CITOS (stowage planning) → MPA (DGPE enforcement) → ship planner (manual intervention).

**Scenario:**  
A mother vessel carrying 45 DG containers has a stowage plan finalised 24 hours before arrival. At T-6 hours, the shipping line submits a DG amendment via PORTNET EDI: Container SGPQ1234567 declared as Class 3 (flammable liquid) is actually Class 6.1 (toxic substance) with a Class 3 subsidiary risk. IMDG Code requires minimum 3m separation between Class 6.1 and Class 8 (corrosive) containers — but the current plan has them stacked in the same bay, 2 positions apart.

CITOS flags the conflict but the automated stowage optimizer cannot resolve it — the vessel has limited Class 6.1-compatible stowage positions due to deck vs. hold constraints. The ship planner must:
1. Identify all affected containers in the bay
2. Re-stowage plan: move Class 6.1 container to a compliant position
3. Check vessel stability/trim after repositioning
4. Coordinate with MPA for re-approval
5. Update CITOS yard assignment (containers may need to be re-stacked at yard to match new stowage sequence)

DG declaration deadline is 12 hours before arrival (MPA requirement). Late amendments create compliance risk: MPA can impose penalties or require off-vessel inspection.

**Cost impact:**
- Emergency re-stowage: ~$150–$300/container × 10 affected containers = ~$1,500–$3,000
- MPA penalty risk: up to $100,000 for non-compliance (first conviction)
- Vessel delay for re-approval: ~$3,000–$5,000/hr × 2–4 hr = ~$6,000–$20,000
- Yard re-handle: ~$30–$50/move × 5 moves = ~$150–$250

**Research grounding:**
- DG declaration requirements (12/24 hrs): `berth-marine.md:209-213`
- Dedicated DG yards post-Tianjin: `berth-marine.md:211`
- IMDG Code physical segregation: `container-yard-transport.md:297-299`
- Known friction: DG declaration errors: `berth-marine.md:264`
- DG inspection and enforcement: `container-yard-transport.md:319-328`

---

## A4: Transhipment Missed-Connection Recovery (100+ Containers)

**Trigger:** Inbound mother vessel delay of 8+ hours risks 100+ transhipment containers missing outbound feeder connections; requires trade-off reasoning between vessel hold vs. rolling cargo.

**Systems involved:** CITOS (berth allocation + ship planning) → PORTNET (feeder schedules) → OptEVoyage (JIT tracking) → yard operations (transhipment clustering).

**Scenario:**  
A mother vessel from Europe arrives 10 hours late due to Red Sea diversions. 200 transhipment containers are planned for three outbound feeder vessels departing between 1800–2200 tonight. With the mother vessel now berthing at 1600, QC discharge rate of 30 moves/hour means:

- Feeder 1 (1800 departure): Can only discharge 40 of 80 planned containers → 40 missed
- Feeder 2 (2000 departure): Can discharge 60 of 70 planned containers → 10 missed  
- Feeder 3 (2200 departure): Can discharge all 50 planned → 0 missed

CITOS and the terminal duty manager must decide:
1. **Hold Feeder 1** by 2 hours (delays feeder's entire schedule, downstream impacts at 3 regional ports)
2. **Roll 40 containers** to next day's feeder (demurrage risk, customer SLA breach)
3. **Prioritise discharge** of transhipment containers over import containers (disrupts import yard plan)

Each option has cascading consequences across the port network. The decision requires reasoning over conflicting objectives: vessel turnaround time, feeder schedule reliability, customer commitments, yard congestion, and QC productivity.

**Cost impact:**
- Feeder demurrage: ~$800–$1,500/hr × 2 hr = ~$1,600–$3,000
- Rolled containers demurrage: ~$100–$300/container/day × 40 = ~$4,000–$12,000
- Customer SLA penalties: variable, potentially ~$5,000–$20,000
- QC re-prioritisation: yard re-handle cost ~$30–$50/move × 30 re-handles = ~$900–$1,500

**Research grounding:**
- Transhipment architecture and connection scheduling: `berth-marine.md:229-254`
- JIT platform and feeder coordination: `berth-marine.md:73-82`
- Known friction: inter-terminal transfer delays, multi-stakeholder coordination: `berth-marine.md:265-267`
- Decision flow — vessel delay path: `critical-flows.md:110-131`

---

# Sector B: Container Yard & Internal Transport

## B1: Reefer Cold-Chain Telemetry Excursion (High-Value Pharma Cargo)

**Trigger:** ARMS detects temperature excursion (>2°C deviation from setpoint) on a reefer container carrying pharmaceutical cargo; requires verifying power plug, technician dispatch, cargo value assessment, and emergency response.

**Systems involved:** ARMS (reefer monitoring) → CITOS (yard assignment) → shipping line agent (cargo owner) → maintenance crew → insurance.

**Scenario:**  
At 0200, ARMS flags Container ONEU4567890 — temperature rising from 2–8°C to 12°C (pharma cold chain tolerance: 2–8°C). The container is in reefer yard block R-07, plugged into power point #4521. ARMS auto-generates alert to operations team.

Operations team must triage:
1. **Power supply check:** Is the power plug functional? (ARMS shows "power on" but temperature rising — could be plug fault, compressor failure, or door seal breach)
2. **Technician dispatch:** Maintenance crew dispatched (15–30 min response time at 0200)
3. **Cargo value assessment:** Pharma cargo (insulin) valued at ~$500,000; spoilage = total loss
4. **Emergency options:** (a) Repair in-situ, (b) Move container to functioning reefer point, (c) Request emergency off-vessel reefer from shipping line
5. **Notification chain:** Shipping line agent, cargo owner, insurer, PSA operations manager

ARMS auto-blocking prevents the container from being loaded onto a vessel, but the decision to repair vs. reroute vs. emergency repack requires multi-party coordination within the critical temperature window (pharma typically allows 2–4 hrs excursion before spoilage risk).

**Cost impact:**
- Cargo spoilage: ~$500,000 (total loss if excursion exceeds 4 hrs)
- Emergency maintenance: ~$500–$2,000
- Technician dispatch (OT): ~$200–$500
- Replacement reefer point allocation: ~$100–$300/day
- Insurance claim processing: ~$5,000–$15,000 admin cost
- Vessel loading delay if container is critical: ~$3,000–$5,000/hr

**Research grounding:**
- ARMS monitoring 10,000+ reefers: `container-yard-transport.md:240-248`
- Reefer infrastructure (13,000+ power points): `container-yard-transport.md:232-237`
- Known friction: power outage response, repair coordination: `container-yard-transport.md:266-271`
- Decision flow — reefer alarm: `critical-flows.md:238-241`

---

## B2: Yard Block Buffer Overflow from Delayed Vessel

**Trigger:** Vessel delay of 12+ hours causes export containers to accumulate in yard blocks beyond planned capacity, forcing unproductive re-handles and blocking aRMG crane corridors.

**Systems involved:** CITOS (yard planning) → A*STAR FMS (AGV dispatch) → aRMG controllers → gate operations (export arrivals).

**Scenario:**  
A vessel scheduled to load 2,000 export containers at 0800 is delayed to 2000. Meanwhile, gate operations continue receiving export containers — 200 trucks arrive between 0800–1200 with containers destined for yard blocks B-12 through B-15 (assigned for this vessel). By 1200, yard blocks B-12 and B-13 reach 95% utilisation.

CITOS yard planner attempts dynamic rebalancing:
1. Redirect new export containers to overflow blocks B-20/B-21 (farther from wharf — longer AGV travel time)
2. Re-stack existing containers to create space — but this requires aRMG re-handles (~$30–$50/move)
3. Notify gate to slow export arrivals (OptETruck slot rebalancing)
4. Coordinate with ship planner for updated loading sequence (containers may not be in optimal yard position when vessel finally berths)

The overflow creates a cascade: aRMG corridors become congested with re-handle operations, AGV travel times increase by 40%, and the yard blocks near the wharf (normally reserved for high-priority transhipment) are now occupied by delayed export containers.

**Cost impact:**
- Unproductive re-handles: ~$30–$50/move × 80 moves = ~$2,400–$4,000
- AGV efficiency loss: ~$50/hr × 15 AGVs × 2 hr additional travel = ~$1,500
- Extended vessel berthing: ~$3,000–$5,000/hr × 3 hr = ~$9,000–$15,000
- Downstream impact on next vessel's yard assignment

**Research grounding:**
- Yard block load balancing: `container-yard-transport.md:170-177`
- Container stacking strategies: `container-yard-transport.md:195-211`
- Known friction: yard congestion, equipment breakdowns: `container-yard-transport.md:429-432`
- Decision flow — block full path: `critical-flows.md:228-232`

---

## B3: Post-Stacking IMDG Class Conflict Discovery

**Trigger:** Manifest amendment received after container stacking reveals an IMDG class conflict with an adjacent container; requires minimum-move yard relocation plan.

**Systems involved:** PORTNET (DG declaration update) → CITOS (yard inventory) → aRMG (re-handle) → MPA (DGPE compliance) → emergency response.

**Scenario:**  
Two DG containers are stacked in yard block DG-03 (dedicated DG yard). Container A (Class 3 — flammable liquid) was stacked at position DG-03-04-A. Container B (Class 9 — miscellaneous DG) was stacked at position DG-03-04-B (adjacent). This stacking was compliant at time of stacking.

Six hours later, PORTNET receives a DG amendment for Container B: original declaration of Class 9 was incorrect — actual classification is Class 4.1 (flammable solid). IMDG Code requires minimum separation between Class 3 and Class 4.1 containers. CITOS flags the conflict.

Yard planner must:
1. Identify all containers in DG-03 affected by the reclassification
2. Develop a relocation plan that moves minimum containers (cost-optimised)
3. Check if any compliant adjacent position exists (considering other DG classes present)
4. Coordinate aRMG re-handle during a window that doesn't conflict with active loading operations
5. Notify MPA of the re-stowage plan for approval
6. Update CITOS yard inventory and DG tracking

**Cost impact:**
- aRMG re-handle: ~$30–$50/move × 3–5 moves = ~$90–$250
- DG compliance risk if not resolved: MPA penalties up to $100,000
- Yard operation disruption: ~$500–$1,000 (aRMG downtime for DG block)
- Emergency response team standby: ~$300–$800
- Vessel loading delay if DG container is critical: ~$3,000–$5,000/hr

**Research grounding:**
- IMDG Code physical segregation rules: `container-yard-transport.md:297-299`
- Dedicated DG storage areas post-Tianjin: `container-yard-transport.md:292-300`
- DG declaration and tracking: `container-yard-transport.md:307-316`
- Known friction: DG mis-declaration: `container-yard-transport.md:428`

---

## B4: 5G Network Outage Impacting AGV Fleet Coordination

**Trigger:** Private 5G network at Tuas Port experiences outage (hardware failure or congestion); AGV fleet coordination degraded; fallback to 4G with higher latency.

**Systems involved:** 5G network (Singtel partnership) → A*STAR FMS → CITOS (AGV dispatch) → aRMG controllers → QC operations.

**Scenario:**  
At 1000 during peak discharge operations, the private 5G network at Tuas Port suffers a base station failure. AGV-to-FMS communication degrades from 10ms latency (5G) to 20–40ms (4G fallback). A*STAR FMS detects increased latency and activates traffic de-rating protocols:

1. AGV spacing increased (safety buffer) → fewer AGVs in active zone → throughput drops 20–30%
2. QC discharge rate reduces because AGV pickup/delivery cycle time increases
3. DTQC gantry trolley operations slow (waiting for AGV positioning confirmation)
4. Battery charging scheduling disrupted (AGVs cannot receive updated charging instructions)

The 5G outage lasts 90 minutes. During this period:
- QC productivity drops from 32 to 22 moves/hour per crane
- 4 QCs × 90 min × 10 fewer moves/hr = 600 fewer container moves
- Vessel discharge timeline extended by ~3 hours
- A*STAR FMS enters "degraded mode" — automated traffic management partially disabled

**Cost impact:**
- Lost QC productivity: ~$350/hr × 4 cranes × 1.5 hr = ~$2,100
- Vessel delay extension: ~$3,000–$5,000/hr × 2 hr (net after recovery) = ~$6,000–$10,000
- AGV fleet efficiency loss: ~$50/hr × 40 AGVs × 1.5 hr = ~$3,000
- 5G restoration cost (emergency maintenance): ~$10,000–$50,000

**Research grounding:**
- 5G network: 10ms latency, Singtel partnership: `container-yard-transport.md:79`
- A*STAR FMS and AGV fleet management: `container-yard-transport.md:83-93`
- Known friction: 5G network dependency: `container-yard-transport.md:123`
- 5G benefits: tighter AGV spacing, real-time feeds: `container-yard-transport.md:96-99`

---

# Sector C: Gate & External Haulage Operations

## C1: eDO/VGM Discrepancy at Gate — Queue Cascade

**Trigger:** Haulier arrives with invalid electronic Delivery Order (eDO) or container weight (VGM) mismatch; gate kiosk halts entry, causing queue backup across OCR lanes.

**Systems involved:** PORTNET (eDO) → AGS/OCR (gate system) → weighbridge → CITOS (yard assignment) → OptETruck (slot management).

**Scenario:**  
At 2300 (peak gate congestion window), a haulier arrives at Tuas Port Gate with a container booked for import pickup. The AGS system checks:
1. OCR reads container number: verified ✓
2. eDO status: **NOT FOUND** — the shipping line has not yet released the delivery order in PORTNET
3. Weighbridge: VGM shows 28,500 kg, but declared VGM is 24,000 kg (>5% discrepancy)

AGS blocks entry. The truck pulls aside to the exception lane, but this blocks one of 4 OCR lanes. Queue builds rapidly:
- 15 trucks queue within 10 minutes
- 30 trucks queue within 20 minutes
- Queue spills into the expressway approach lane

Operations team must:
1. Contact shipping line agent (at 2300 — limited staff) to release eDO
2. Verify VGM discrepancy — haulier must re-advise VGM in PORTNET (>4 hrs before vessel ETB or face $10/container charge)
3. Manually clear queue by opening overflow processing lane
4. Coordinate with OptETruck to rebalance remaining time slots

**Cost impact:**
- Gate processing delay: ~$50–$100/truck × 30 trucks × 30 min = ~$750–$1,500
- Queue spillover (expressway): potential LTA fine + reputational cost
- Haulier TRT extension: ~$30–$50/hr × 2 hr × 5 affected hauliers = ~$300–$500
- VGM late amendment: $10/container × 1 = $10

**Research grounding:**
- FTG processing 25 seconds, 700 trucks/hr: `gate-haulage.md:64-68`
- eDO and VGM compliance: `gate-haulage.md:104-118`
- Peak congestion window 23:00–01:00: `critical-flows.md:295`
- Known friction: gate congestion, VGM non-compliance: `gate-haulage.md:355-358`

---

## C2: External Disruption to Haulier Pools (Weather/Fleet Shortage)

**Trigger:** Expressway congestion (accident, weather, road works) causes 40% of booked hauliers to miss time-slots; requires dynamic slot re-balancing between OptETruck and SmartBooking.

**Systems involved:** OptETruck (TMS) → SmartBooking (slot management) → PORTNET (gate schedule) → CITOS (yard planning) → affected hauliers.

**Scenario:**  
A major accident on the Ayer Rajah Expressway (AYE) at 0700 blocks 2 lanes for 3 hours. 60% of booked haulier slots for the 0700–1000 window are for export containers. Affected hauliers:
- 45 trucks booked for 0700–0800 slot: 30 delayed (67%)
- 40 trucks booked for 0800–0900 slot: 20 delayed (50%)
- 35 trucks booked for 0900–1000 slot: 10 delayed (29%)

OptETruck attempts dynamic rebalancing:
1. Reallocate delayed slots to hauliers stuck in queue (but they cannot reach terminal)
2. Push delayed slots to afternoon window (but afternoon slots already 80% booked)
3. Notify yard planner — export containers now arrive 3+ hours late, affecting vessel loading sequence
4. Coordinate with SmartBooking — depot bookings for empty container pickups also delayed

The delay cascades to yard operations: vessel loading planned for 1200 now has 85 containers not yet arrived at yard. Ship planner must re-sequence loading to prioritise containers already in yard.

**Cost impact:**
- Haulier idle time: ~$50/hr × 60 trucks × 3 hr = ~$9,000
- Vessel loading delay: ~$3,000–$5,000/hr × 2 hr = ~$6,000–$10,000
- Yard re-sequencing: ~$500–$1,000 (planner overtime + re-handles)
- Carbon impact: ~60 trucks idling × 3 hr × 2.5 kg CO2/hr = ~450 kg CO2

**Research grounding:**
- OptETruck scheduling and slot management: `gate-haulage.md:135-163`
- SmartBooking integration: `gate-haulage.md:165-178`
- Known friction: gate congestion, haulier slot mismatches: `gate-haulage.md:355-363`
- Decision flow — congestion path: `critical-flows.md:347-350`

---

## C3: Empty Container Rejection & Off-Dock Depot Defect Loop

**Trigger:** Haulier arrives with damaged empty box rejected by terminal inspection; requires real-time routing to depot M&R without deadhead trucking miles.

**Systems involved:** AGS (gate inspection) → iBOX (depot management) → OptETruck (routing) → depot M&R system → shipping line agent.

**Scenario:**  
A haulier delivers an empty container (CMAU7890123) to the on-dock depot after completing an import de-stuffing. Gate inspection detects:
- Structural damage to right-hand corner post (visible dent, potential frame compromise)
- Minor oil residue inside container
- Seal intact, no cargo discrepancy

AGS flags container as "defective — requires M&R assessment." The container cannot be restuffed for export until repaired. The haulier is now stuck:
1. Container rejected at on-dock depot → cannot drop off
2. Must take container to off-dock M&R facility → 45 min drive to Jurong
3. But haulier has a return job (OptETruck matched) → must complete pickup within 2 hours or lose incentive
4. If haulier drives to M&R, the return job is missed → empty trip added back to statistics
5. If haulier completes return job first, the defective container sits on chassis → blocking chassis pool

Shipping line agent must be notified to authorise M&R. iBOX must find available M&R slot at nearest depot. OptETruck must re-route haulier to M&R and reassign the return job to another truck.

**Cost impact:**
- M&R repair: ~$200–$800 (corner post repair)
- Haulier deadhead to M&R facility: ~$50–$100 (fuel + time)
- Missed return job: ~$80–$150 (incentive lost)
- Chassis pool blocking: ~$30–$50/day (if chassis held overnight)
- Carbon waste: ~45 km deadhead × 2.5 kg CO2/km = ~112 kg CO2

**Research grounding:**
- iWX container reuse prediction: `container-yard-transport.md:364-382`
- Empty depot management: `container-yard-transport.md:355-362`
- Known friction: empty container imbalances, OptETruck adoption gaps: `gate-haulage.md:359-363`
- Empty container return logistics: `gate-haulage.md:268-324`

---

## C4: Drop-and-Hook Bottleneck Under Tight Free-Time SLA

**Trigger:** Demurrage/detention clock expiring on import cargo while haulier chassis availability is constrained; requires cross-haulier asset-pooling coordination.

**Systems involved:** PORTNET (demurrage tracking) → OptETruck (asset pooling) → SmartBooking (slot management) → iBOX (depot ops) → haulier fleet systems.

**Scenario:**  
Import container CMAU5678901 has been at the terminal for 5 days. Free time expires at midnight — demurrage of $150/day begins tomorrow. The cargo consignee has arranged pickup, but the haulier's chassis pool is fully utilised:
- Haulier has 20 chassis, all in use
- 8 containers are at various stages of pickup/delivery
- Chassis turnaround time: ~4 hours (gate-in + yard ops + gate-out + depot drop-off)
- Earliest chassis available: 0200 tomorrow (after demurrage has already started)

Options:
1. **Extend free time:** Contact shipping line for 1-day extension (may not be granted, fee ~$50–$100)
2. **Asset pool via OptETruck:** Request chassis from partner haulier (OptETruck asset pooling) — but partner has 60% utilisation, only 4 chassis available
3. **Emergency chassis rental:** Contact depot for emergency chassis (premium rate ~$200/day)
4. **Accept demurrage:** Let clock run, pass cost to consignee (~$150/day)

OptETruck attempts cross-haulier matching but asset pooling requires real-time visibility of partner chassis availability — data may be stale by 15–30 minutes. The decision window is 6 hours before free time expiry.

**Cost impact:**
- Demurrage: ~$150/day × 1–3 days = ~$150–$450
- Emergency chassis rental: ~$200/day × 1 day = ~$200
- OptETruck asset pool coordination: ~$0 (platform cost) but ~2 hr planner time
- Customer relationship: demurrage passed to consignee, potential dispute
- Carbon: additional truck trip if emergency rental used

**Research grounding:**
- Demurrage/detention tracking: `gate-haulage.md:282-297`
- OptETruck asset pooling: `gate-haulage.md:138-152`
- SmartBooking slot management: `gate-haulage.md:165-178`
- Known friction: demurrage/detention disputes, OptETruck adoption gaps: `gate-haulage.md:359-363`

---

# Sector D: Multimodal Logistics & Supply Chain Adjacencies

## D1: Sea-to-Air Transhipment Flight Cut-Off Threat

**Trigger:** Vessel berthing delay jeopardises a tight 12-hour transfer window to Changi Airport for scheduled flight departure; requires priority discharge, express customs clearance, and airline flight rebooking.

**Systems involved:** OptEModal (sea-air platform) → CITOS (terminal ops) → CALISTA (milestone tracking) → TradeNet (customs) → SATS/dnata (ground handling) → airline.

**Scenario:**  
A vessel carrying 50 sea-air containers (electronics components for Samsung, valued at ~$2M) arrives at 0600, 8 hours late. The cargo must reach Changi Airfreight Centre and clear customs by 1800 for a 2000 departure on Singapore Airlines cargo flight SQ7890. Timeline:

| Time | Activity | Status |
|------|----------|--------|
| 0600 | Vessel arrives | 8 hr late |
| 0600–0800 | QC discharge (50 containers) | Must complete by 0800 |
| 0800–0830 | AGV to yard + aRMG pickup | Must complete by 0830 |
| 0830–0900 | ITT truck dispatch to Changi | Must depart by 0900 |
| 0900–1000 | Transit to Changi (35 km via AYE) | Must arrive by 1000 |
| 1000–1200 | Airside customs clearance | Must clear by 1200 |
| 1200–1800 | SATS handling + cargo acceptance | Must accept by 1800 |
| 2000 | Flight departure | Hard deadline |

OptEModal AI detects the risk and recommends:
1. **Priority discharge:** Request CITOS to assign 6 QCs (instead of 4) to accelerate discharge
2. **Express customs:** Pre-lodge TradeNet clearance while cargo is in transit
3. **Express ITT:** Dispatch dedicated prime movers (not shared ITT pool)
4. **Flight rebooking:** If 12-hr window cannot be met, OptEModal suggests alternative flights (next day 0800, or competitor flights at 2200)

But each option requires multi-party coordination: terminal ops, customs, trucking, ground handling, airline. No single system has authority to expedite all steps.

**Cost impact:**
- Flight rebooking: ~$5,000–$15,000 (cargo rebooking fee)
- Customer SLA breach: ~$10,000–$50,000 (electronics manufacturing delay)
- Priority discharge premium: ~$2,000–$5,000
- SATS handling expedite: ~$1,000–$3,000
- Carbon: additional flight or extended trucking

**Research grounding:**
- OptEModal platform (24-hr transfer target): `multimodal-logistics.md:119-134`
- Changi Airfreight Centre operations: `multimodal-logistics.md:142-157`
- PSA-SATS partnership: `multimodal-logistics.md:159-165`
- Known friction: sea-air transfer timing, multi-party coordination: `multimodal-logistics.md:396-404`
- Decision flow — vessel delay path: `critical-flows.md:460-467`

---

## D2: Cross-Border Customs / Regulatory Inspection Hold

**Trigger:** Singapore Customs or phytosanitary agency places an unexpected inspection hold on multimodal cargo mid-transit; requires multi-party notification and partial manifest release.

**Systems involved:** TradeNet (customs) → CALISTA (milestone tracking) → OptEModal (transfer coordination) → SATS/dnata (airside) → forwarder/shipper.

**Scenario:**  
Sea-air cargo (pharmaceutical raw materials from India, transhipped via Singapore) is in transit from PSA terminal to Changi Airfreight Centre. At 1100, TradeNet flags the shipment for phytosanitary inspection — random selection triggered by HS code classification (plant-derived compound).

The inspection hold means:
1. Cargo cannot proceed past Changi FTZ "In" gate
2. SATS has already allocated cargo acceptance slot for 1400
3. Airline has cargo space booked for 1600 departure
4. Inspector is available at 1500 (earliest)

CALISTA milestone tracker shows the hold to all parties. OptEModal recalculates:
- If inspection clears by 1600: cargo makes 1600 flight (tight but possible)
- If inspection clears by 1800: cargo misses 1600, next available flight is 2200 (6-hr delay)
- If inspection requires lab testing: cargo delayed 24–48 hrs

The forwarder must provide additional documentation (certificate of origin, phytosanitary certificate from origin country). But the document is with the shipper in Mumbai — email/WhatsApp coordination across time zones.

**Cost impact:**
- Flight delay: ~$3,000–$8,000 (rebooking + demurrage)
- Cargo hold: ~$500–$1,000/day (storage at Changi FTZ)
- Customer impact: manufacturing line delay ~$10,000–$50,000/day (pharma)
- Inspection fee: ~$200–$500
- Documentation coordination: ~2–4 hr staff time

**Research grounding:**
- TradeNet (16 agency forms, single window): `multimodal-logistics.md:256-266`
- Regulatory hold management: `multimodal-logistics.md:284-296`
- CALISTA milestone tracking: `multimodal-logistics.md:301-320`
- Known friction: customs clearance delays, inter-modal documentation: `multimodal-logistics.md:398-400`

---

## D3: Cold-Chain Pharma Discrepancy at Regional Distribution Hub

**Trigger:** Temperature logger mismatch during container devanning at PSA Supply Chain Hub @ Tuas (PSCH); requires coordination between forwarder, insurer, and terminal.

**Systems involved:** Roambee (sensor data) → PSA BDP Temp Guard (cold chain) → CALISTA (milestone tracking) → PSCH warehouse ops → shipping line → insurer.

**Scenario:**  
A reefer container (MSCU7890123) carrying temperature-sensitive pharmaceuticals arrives at PSCH for devanning and regional distribution. During unloading:

1. **Physical temperature logger** (placed inside container at origin): Shows temperature exceeded 8°C threshold for 3 hours during transit
2. **Digital telematics** (ONE reefer fleet, installed device): Shows temperature remained at 2–8°C throughout transit
3. **Roambee sensor** (placed at PSCH intake): Confirms current temperature is 4°C (within range)

The discrepancy creates a dispute:
- Forwarder claims cargo is fine (telematics data shows compliance)
- Consignee demands physical logger data be honoured (shows excursion)
- Insurer requires third-party verification before coverage decision
- PSA BDP Temp Guard flags the discrepancy in the control tower dashboard

Resolution requires:
1. Cross-reference Roambee historical data (item-level tracking) with telematics
2. Verify physical logger calibration certificate
3. Obtain lab analysis of cargo (if required by consignee)
4. Multi-party decision: accept cargo, reject cargo, or partial acceptance with discount
5. Update CALISTA milestone with exception status

**Cost impact:**
- Cargo hold: ~$2,000–$5,000/day (pharmaceuticals in cold storage)
- Lab testing: ~$1,000–$3,000
- Insurance claim processing: ~$5,000–$15,000
- Customer impact: supply chain disruption ~$10,000–$100,000/day (pharma)
- Cargo degradation: if excursion confirmed, potential total loss (~$500,000–$2M)

**Research grounding:**
- Roambee partnership (70% better ETA, 90%+ cold chain compliance): `multimodal-logistics.md:338-349`
- PSA BDP Temp Guard: `baseline-systems.md:561-564`
- CALISTA milestone tracking: `multimodal-logistics.md:301-320`
- Known friction: temperature-sensitive cargo handling, real-time data integration: `multimodal-logistics.md:401-403`

---

## D4: Multi-Party ITT Coordination Failure (Cross-Terminal)

**Trigger:** Priority transhipment containers must move from Pasir Panjang to Tuas during peak road traffic; coordination breakdown between road ITT, sea ITT, and yard operations at both terminals.

**Systems involved:** CITOS (both terminals) → OptETruck (road ITT) → feeder vessels (sea ITT) → PORTNET (inventory tracking) → gate operations.

**Scenario:**  
120 transhipment containers at Pasir Panjang Terminal (PPT) must reach Tuas Port for loading on a vessel departing at 2000. Current time: 1000. Transfer options:

**Road ITT:**
- 20 prime movers available; under LTA road regulations, each carries 1x 40ft (FEU) or 2x 20ft (TEU) containers (max 20–40 containers per wave)
- Transit time PPT → Tuas: 45–90 min (depending on AYE traffic)
- 2 trips possible before 1800 cut-off
- But: AYE peak congestion 1700–1900, second trip may not make it

**Sea ITT (feeder vessel):**
- Feeder vessel available at 1400, capacity 200 TEU
- Transit time: ~2 hours
- But: feeder must also load other cargo, departure may slip to 1600
- Arrives Tuas at 1800 — tight for 2000 vessel departure

**Coordination failure:**
- Road ITT: OptETruck dispatches 15 trucks, but 5 are stuck at PPT gate (gate congestion)
- Sea ITT: Feeder vessel delayed 1 hour (berth conflict at PPT)
- Yard at Tuas: Tuas yard planner expects containers at 1600 (road ITT) — but sea ITT delivers at 1800
- QC loading sequence must be re-planned

Decision required: prioritise road ITT (risk: traffic delay) or sea ITT (risk: feeder delay)?

**Cost impact:**
- Vessel delay: ~$3,000–$5,000/hr × 2 hr = ~$6,000–$10,000
- Road ITT cost: ~$100–$200/trip × 20 trucks × 2 trips = ~$4,000–$8,000
- Sea ITT cost: ~$5,000–$10,000 (feeder charter)
- Yard re-handling: ~$30–$50/move × 20 re-handles = ~$600–$1,000
- Customer SLA: missed connections at destination port

**Research grounding:**
- ITT operations (road + sea): `container-yard-transport.md:400-420`
- Known friction: inter-terminal transfer delays: `container-yard-transport.md:433`
- Autonomous feeder EOI: `berth-marine.md:237-242`
- Decision flow — ITT coordination: `gate-haulage.md:247-253`

---

## Summary Statistics

| Sector | Scenarios | Min per Sector | ✓ Met |
|--------|-----------|---------------|-------|
| Berth & Marine | 4 (A1–A4) | 3 | ✅ |
| Yard & Transport | 4 (B1–B4) | 3 | ✅ |
| Gate & Haulage | 4 (C1–C4) | 3 | ✅ |
| Multimodal | 4 (D1–D4) | 3 | ✅ |
| **Total** | **16** | **12** | **✅** |

## Acceptance Criteria Verification

- [x] **Minimum 12 scenarios:** 16 cataloged ✅
- [x] **At least 3 per sector:** 4 per sector ✅
- [x] **Every scenario identifies data/event source:** All grounded in Phase 1 research ✅
- [x] **Every scenario involves 2+ interacting entities:** All involve cross-system handoffs ✅
- [x] **Excludes out-of-scope/pre-solved problems:** No microsecond AGV pathing, standard barcode scans ✅

---

## Sources

All scenarios are grounded in the following Phase 1 research files:
- `research/sectors/berth-marine.md`
- `research/sectors/container-yard-transport.md`
- `research/sectors/gate-haulage.md`
- `research/sectors/multimodal-logistics.md`
- `research/systems/baseline-systems.md`
- `research/flows/critical-flows.md`
