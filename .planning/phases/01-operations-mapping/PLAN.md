# Phase 1: Broad PSA Singapore Operations & Systems Mapping — PLAN

**Created:** 2026-08-17
**Status:** ✅ COMPLETE (2026-08-17)
**Depends on:** Nothing (first phase)
**Requirements:** P1-01, P1-02, P1-03

## Goal

Build a clear technical understanding of PSA Singapore's operations and existing digital infrastructure across all 4 core sectors and 7 baseline systems, with Physical/Information/Decision flows documented per sector.

## Tasks

### 01-01: Research the 4 Operational Sectors

Research each sector's operations, equipment, workflows, and pain points.

**Deliverable:** `deliverables/01-01-sector-research.md` — 4 sector profiles with topic-level detail

**Research fields per sector:**

#### Berth & Marine Operations
- [ ] Vessel traffic management and arrival sequencing (MPA coordination, Straits of Malacca approach)
- [ ] Dynamic berth allocation and quay optimization (vessel draft, tidal windows, LOA, crane split allocation)
- [ ] Marine services synchronization (pilotage, tugboat dispatch, mooring/unmooring, bunkering, crew/provisioning windows)
- [ ] Quay Crane (QC / dual-trolley) loading and discharge sequencing
- [ ] Vessel stowage planning, stability/trim constraints, hazardous cargo onboard segregation
- [ ] Transhipment connection scheduling (mother vessel to feeder vessel transfer windows and cut-off deadlines)

#### Container Yard & Internal Transport
- [ ] AGV fleet management, dynamic routing, traffic deadlock resolution, battery charging optimization
- [ ] aRMG / aYGC job sequencing and yard block load balancing
- [ ] Container stacking optimization (transhipment clustering, import/export separation, minimizing re-handles)
- [ ] Reefer telemetry monitoring, power connection management, temperature excursions, alert triage
- [ ] DG yard storage compliance, IMDG class physical segregation rules, emergency containment protocols
- [ ] Empty container depot management, M&R routing, repositioning flows

#### Gate & External Haulage Operations
- [ ] AGS, OCR, weighbridge validation, haulier mobile authentication
- [ ] Haulier booking and time-slot scheduling (OptETruck integration, dynamic slot quota adjustment)
- [ ] External prime mover TRT time optimization and gate-to-yard buffer queue management
- [ ] ITT balancing (dedicated haulier and barge dispatching between Pasir Panjang Terminal and Tuas Mega Port)
- [ ] Empty container return logistics, drop-and-hook operations, demurrage/detention tracking

#### Multimodal Logistics & Supply Chain Adjacencies
- [ ] Sea-to-air multimodal transfers (OptEModal orchestration between PSA Singapore terminals and Changi Airfreight Centre)
- [ ] Port-adjacent warehousing and distribution (PSCH, Keppel Distripark, regional distribution centers)
- [ ] Regulatory and customs compliance clearance (TradeNet, Singapore Customs, MPA, phytosanitary/security inspection holds)
- [ ] End-to-end cargo visibility and milestone event tracking (CALISTA, BoxVoyant data ingestion)
- [ ] Shipper/Forwarder exception handling (manifest discrepancies, late cargo release orders, bill of lading mismatches)

**Acceptance:**
- [x] All 4 sectors documented with every research field above covered ✅
- [x] Each field has a concise summary of how it works today, who/what is involved, and known friction points ✅

---

### 01-02: Map the 7 Baseline Digital Systems

Research each system's capabilities, integrations, data flows, and limitations.

**Deliverable:** `deliverables/01-02-baseline-systems.md` — 7 system profiles

**Research fields per system:**

- [ ] **CITOS® (Computer Integrated Terminal Operations System)**
  - Core capabilities (TOS functions: berth allocation, QC scheduling, aRMG sequencing, AGV dispatch, stowage)
  - Data inputs and outputs
  - Integration points with other systems
  - Known limitations or manual workarounds

- [ ] **PORTNET®**
  - Core capabilities (B2B port community platform, EDI messaging, customs clearances)
  - Stakeholder integrations (shipping lines, freight forwarders, hauliers, government agencies)
  - Data flow patterns
  - Known limitations

- [ ] **OptETruck**
  - Core capabilities (TMS, job scheduling, route optimization, asset pooling)
  - Integration with CITOS/PORTNET
  - Trucking ecosystem coverage
  - Known limitations

- [ ] **SmartBooking™ & iBOX™**
  - Core capabilities (depot-terminal exchange, appointment booking, gate queue visibility)
  - CDAS integration
  - Depot network coverage
  - Known limitations

- [ ] **OptEModal**
  - Core capabilities (sea-air intermodal, ETA predictions, flight rebooking)
  - CCN integration
  - Changi Airfreight Centre linkage
  - Known limitations

- [ ] **CALISTA® & CALISTA P!NG™**
  - Core capabilities (supply chain orchestration, milestone tracking, cross-border customs)
  - CrimsonLogic/GeTS integration
  - Trade corridor coverage
  - Known limitations

- [ ] **PSA BDP Enterprise Solutions**
  - Core capabilities (control tower, cold-chain, chemical/hazardous logistics)
  - PSA Cargo Solutions + BDP International unification
  - Specialized cargo handling
  - Known limitations

**Acceptance:**
- [x] All 7 systems documented with capabilities, integrations, and limitations ✅
- [x] Cross-system integration map showing which systems talk to each other ✅

---

### 01-03: Document the 3 Critical Flows Per Sector

For each of the 4 sectors, document Physical, Information, and Decision flows.

**Deliverable:** `deliverables/01-03-critical-flows.md` — 4 sectors × 3 flows = 12 flow descriptions

**Research fields per sector:**

- [ ] **Physical Flow:** How containers, ships, cranes, and trucks physically move
- [ ] **Information Flow:** What EDI messages, API calls, sensor alerts, and emails are sent at each step
- [ ] **Decision Flow:** Who or what system decides what happens when schedules are met versus when delays occur

**Acceptance:**
- [x] All 4 sectors have Physical, Information, and Decision flows documented ✅
- [x] Each flow identifies the systems, actors, and handoff points involved ✅

---

## Deliverables Summary

| Task | Deliverable | Output |
|------|-------------|--------|
| 01-01 | `deliverables/01-01-sector-research.md` | 4 sector profiles |
| 01-02 | `deliverables/01-02-baseline-systems.md` | 7 system profiles + integration map |
| 01-03 | `deliverables/01-03-critical-flows.md` | 12 flow descriptions |

## Success Criteria

1. All 4 operational sectors documented with every research field covered
2. All 7 baseline systems mapped with capabilities, integrations, and limitations
3. Physical, Information, and Decision flows documented for each sector
4. A unified operations landscape exists as the foundation for Phase 2 disruption mining
5. Cross-system integration map shows which systems connect to each other

## Exit Gate

Phase 1 is complete when:
- [x] All 3 deliverables exist in `research/` ✅
- [x] Every checkbox in every task is checked ✅
- [x] The team can reference any sector, system, or flow by name and find its documentation ✅
