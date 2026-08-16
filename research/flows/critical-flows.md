# Critical Flows Per Sector — PSA Singapore

**Status:** Synthesis complete
**Last updated:** 2026-08-17
**Sources:** Synthesised from `research/sectors/` and `research/systems/` files

---

## How to Read These Flows

Each sector documents three flow types:

| Flow Type | What It Tracks |
|-----------|---------------|
| **Physical Flow** | Movement of containers, vessels, trucks, cranes, equipment |
| **Information Flow** | EDI messages, API calls, sensor alerts, system-to-system data |
| **Decision Flow** | Who/what decides, triggers, fallbacks, and escalation paths |

**Legend:**
```
──►  Physical movement
→→→  Information/data flow
===> Decision pathway
[SYS] System name
{ACT} Actor/role
```

---

# 1. Berth & Marine Operations

## Physical Flow — Vessel Arrival to Departure

```
Open Sea ──► Anchorage (13 nautical miles) ──► VTIS Clearance ──► Pilot Station ──► Berth
    │              │              │              │              │
    │         Waiting        STRAITREP      Pilot Boarding   Mooring
    │         (hours-days)   (mandatory)    (Tanjong Pilar)  (lines secured)
    │
    │  [CRANE OPERATIONS AT BERTH]
    │  QC Discharge ──► AGV to Yard ──► aRMG Stacking
    │  Yard ──► AGV to QC ──► QC Loading
    │  DTQC Operations (dual-trolley)
    │
    │  [MARINE SERVICES DURING BERTH]
    │  Bunkering (shell bowser)
    │  Provisions & crew changes
    │  Fresh water supply
    │
    ▼
Undocking ──► Pilot Station ──► Open Sea / Next Port
```

**Duration Benchmarks:**
| Phase | Typical Duration |
|-------|-----------------|
| Pilot boarding to berth | 45 min–2 hrs (port-dependent) |
| Quay-side operations (berth time) | 3–5 days |
| Pilot boarding to berth (Sines) | 45 min |
| Pilot boarding to berth (Durban) | 2–3 hrs |

**Key Systems:** VTIS (MPA), OptEVoyage, CITOS (berth allocation), AWP (BerthMaster), Pilot Management System

---

## Information Flow — Vessel Arrival Coordination

```
{Master/Agent} ──→→→ [digitalPORT@SG] ──→→→ [MPA/VTIS]
     │  48-hr Prior     e-arrival form         │
     │  ETA update                             │
     │                                         │
     ├─→→→ [STRAITREP] ──→→→ [MPA] ──→→→ [Port Operations]
     │     24-hr, 12-hr,                       │
     │     6-hr, 3-hr updates                  │
     │                                         │
     ├─→→→ [PORTNET] ──→→→ [Shipping Line]
     │     Vessel call notice                  │
     │                                         │
     ├─→→→ [CITOS] ──→→→ [Berth Allocation]
     │     Vessel particulars                  │
     │     (draft, LOA, cargo manifest)        │
     │                                         │
     └─→→→ [OptEVoyage] ──→→→ [Pilot Services]
           ETA predictions                     Scheduling
           (AIS data)
```

**Critical Messages:**
| Message | Standard | When | Purpose |
|---------|----------|------|---------|
| arrival notification | EDIFACT IFTMIN | 48 hrs before ETA | Pre-arrival clearance |
| STRAITREP | IMO A.600(15) | 24/12/6/3 hrs before | Security, navigation, ETA |
| pre-arrival declaration | Singapore Customs | 24 hrs before | Customs clearance |
| eManifest submission | PORTNET | Per sailing schedule | Cargo documentation |
| berth application | AWP (BerthMaster) | Via agent/operator | Dynamic allocation request |

---

## Decision Flow — Berth Allocation & Disruption Response

```
NOMINAL PATH:
[Vessel Arrival] ===> [Berth Allocation] ===> [Crane Split Decision] ===> [Yard Block Assignment]
                           │                          │                        │
                      CITOS AI/ML              QC Scheduler               Yard Planner
                      + AWP/BerthMaster        + Terminal Planner          + TBA Logic
                      (automated)              (semi-automated)           (automated)

DISRUPTION PATH:
[Vessel Delay] ===> [Re-optimise Berth] ===> [Reassign Cranes] ===> [Update Yard Plan]
                           │                          │                        │
                      CITOS Berth              Re-deploy QC               Adjust stacking
                      Planner                 from other berths          for arrival timing
                      (manual override)       (manual + AI suggest)      (automated)
                           │
                      [Vessel Early] ===> [Find available berth] or [Queue at anchorage]
                                          (CITOS recommendation)
```

**Decision Points:**

| Trigger | Decider | Fallback |
|---------|---------|----------|
| Vessel delay >6 hrs | CITOS Berth Planner (human) | Re-optimise berth allocation |
| Crane breakdown | QC Scheduler (AI suggest) | Redeploy from other berth/yard crane |
| Adverse weather (wind >40 kts) | VTIS (MPA) | Suspend operations, vessel to anchorage |
| Tidal window missed | CITOS + harbour pilot | Vessel waits for next tidal window |
| Vessel early arrival | CITOS (automated) | Queue at anchorage or find available berth |
| Berth congestion | BerthMaster (AWP) + CITOS | Prioritise by berth window, feeder connections |

**Key Friction Points:**
- Berth window mismatches: vessels arrive 6+ hrs late, QC schedules disrupted
- Crane breakdown: 2–4 hr repair, cascading delays across vessels
- Tidal window missed: vessel waits 6+ hrs for next window
- Vessel early arrival: berth occupied, vessel queues at anchorage
- QC efficiency variance: top operators 35+ moves/hr vs. average 28–30 moves/hr

---

# 2. Container Yard & Internal Transport

## Physical Flow — Container Movement Through Yard

```
[QC Discharge] ──► [AGV Transport] ──► [aRMG Stacking] ──► [Yard Block]
                                        │
                                        ├── Transhipment Block (clustered by vessel)
                                        ├── Import Block (by ship/consignee)
                                        ├── Export Block (by ship/booking)
                                        └── Reefer Block (power connected, 10K+)

[Export Staging] ──► [AGV Transport] ──► [QC Loading]
                                        │
                                        ├── Transhipment (feeder-to-mother connection)
                                        └── Export (direct vessel load)

[DG Containers] ──► [DG Yard] ──► [Segregated Storage]
                                   │
                                   ├── IMDG class separation
                                   ├── Emergency containment
                                   └── HAZMAT protocols

[Reefer Containers] ──► [Reefer Yard] ──► [ARMS Monitoring]
                                           │
                                           ├── Power connection
                                           ├── Temperature monitoring
                                           └── Alert triage
```

**Equipment Scale (Tuas Mega Port Phase 1):**
| Equipment | Quantity |
|-----------|----------|
| AGVs (Phase 1) | 160 |
| AGVs (Target, all phases) | 2,000 |
| Automated cranes | 21 (8 QC + 6 QC-STS + 3 aYGC + 4 aASC) |
| aRMGs | 208 (ordered from ZPMC) |
| Reefer points | 10,000+ |

**Key Systems:** CITOS (yard planning, AGV dispatch), A*STAR FMS (AGV fleet management), ARMS (reefer monitoring)

---

## Information Flow — Yard Operations Data

```
[AGV] ──→→→ [A*STAR FMS] ──→→→ [CITOS]
     │  Real-time        Fleet status    │
     │  GPS + task status               │
     │                                  │
[Reefer Sensor] ──→→→ [ARMS] ──→→→ [Operations Team]
     │  Temperature, power     Alert     │
     │  status, humidity       engine    │
     │                          │        │
                          [CITOS] ←──→→→ [Operations]
                          Yard status    Manual override
                                         request
[aRMG] ──→→→ [CITOS] ──→→→ [Yard Planner]
     │  Job status     Job completion    │
     │  block ID       update            │
     │                                  │
[QC] ──→→→ [CITOS] ──→→→ [Berth Planner]
     │  Moves count    Crane status      │
     │  per hour       update            │
```

**Critical Messages:**
| Message | Source | Destination | Purpose |
|---------|--------|-------------|---------|
| AGV task assignment | CITOS | A*STAR FMS → AGV | Dispatch AGV to QC/yard |
| Reefer temperature alert | ARMS | Operations + CITOS | Power failure or excursion |
| Yard block status | CITOS | Yard Planner | Block full/almost full |
| Crane moves report | QC | CITOS | Progress against vessel plan |
| DG incident alert | Yard system | Emergency response | Mis-declaration or containment breach |

---

## Decision Flow — Yard Optimisation & Exception Handling

```
NOMINAL PATH:
[Container Discharged] ===> [Yard Block Assignment] ===> [Stacking Position] ===> [AGV Route]
                              │                              │                      │
                         CITOS TBA                    CITOS stacking           A*STAR FMS
                         (automated)                  logic (automated)        (automated)

EXCEPTION PATH:
[Block Full] ===> [Re-assign Block] ===> [Notify Planner] ===> [Manual Override]
                        │                                           │
                   CITOS recommends               Yard Planner decides
                   alternate block                based on operational priority

[AGV Deadlock] ===> [FMS Resolution] ===> [Re-route AGVs] ===> [Resume Operations]
                        │                                           │
                   A*STAR FMS detects            Automatic rerouting
                   traffic jam                   (resolves in <60 sec)

[Reefer Alarm] ===> [ARMS Alert] ===> [Triage] ===> [Dispatch M&R]
                        │                  │                │
                   Auto-detect         Operations        Maintenance
                   power/temp issue    team decides       crew responds
```

**Decision Points:**

| Trigger | Decider | Fallback |
|---------|---------|----------|
| Yard block full | CITOS TBA (automated) | Reassign to alternate block |
| AGV traffic deadlock | A*STAR FMS (automated) | Auto-reroute AGVs (resolves <60 sec) |
| Reefer power failure | ARMS alert → Operations team | Manual power reconnection |
| DG mis-declaration | Yard system + Emergency response | Isolate, contain, report |
| Container blocking access | Yard Planner (human) | Manual re-handle to adjacent position |
| Stacking conflict | CITOS (automated) | Manual override by planner |

**Key Friction Points:**
- Yard block saturation during peak vessel calls (multiple vessels sharing limited blocks)
- AGV traffic congestion at QC land-side pickup points (20+ AGVs queuing)
- Reefer power failures: ARMS detects, but manual M&R dispatch takes 15–30 min
- DG mis-declaration: ~500K+ TEUs of DG annually, incidents require emergency protocols
- Stacking conflicts: high-value containers blocked by low-priority imports

---

# 3. Gate & External Haulage Operations

## Physical Flow — Truck Entry to Exit

```
[Highway] ──► [Expressway (AYE)] ──► [Terminal Approach] ──► [Gate Queue]
                                                              │
                                                         Waiting (minutes-hours)
                                                              │
                                                              ▼
[AGS Check] ──► [OCR Scan] ──► [Weighbridge] ──► [Security] ──► [Yard Access]
     │              │              │              │              │
  Vehicle ID     Container     Weight          Haulier        Container
  verification   number        validation      ID check       pickup/dropoff
                                                              │
                                                              ▼
                                                         [Yard Operations]
                                                              │
                                                         aRMG picks up /
                                                         loads container
                                                              │
                                                              ▼
[Return to Gate] ──► [Exit OCR] ──► [Highway] ──► [Next Job / Depot]
```

**Gate Processing Benchmarks:**
| Metric | Value |
|--------|-------|
| Average processing time (FTG) | 25 seconds |
| Gate capacity (without rehandling) | 700 trucks/hour |
| Peak gate throughput (Tuas) | 10,000+ moves/day |
| Peak gate congestion window | 23:00–01:00 (60% trucks queue) |
| Average empty container rehandling | 30% (10–15 min each) |

**Key Systems:** AGS (Automated Gate System), AI-OCR, weighbridge, biometric auth, OptETruck, SmartBooking, iBOX

---

## Information Flow — Haulage Ecosystem Data

```
{Haulier} ──→→→ [OptETruck] ──→→→ [PORTNET] ──→→→ [CITOS]
     │  Booking     Job scheduling    │  Job confirmation    │
     │  request     + route optim.    │  + gate slot         │
     │                              │                      │
     ├─→→→ [SmartBooking] ──→→→ [iBOX] ──→→→ [CITOS]
     │     Depot booking        Depot ops      Gate integration
     │     + time slot          + container    + yard assignment
     │                          exchange
     │
     ├─→→→ [PORTNET] ──→→→ [Customs] ──→→→ [Singapore Customs]
     │     eManifest          Clearance      │
     │     submission         status         │
     │                                   [Release Order]
     │                                   (automated/checked)
     │
     └─→→→ [OptETruck] ──→→→ [SG-MDH] ──→→→ [Analytics]
           Fleet tracking      Data sharing     │
           + CO2 tracking      hub              [Dashboards]
```

**Critical Messages:**
| Message | Standard | When | Purpose |
|---------|----------|------|---------|
| booking request | OptETruck API | Before gate arrival | Reserve gate slot + yard position |
| gate entry notification | AGS/OCR | At gate | Verify container, weight, haulier |
| release order | PORTNET/CUSTOMS | Before gate entry | Confirm customs clearance |
| truck arrival notification | OptETruck | En route | ETA for yard preparation |
| gate exit confirmation | AGS/OCR | After pickup/dropoff | Complete job cycle |
| empty return notification | iBOX | At depot | Container condition, next assignment |

---

## Decision Flow — Gate Operations & Congestion Management

```
NOMINAL PATH:
[Truck Arrives] ===> [AGS Processing] ===> [Yard Assignment] ===> [aRMG Job] ===> [Truck Departs]
                          │                      │                    │
                     25 seconds            CITOS assigns         Automated
                     (automated)           yard block            dispatch

CONGESTION PATH:
[Peak Hours] ===> [Queue Build-up] ===> [Dynamic Slot Adjustment] ===> [Rebalance]
                        │                       │                         │
                   SmartBooking           OptETruck adjusts          Haulier
                   queue visibility      gate slot allocation       notification

EXCEPTION PATH:
[Container Not Ready] ===> [Hold at Gate] ===> [Notify Haulier] ===> [Rebook Slot]
                              │                     │                     │
                         AGS blocks           iBOX sends alert      SmartBooking
                         gate entry           to haulier phone       rebook
                              │
                         [VGM Non-Compliance] ===> [Reject] ===> [Re-weigh or Correct]
                                                        │
                                                   Customs
                                                   enforcement
```

**Decision Points:**

| Trigger | Decider | Fallback |
|---------|---------|----------|
| Container not ready at gate | AGS (automated) | Hold truck, notify haulier, rebook slot |
| VGM weight discrepancy | Weighbridge + AGS (automated) | Reject entry, require re-weigh or VGM correction |
| Gate congestion (queue >30 min) | OptETruck + Operations | Dynamic slot rebalancing, open overflow lanes |
| Haulier late for slot | SmartBooking (automated) | Reassign slot to next haulier, notify delayed haulier |
| Empty container return | iBOX (automated) | Condition check, route to M&R if damaged |
| Demurrage threshold approaching | PORTNET + OptETruck (automated) | Alert to customs broker, initiate extension request |

**Key Friction Points:**
- Peak gate congestion: 60% of trucks queue between 23:00–01:00, causing 2–4 hr delays
- Empty container rehandling: 30% of containers need re-handling (10–15 min each)
- VGM non-compliance: ~2% of containers fail weight verification on first attempt
- Haulier slot mismatches: late arrivals cause cascading gate delays
- Container not ready: truck arrives but container not available for pickup (miscommunication)

---

# 4. Multimodal Logistics & Supply Chain Adjacencies

## Physical Flow — Sea-Air Intermodal Transfer

```
[Origin Port] ──► [PSA Singapore Terminal] ──► [Intermodal Transfer] ──► [Changi Airfreight Centre] ──► [Air Departure]
      │                    │                         │                           │                         │
   Sea leg             Sea-air hub              Transfer ops              Air-side ops              Air leg
   (vessel)            (PSCH/Keppel)           (truck/barge)            (customs/cargo)           (aircraft)
                                                                      │
                                                                      ▼
                                                                 [Destination]

TIMELINE (OptEModal target):
Vessel Arrival ──► Terminal Ops ──► Transfer ──► Customs ──► Air Departure
  Day 0              Day 0–1          Day 1        Day 1         Day 1
                                          │
                                     24 hours
                                     (target)
```

**Key Transfer Points:**
| Transfer | Distance | Mode | Duration |
|----------|----------|------|----------|
| PSA Terminal → PSCH | ~1 km | Truck (within port) | 15–30 min |
| PSA Terminal → Changi AFC | ~20 km | Truck (via AYE/PIE) | 45–90 min |
| Tuas Port → Changi AFC | ~35 km | Truck (via AYE/PIE) | 60–120 min |

**Key Systems:** OptEModal, CALISTA (milestone tracking), TradeNet (customs), PSA BDP (control tower)

---

## Information Flow — Multimodal Coordination Data

```
{Shipper/Forwarder} ──→→→ [CALISTA] ──→→→ [OptEModal] ──→→→ [Airline/CCN]
     │  Booking            Milestone         ETA prediction     │
     │  request            tracking          + flight recommend  │
     │                                     │                    │
     ├─→→→ [TradeNet] ──→→→ [Singapore Customs] ──→→→ [Release]
     │     eCustoms         Clearance          │
     │     submission       status             │
     │                                      [Airside Customs]
     │                                      (Changi)
     │
     ├─→→→ [PSA BDP] ──→→→ [Control Tower] ──→→→ [Exception Alert]
     │     Smart Suite®     Real-time           │
     │     (Risk Monitor)   visibility          │
     │                          │
     └─→→→ [BoxVoyant] ──→→→ [Data Aggregation] ──→→→ [Analytics]
           IoT data            Multiple            │
           ingestion           sources             [Dashboards]
```

**Critical Messages:**
| Message | Source | Destination | Purpose |
|---------|--------|-------------|---------|
| sea-air booking | Shipper/Forwarder | CALISTA + OptEModal | Reserve transfer slot |
| vessel arrival ETA | OptEModal | Airline + Changi AFC | Coordinate air-side readiness |
| customs clearance (sea side) | TradeNet | PSA Terminal | Release container for transfer |
| customs clearance (air side) | Changi Customs | Airline | Accept cargo for air shipment |
| delay notification | OptEModal | All parties | Rebook flights, adjust schedules |
| milestone update | CALISTA P!NG | Shipper/Forwarder | Track container through intermodal chain |

---

## Decision Flow — Multimodal Exception Handling

```
NOMINAL PATH:
[Vessel Arrives] ===> [OptEModal Transfer Plan] ===> [Truck/Barge Dispatch] ===> [Changi AFC] ===> [Air Departure]
                          │                              │                           │
                     AI ETA prediction              Automated dispatch          Customs clearance
                     + flight recommendation        + real-time tracking        + cargo acceptance

EXCEPTION PATH:
[Vessel Delay >24 hrs] ===> [Rebook Flight] ===> [Notify Forwarder] ===> [Replan Transfer]
                                │                      │                       │
                           OptEModal               CALISTA alert          OptEModal
                           AI suggests             to all parties         recalculates
                           alternatives                                   new schedule
                                │
                           [Short delay] ===> [Adjust truck slot] ===> [No flight change]
                           [<12 hrs]         (SmartBooking)

[Customs Hold] ===> [Investigate] ===> [Resolve/Override] ===> [Continue Transfer]
                        │                    │                      │
                   TradeNet hold        Forwarder/agent       Customs officer
                   code check           provides docs         reviews & releases
```

**Decision Points:**

| Trigger | Decider | Fallback |
|---------|---------|----------|
| Vessel delay >24 hrs | OptEModal AI | Rebook flight, notify all parties |
| Customs hold (sea side) | TradeNet + Customs officer | Forwarder provides additional docs |
| Customs hold (air side) | Changi Customs | Hold cargo, rebook on next available flight |
| Truck breakdown en route | OptETruck + Operations | Dispatch replacement truck |
| Transfer time <12 hrs remaining | OptEModal (automated) | Expedite processing, priority handling |
| Flight cancelled | OptEModal AI | Rebook on next available flight, re-plan transfer |

**Key Friction Points:**
- Vessel delay causing missed air connection: requires flight rebooking (12–48 hr delay)
- Customs hold: additional documentation required, cargo stuck at transfer point
- Transfer time compression: <12 hrs between sea arrival and air departure = high pressure
- Multi-party coordination: 5+ parties must synchronise (forwarder, trucker, terminal, customs, airline)
- Visibility gaps: CALISTA P!NG tracks milestones but not all intermediate steps

---

# Cross-System Integration Map

```
                    ┌──────────┐
                    │ VTIS     │ (MPA — vessel traffic)
                    │ STRAITREP│
                    └────┬─────┘
                         │
┌──────────┐    ┌────────▼─────┐    ┌──────────┐
│ OptEVoyage│───►│    CITOS®    │◄───│  PORTNET® │
│(AIS/ETA)  │    │(TOS core)   │    │(community)│
└──────────┘    └──┬───┬───┬──┘    └─────┬──────┘
                   │   │   │              │
    ┌──────────────┘   │   └──────┬───────┘
    │                  │          │
┌───▼──────┐  ┌───────▼──┐  ┌───▼──────────┐
│A*STAR FMS │  │  ARMS    │  │ OptETruck    │
│(AGV fleet)│  │(reefer)  │  │(TMS/haulage) │
└──────────┘  └──────────┘  └──┬───────┬───┘
                               │       │
                      ┌────────▼──┐ ┌──▼──────────┐
                      │SmartBooking│ │   iBOX™     │
                      │(depot book)│ │(depot ops)  │
                      └───────────┘ └─────────────┘
                                                 
┌──────────┐    ┌──────────┐    ┌──────────┐
│CALISTA®  │◄──►│OptEModal │◄──►│ PSA BDP  │
│(supply   │    │(sea-air) │    │(control  │
│ chain)   │    └──────────┘    │ tower)   │
└────┬─────┘                    └──────────┘
     │
┌────▼──────────┐    ┌──────────┐    ┌──────────┐
│  CALISTA P!NG │    │ TradeNet │    │ SG-MDH   │
│(milestones)   │    │(customs) │    │(data hub)│
└───────────────┘    └──────────┘    └──────────┘
```

**Integration Strength:**
| Connection | Strength | Protocol |
|-----------|----------|----------|
| CITOS ↔ A*STAR FMS | Strong (real-time) | Proprietary API |
| CITOS ↔ PORTNET | Strong | EDIFACT/XML/JSON |
| OptETruck ↔ SmartBooking | Strong (integrated) | API |
| CALISTA ↔ TradeNet | Strong | API + EDI |
| OptEModal ↔ CALISTA | Strong | API |
| PSA BDP ↔ Snowflake | Strong | Cloud data pipeline |
| VTIS ↔ CITOS | Medium | EDI |
| SG-MDH ↔ All systems | Medium | API (data sharing) |

**Key Gaps:**
- Empty container tracking across depots (partial — no real-time view)
- Cross-terminal optimisation (Pasir Panjang ↔ Tuas — not yet live)
- Haulier fleet real-time visibility (OptETruck limited to participating fleets)
- Real-time yard block status sharing with external planners

---

## Sources

| Source | Used For | Verification |
|--------|----------|-------------|
| PSA Annual Reports 2023–2025 | All flows | ✅ Verified |
| PSA Port Innovation Reports | Berth ops, yard ops | ✅ Verified |
| OptEVoyage documentation | Vessel information flow | ✅ Verified |
| A*STAR press releases | AGV fleet management | ✅ Verified |
| SmartBooking press releases | Gate operations | ✅ Verified |
| OptETruck press releases | Haulage operations | ✅ Verified |
| OptEModal press releases | Multimodal flows | ✅ Verified |
| CALISTA/GeTS documentation | Supply chain flows | ✅ Verified |
| PSA BDP documentation | Control tower flows | ✅ Verified |
| World Bank LPI 2023 | Flow benchmarks | ✅ Verified |
