# Master Problem Charter: Multi-Party ITT Coordination Failure (Cross-Terminal)

**Status:** Locked  
**Flagship Problem:** PB-12  
**Parent Cluster:** C2 — Manual Multi-Party Coordination  
**Last updated:** 2026-08-19

---

## 1. Executive Summary & Operational Context

- **Sector:** Multimodal Logistics & Supply Chain Adjacencies
- **Target User Persona:** PSA ITT Operations Controller (Pasir Panjang Terminal)
- **Parent Cluster:** C2 — Manual Multi-Party Coordination (7 passing problems, ~$316K/month aggregate)
- **Operational Problem Statement:** When 120+ priority transhipment containers must move from Pasir Panjang Terminal (PPT) to Tuas Port via road or sea ITT during peak traffic, coordination breaks down across road ITT (OptETruck), sea ITT (feeder vessels), yard operations (separate CITOS instances at PPT and Tuas), and gate operations. PPT and Tuas CITOS are not integrated — container availability at PPT is invisible to Tuas yard planners in real-time (PORTNET updates delayed 30–60 min). The ITT split between road and sea modes is negotiated via phone calls between PPT planner, Tuas planner, and feeder operator — no system optimises the split. The result: suboptimal transport mode allocation, missed feeder connections, vessel loading delays at Tuas, and $15,600–$29,000 per incident in combined costs.
- **Selected Autonomy Level:** Tier 2 — Human-in-the-Loop (HITL) Exception Solver

---

## 2. As-Is vs. To-Be Workflow Comparison

### As-Is Baseline (Current Manual Process)

| Step | Actor | System/Channel | Action | Time |
|------|-------|---------------|--------|------|
| 1 | PPT Yard Planner | CITOS (PPT) | Identifies 120 containers ready for ITT | T+0 |
| 2 | PPT Yard Planner | Phone | Calls Tuas yard planner to discuss receiving capacity | T+5 min |
| 3 | Tuas Yard Planner | Phone | Confirms yard blocks available, suggests 60/40 road/sea split | T+15 min |
| 4 | PPT Yard Planner | Phone | Contacts OptETruck to dispatch 15 trucks | T+20 min |
| 5 | OptETruck | Auto-dispatch | Dispatches trucks (but PPT gate congestion delays 5 trucks) | T+25 min |
| 6 | PPT Yard Planner | Phone | Contacts feeder vessel operator to confirm 1400 departure | T+30 min |
| 7 | Feeder Operator | Phone | Reports berth conflict — departure delayed to 1600 | T+35 min |
| 8 | Tuas Yard Planner | Phone (from PPT planner) | Learns of feeder delay | T+40 min |
| 9 | Tuas Yard Planner | CITOS (Tuas) | Re-sequences QC loading for delayed sea ITT containers | T+50 min |
| 10 | Road ITT arrives | OptETruck GPS | 10 trucks arrive at Tuas — 60 containers processed | T+3 hrs |
| 11 | Sea ITT arrives | Feeder vessel | Feeder arrives at Tuas — 60 containers processed | T+6 hrs |
| 12 | QC Loading | CITOS (Tuas) | Vessel loading delayed 2 hrs waiting for sea ITT containers | T+8 hrs |

**Total resolution time:** 4–8 hours  
**Coordination channels:** Phone calls between 5 parties, no system of record  
**Key failure:** Feeder delay discovered at T+35 min — by then, road ITT trucks are already dispatched and cannot be re-routed

### To-Be Agentic Workflow

| Step | Actor | System | Action | Time |
|------|-------|--------|--------|------|
| 1 | Agent | CITOS (PPT) | Receives container readiness event (webhook) | T+0 |
| 2 | Agent | CITOS (PPT) | Queries PPT yard status — 120 containers confirmed ready | T+0.5 min |
| 3 | Agent | OptETruck | Queries road ITT capacity — 20 trucks available, 90 min transit | T+1 min |
| 4 | Agent | PORTNET | Queries feeder status — berth available, departure window 1400–1600 | T+1.5 min |
| 5 | Agent | PORTNET | Queries downstream port tidal window — feeder must depart by 1530 | T+2 min |
| 6 | Agent | Internal | Computes optimal split: 80 road (60 trips: $9,000) / 40 sea ($1,400 handling) (total: $10,400 vs $12,000 baseline) | T+2.5 min |
| 7 | Agent | HITL Gate | Presents approval card to ITT coordinator | T+3 min |
| 8 | ITT Coordinator | HITL Card | Reviews cost analysis, approves split | T+5 min |
| 9 | Agent | OptETruck | Dispatches initial wave of 16 trucks via "PPT -> West Coast Highway -> AYE -> Tuas Port Boulevard" | T+5.5 min |
| 10 | Agent | PORTNET | Sends feeder hold request (1 hr) with cost analysis | T+6 min |
| 11 | Agent | CITOS (Tuas) | Updates Tuas yard planner with expected ITT arrival times | T+6.5 min |
| 12 | Agent | PORTNET | Monitors feeder status — detects berth conflict at T+15 min | T+21 min |
| 13 | Agent | Internal | Re-computes split: 100 road / 20 sea (feeder delayed) | T+22 min |
| 14 | Agent | HITL Gate | Presents emergency re-split to ITT coordinator | T+23 min |
| 15 | ITT Coordinator | HITL Card | Approves emergency re-split | T+25 min |
| 16 | Agent | OptETruck | Dispatches 4 additional trucks | T+26 min |
| 17 | Agent | CITOS (Tuas) | Updates loading sequence for adjusted arrival times | T+27 min |

**Total resolution time:** 27 minutes (vs. 4–8 hours)  
**Coordination channels:** Agent handles 5 system queries + 2 HITL approvals (vs. 12+ phone calls)  
**Key improvement:** Feeder conflict detected at T+21 min — trucks re-routed before road ITT fully dispatched

---

## 3. Mock API Toolset Specification

### Tool 1: `get_itt_candidates`

```python
def get_itt_candidates(
    cit_ppt_endpoint: str,
    vessel_id: str
) -> dict:
    """
    Query PPT CITOS for containers requiring cross-terminal transfer to Tuas.
    Returns container list with yard block, weight, DG class, and priority.
    """
    # Sample Output:
    {
        "status": "success",
        "vessel_id": "MV SOPHIA",
        "tuas_departure": "2026-08-19T20:00:00+08:00",
        "total_containers": 120,
        "total_teu": 160,
        "container_breakdown": {
            "40ft_feu": 40,
            "20ft_teu": 80
        },
        "lta_truck_trip_requirement": {
            "40ft_feu_trips": 40,
            "20ft_teu_trips": 40,
            "total_potential_truck_trips_100pct_road": 80
        },
        "containers": [
            {
                "container_id": "MSKU7654321",
                "size": "40ft",
                "yard_block": "B-07",
                "yard_position": "Bay 14 Row 02 Tier 03",
                "weight_kg": 28500,
                "dg_class": null,
                "priority": "high",
                "consignee": "DB Schenker",
                "destination_port": "LA",
                "ready_for_itt": true
            },
            {
                "container_id": "TCLU1234567",
                "size": "20ft",
                "yard_block": "B-12",
                "yard_position": "Bay 08 Row 05 Tier 01",
                "weight_kg": 15200,
                "dg_class": null,
                "priority": "standard",
                "consignee": "Kuehne+Nagel",
                "destination_port": "Rotterdam",
                "ready_for_itt": true
            }
        ],
        "blocks_affected": ["B-07", "B-08", "B-12", "B-14"],
        "dg_containers": 3,
        "reefer_containers": 0
    }
```

### Tool 2: `check_road_itt_capacity`

```python
def check_road_itt_capacity(
    optetruck_endpoint: str,
    terminal: str,
    time_window_start: str,
    time_window_end: str
) -> dict:
    """
    Query OptETruck for available trucks, transit time, and road conditions
    for road ITT from PPT to Tuas.
    """
    # Sample Output:
    {
        "status": "success",
        "terminal": "PPT",
        "available_trucks": 20,
        "transit_time_minutes": 90,
        "road_conditions": {
            "AYE": "normal",
            "West_Coast_Highway": "moderate_traffic_near_pandan",
            "Tuas_Port_Boulevard": "clear"
        },
        "cost_per_trip": 150,
        "lta_chassis_limits": "1x 40ft/45ft (FEU) OR up to 2x 20ft (TEU) per prime mover",
        "estimated_round_trip_minutes": 210,
        "baseline_trips_all_120_containers": 80,
        "baseline_road_cost_all_120": 12000,
        "split_road_containers_spec": "40x 40ft (40 trips) + 40x 20ft (20 trips) = 80 containers (60 trips)",
        "trips_needed_for_80_road_split": 60,
        "estimated_road_cost_80_split": 9000,
        "earliest_departure": "2026-08-19T11:00:00+08:00",
        "latest_arrival_at_tuas": "2026-08-19T18:00:00+08:00"
    }
```

### Tool 3: `check_sea_itt_capacity`

```python
def check_sea_itt_capacity(
    portnet_endpoint: str,
    feeder_id: str,
    current_time: str
) -> dict:
    """
    Query PORTNET for feeder vessel availability, berth status, and departure window.
    Includes downstream port constraints (tidal windows, connection deadlines).
    """
    # Sample Output:
    {
        "status": "success",
        "feeder_id": "FEEDER ATLANTIC-03",
        "feeder_operator": " PIL Shipping",
        "vessel_type": "Feeder",
        "capacity_teu": 800,
        "current_occupancy_teu": 620,
        "available_capacity_teu": 180,
        "berth_status": "berthed_at_PPT_B12",
        "departure_window": {
            "earliest": "2026-08-19T14:00:00+08:00",
            "latest": "2026-08-19T16:00:00+08:00",
            "requested": "2026-08-19T14:00:00+08:00"
        },
        "downstream_constraints": {
            "destination_port": "Port Klang",
            "tidal_window": "2026-08-19T23:00:00+08:00",
            "transit_time_hours": 18,
            "must_depart_by": "2026-08-19T05:00:00+08:00",
            "buffer_hours": 1.0
        },
        "hold_cost_per_hour": 800,
        "missed_connection_cost": 5000
    }
```

### Tool 4: `compute_itt_split`

```python
def compute_itt_split(
    candidates: list,
    road_capacity: dict,
    sea_capacity: dict,
    tuas_vessel_departure: str,
    constraints: dict
) -> dict:
    """
    Run multi-constraint optimisation for road/sea allocation.
    Minimises total cost (transport + demurrage + SLA) subject to:
    - Tuas vessel departure deadline
    - Feeder departure window
    - Road truck availability (LTA 1x 40ft or 2x 20ft per chassis)
    - Yard block capacity at Tuas
    """
    # Sample Output:
    {
        "status": "success",
        "optimal_split": {
            "road_containers": 80,
            "road_breakdown": "40x 40ft (40 trips) + 40x 20ft (20 trips)",
            "road_trips": 60,
            "road_cost": 9000,
            "sea_containers": 40,
            "sea_breakdown": "40x 20ft (40 TEU)",
            "sea_marginal_charter_cost": 0,
            "sea_terminal_handling_cost": 1400,
            "total_transport_cost": 10400,
            "cost_notes": "Sea transfer has $0 marginal charter cost (scheduled feeder rotation) + $1,400 terminal handling ($35/lift across 40 containers); avoids 20 prime mover road trips along West Coast Highway/AYE."
        },
        "alternatives": [
            {
                "road_containers": 100,
                "road_breakdown": "40x 40ft (40 trips) + 60x 20ft (30 trips)",
                "road_trips": 70,
                "road_cost": 10500,
                "sea_containers": 20,
                "sea_marginal_charter_cost": 0,
                "sea_terminal_handling_cost": 700,
                "total_transport_cost": 11200,
                "risk": "road_congestion_delay_near_pandan"
            },
            {
                "road_containers": 60,
                "road_breakdown": "40x 40ft (40 trips) + 20x 20ft (10 trips)",
                "road_trips": 50,
                "road_cost": 7500,
                "sea_containers": 60,
                "sea_marginal_charter_cost": 0,
                "sea_terminal_handling_cost": 2100,
                "total_transport_cost": 9600,
                "risk": "feeder_capacity_exceeded_20TEU"
            }
        ],
        "timeline": {
            "road_itt_arrival": "2026-08-19T14:30:00+08:00",
            "sea_itt_arrival": "2026-08-19T16:30:00+08:00",
            "tuas_loading_start": "2026-08-19T17:00:00+08:00",
            "vessel_departure": "2026-08-19T20:00:00+08:00",
            "margin_minutes": 180
        },
        "cost_vs_baseline": {
            "baseline_all_road_cost": 12000,
            "baseline_all_road_trips": 80,
            "optimised_transport_cost": 10400,
            "direct_transport_savings": 1600,
            "congestion_and_delay_risk_reduction": "High (20 fewer road trips on AYE/West Coast Highway corridor)"
        }
    }
```

### Tool 5: `update_tuas_loading_sequence`

```python
def update_tuas_loading_sequence(
    cit_tuas_endpoint: str,
    vessel_id: str,
    itt_eta_road: str,
    itt_eta_sea: str,
    container_ids_road: list,
    container_ids_sea: list
) -> dict:
    """
    Update Tuas QC loading sequence based on ITT arrival predictions.
    Adjusts bay assignment to match container arrival order.
    """
    # Sample Output:
    {
        "status": "success",
        "vessel_id": "MV PACIFIC STAR",
        "original_loading_sequence": "Bay14→Bay12→Bay10→Bay08",
        "updated_loading_sequence": "Bay14(road@14:30)→Bay12(road@14:30)→Bay10(sea@16:30)→Bay08(sea@16:30)",
        "qc_adjustments": [
            {"qc_id": "QC-07", "original_bay": "Bay14", "new_bay": "Bay14", "eta": "14:30"},
            {"qc_id": "QC-07", "original_bay": "Bay12", "new_bay": "Bay12", "eta": "14:30"},
            {"qc_id": "QC-08", "original_bay": "Bay10", "new_bay": "Bay10", "eta": "16:30"},
            {"qc_id": "QC-08", "original_bay": "Bay08", "new_bay": "Bay08", "eta": "16:30"}
        ],
        "estimated_loading_completion": "2026-08-19T19:30:00+08:00",
        "margin_before_departure_minutes": 30
    }
```

---

## 4. Safety Guardrails, Schema Validation & Injected Failure Scenarios

### Mandatory HITL Gate Card

The agent presents the following approval card at the critical decision point (Tool 4 output — ITT split commit):

```
┌──────────────────────────────────────────────────────────────┐
│  ITT COORDINATION — APPROVAL REQUIRED                        │
├──────────────────────────────────────────────────────────────┤
│  ACTION: Commit ITT split — 80 containers road / 40 sea     │
│  VESSEL: MV PACIFIC STAR — Tuas departure 2000              │
│  DEADLINE: ITT must arrive at Tuas by 1800                  │
├──────────────────────────────────────────────────────────────┤
│  ROAD ITT: 60 trips (40x 40ft + 40x 20ft) × $150 = $9,000  │
│  SEA ITT: 40 containers (40x 20ft) — $0 marginal charter    │
│           + $1,400 terminal handling ($35/move) = $1,400    │
│  TOTAL TRANSPORT COST: $10,400                              │
│  VS BASELINE (all road: 80 trips × $150): $12,000            │
│  DIRECT SAVINGS: $1,600 + avoids AYE peak road congestion   │
├──────────────────────────────────────────────────────────────┤
│  RISK: Feeder departure window closes 1530 — hold max 1 hr  │
│  MARGIN: 3 hrs before vessel departure (Adequate)           │
├──────────────────────────────────────────────────────────────┤
│  [APPROVE]  [MODIFY SPLIT]  [REJECT]                        │
└──────────────────────────────────────────────────────────────┘
```

### Input Validation Guardrails

| Guard | Check | Action on Failure |
|-------|-------|-------------------|
| Container weight bounds | `0 < weight_kg < 60000` | Reject container from ITT candidate list, log warning |
| Yard block capacity | `containers_per_block ≤ block_max_capacity` | Trigger overflow routing before ITT dispatch |
| Truck availability | `available_trucks ≥ 1` | Fall back to 100% sea ITT if road unavailable |
| Feeder capacity | `sea_containers ≤ feeder_available_teu` | Reduce sea allocation, increase road allocation |
| Tuas vessel departure | `itt_arrival < vessel_departure - 60min` | Reject split — insufficient margin |
| Feeder tidal window | `feeder_departure < tidal_window_deadline` | Enforce hold limit in split computation |

### Injected Failure Scenarios

**Scenario A: Feeder Berth Conflict (Demo Edge Case)**

| Timing | Event | Agent Response |
|--------|-------|----------------|
| T+0 | Agent computes 80/40 split | Presents HITL card |
| T+5 min | ITT coordinator approves | Agent dispatches trucks, requests feeder hold |
| T+21 min | PORTNET reports feeder berth conflict — departure delayed to 1600 | Agent detects: feeder will miss downstream tidal window at Port Klang |
| T+22 min | Agent re-computes split: 100 road / 20 sea | Recalculates with feeder constraint |
| T+23 min | Agent presents emergency re-split to ITT coordinator | Shows cost impact: +$1,500 road cost but avoids $5,000 missed connection |
| T+25 min | ITT coordinator approves emergency re-split | Agent dispatches 4 additional trucks |
| T+26 min | Agent updates Tuas loading sequence | Adjusts bay assignments for new arrival times |
| T+30 min | Agent logs deviation | Records why original plan failed and how recovery was executed |

**Scenario B: Data Staleness (Edge Case)**

| Timing | Event | Agent Response |
|--------|-------|----------------|
| T+0 | Agent queries PPT CITOS | Data timestamp: 25 min old |
| T+1 min | Agent detects data age > 20 min | Triggers escalation: "PPT data stale — verify container readiness with yard planner" |
| T+2 min | Agent presents stale-data alert to ITT coordinator | Asks: "Proceed with cached data or refresh?" |
| T+3 min | ITT coordinator requests refresh | Agent sends query to PPT CITOS, receives fresh data |
| T+4 min | Agent notes: 3 containers no longer ready (removed by customs hold) | Adjusts candidate list from 120 to 117 |
| T+5 min | Agent recomputes split with 117 containers | Presents updated approval card |

---

## 5. Dual-Layer Mathematical ROI & Economic Model

> **Methodology Note on Financial Metrics:**
> - **Gross Disruption Exposure ($15,600–$29,000 per incident):** Total capital and operational assets exposed to risk during an unmitigated ITT failure (vessel demurrage liability, feeder charter hire, and base haulage).
> - **Net Recoverable Friction Savings ($8,000 per incident):** Direct, addressable operational waste eliminated by the agent per event (avoided vessel delay hours + avoided truck overprovisioning + avoided yard re-handles − agent runtime cost).

### Grounded Singapore Cost Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Mother vessel demurrage rate | $2,500/hr | Industry standard for Panamax container vessel |
| Feeder vessel charter rate | $800/hr | Industry standard for regional feeder |
| Road ITT cost per trip | $150 | PPT→Tuas (~35 km via West Coast Highway/AYE), prime mover + driver + fuel |
| LTA prime mover chassis capacity | 1 FEU (40ft/45ft) OR up to 2 TEU (20ft) | Singapore Land Transport Authority road safety regulations |
| Sea ITT marginal charter cost | $0 | Existing scheduled feeder/barge rotation between PPT and Tuas |
| Sea ITT terminal handling cost | $35/lift-move | PSA standard container handling lift cost at berths |
| Sea ITT cost per feeder hold hour | $800/hr | Feeder charter rate |
| Unproductive yard re-handle | $35/move | PSA standard cost |
| Dry container missed connection | $150/container | SLA penalty + demurrage at destination |
| Container yard block max capacity | 4,500 TEU | CITOS yard planning parameter |
| AGV round trip PPT→Tuas (road ITT proxy) | N/A | Road ITT uses external haulier trucks |

### Anchor Problem ROI (PB-12 Single Incident)

$$\text{Savings}_{\text{incident}} = \text{Avoided Vessel Delay} + \text{Avoided Road ITT Overprovision} + \text{Avoided Sea ITT Overcharge} + \text{Avoided Yard Re-handles} - \text{Agent Operating Cost}$$

**Current state (manual) cost per incident:**
- Vessel delay at Tuas (2 hrs × $2,500/hr): **$5,000**
- Road ITT overprovision (5 extra trucks × $150): **$750**
- Sea ITT overcharge (feeder hold 2 hrs × $800): **$1,600**
- Yard re-handling (20 re-handles × $35): **$700**
- Staff coordination (8 staff-hours × $50/hr): **$400**
- **Total manual cost: $8,450**

**Agent-assisted state cost per incident:**
- Vessel delay avoided (0 hrs): **$0**
- Road ITT optimal (0 extra trucks): **$0**
- Sea ITT minimal hold (0.5 hr × $800): **$400**
- Yard re-handles avoided (0): **$0**
- Agent operating cost (amortised): **$50**
- **Total agent cost: $450**

$$\text{Savings}_{\text{incident}} = \$8,450 - \$450 = \$8,000$$

### Annualised Flagship ROI

| Metric | Value |
|--------|-------|
| Savings per incident | $8,000 |
| Incidents per month | 4–6 |
| Monthly savings | $32,000–$48,000 |
| **Annual savings (flagship only)** | **$384,000–$576,000** |

### Cluster Addressable Impact (C2 Platform Generalisation)

| Problem | Monthly Frequency | Savings/Incident | Monthly Savings | Annual Savings |
|---------|------------------|-------------------|-----------------|----------------|
| **PB-01** (Berth Delay) | 2–3 | $8,000 | $16,000–$24,000 | $192,000–$288,000 |
| **PB-02** (DTQC Breakdown) | 4–6 | $4,000 | $16,000–$24,000 | $192,000–$288,000 |
| **PB-04** (Missed Connection) | 3–5 | $5,000 | $15,000–$25,000 | $180,000–$300,000 |
| **PB-09** (Expressway Blockage) | 2–4 | $5,000 | $10,000–$20,000 | $120,000–$240,000 |
| **PB-10** (Sea-Air Cut-Off) | 1–2 | $10,000 | $10,000–$20,000 | $120,000–$240,000 |
| **PB-11** (Customs Hold) | 2–4 | $3,000 | $6,000–$12,000 | $72,000–$144,000 |
| **PB-12** (ITT Coordination) | 4–6 | $8,000 | $32,000–$48,000 | $384,000–$576,000 |
| **Total Cluster C2** | **18–30/month** | — | **$105,000–$173,000** | **$1,260,000–$2,076,000** |

**Cluster Addressable Annual Impact: $1.26M–$2.08M**

The agent architecture built for PB-12 (event ingestion, multi-tool orchestration, HITL gate, multi-party notification) generalises to all 7 sibling problems with minimal tool customisation — the core reasoning planner, email/EDI parser, and approval workflow remain identical.

---

## 6. Platform Generalization (Cluster Scalability)

### Sibling Problems Addressed by Same Core Architecture

| Problem | Core Architecture Reuse | Tool Customisation Required |
|---------|------------------------|-----------------------------|
| **PB-01** (Berth Delay) | Event ingestion, multi-tool orchestration, HITL gate | Replace ITT tools with VTIS/OptEVoyage/CITOS berth tools |
| **PB-02** (DTQC Breakdown) | Event ingestion, multi-tool orchestration, HITL gate | Replace ITT tools with ROCC/CITOS/FMS crane tools |
| **PB-04** (Missed Connection) | Event ingestion, multi-tool orchestration, HITL gate | Replace ITT tools with PORTNET/CITOS feeder tools |
| **PB-09** (Expressway Disruption) | Event ingestion, multi-tool orchestration, HITL gate | Replace ITT tools with OptETruck/SmartBooking slot tools |
| **PB-10** (Sea-Air Cut-Off) | Event ingestion, multi-tool orchestration, HITL gate | Replace ITT tools with OptEModal/TradeNet/SATS tools |
| **PB-11** (Customs Hold) | Event ingestion, multi-tool orchestration, HITL gate | Replace ITT tools with TradeNet/CALISTA document tools |

### Shared Agentic Primitives

| Primitive | Description | Generalisation |
|-----------|-------------|----------------|
| **Event Ingestion Layer** | Webhook receiver for disruption events (vessel delay, QC breakdown, customs hold, etc.) | Identical across all problems — only event schema differs |
| **Reasoning Planner** | LLM-based planner that ingests event context, queries tools, computes options, and selects optimal action | Identical core prompt — tool descriptions change per problem |
| **Multi-Tool Orchestrator** | Dynamic tool selection and parallel execution across ≥3 PSA systems | Identical framework — tool definitions change per problem |
| **HITL Approval Gate** | Structured approval card with cost analysis, risk assessment, and approve/modify/reject options | Identical UI component — data populated per problem |
| **Multi-Party Notification** | Automated notification to affected stakeholders (phone/email/system alert) | Identical framework — recipient list and message template change per problem |
| **Deviation Logger** | Records when agent deviates from original plan and why | Identical across all problems |

---

## 7. Execution Trace & Demo Script

### Trigger Event Payload (Simulated JSON Input)

```json
{
  "event_type": "ITT_COORDINATION_REQUEST",
  "timestamp": "2026-08-19T10:30:00+08:00",
  "source": "CITOS_PPT",
  "priority": "high",
  "payload": {
    "origin_terminal": "PPT",
    "destination_terminal": "TUAS",
    "vessel_id": "MV PACIFIC STAR",
    "tuas_vessel_departure": "2026-08-19T20:00:00+08:00",
    "container_count": 120,
    "containers_ready": 120,
    "blocks_affected": ["B-07", "B-08", "B-12", "B-14"],
    "dg_containers": 3,
    "priority_containers": 45,
    "requested_by": "PPT_Yard_Planner_Lim",
    "notes": "Priority transhipment for MV PACIFIC STAR. 120 containers ready for cross-terminal ITT. Both road and sea options available."
  }
}
```

### Happy Path Step-by-Step Trace

| Step | Agent Thought | Action | Observation |
|------|--------------|--------|-------------|
| 1 | "New ITT coordination request. 120 containers from PPT to Tuas. Vessel departs 2000. I need to check what's available at PPT and what transport options exist." | `get_itt_candidates("CITOS_PPT", "MV PACIFIC STAR")` | 120 containers (40x 40ft + 80x 20ft = 160 TEU) confirmed ready across 4 yard blocks |
| 2 | "Containers confirmed. Now I need to check road ITT capacity — how many trucks are available, transit time, and road conditions along West Coast Highway and AYE?" | `check_road_itt_capacity("OPTETRUCK", "PPT", "11:00", "18:00")` | 20 trucks available, 90 min transit, $150/trip, 60 trips needed for 80-container road split (40x 40ft + 40x 20ft) |
| 3 | "Road capacity is 20 trucks. Now I need to check sea ITT — what feeder vessels are available and what are the departure constraints?" | `check_sea_itt_capacity("PORTNET", "FEEDER ATLANTIC-03", "2026-08-19T10:35:00+08:00")` | Feeder available, 180 TEU capacity, departure window 1400–1600, downstream tidal window at Port Klang at 2300 |
| 4 | "I have all the data. Let me compute the optimal road/sea split considering LTA chassis limits (1x 40ft or 2x 20ft per trip), cost, time, and downstream constraints." | `compute_itt_split(candidates, road_capacity, sea_capacity, "2026-08-19T20:00:00+08:00", constraints)` | Optimal split: 80 road (60 trips: $9,000) / 40 sea ($0 charter + $1,400 handling), total transport cost $10,400 (vs. $12,000 all-road baseline of 80 trips) |
| 5 | "I have the optimal split. This involves committing trucks and requesting a feeder hold — both are state-mutating actions. I need ITT coordinator approval." | **HITL Gate** — Present approval card | ITT coordinator reviews and approves |
| 6 | "Approved. Dispatching 16 trucks on West Coast Highway corridor and requesting 1-hour feeder hold." | `dispatch_road_itt("OPTETRUCK", 16, "PPT -> West Coast Highway -> AYE -> Tuas Port Boulevard")` + `request_feeder_hold("PORTNET", "FEEDER ATLANTIC-03", 1)` | Trucks dispatched, feeder hold requested |
| 7 | "Road ITT dispatched. Updating Tuas yard planner with expected arrival times." | `update_tuas_loading_sequence("CITOS_TUAS", "MV PACIFIC STAR", "14:30", "16:30", road_ids, sea_ids)` | Tuas loading sequence updated |
| 8 | "Monitoring... 21 minutes elapsed. PORTNET just reported a feeder berth conflict." | Agent detects deviation | Feeder departure delayed to 1600 — will miss tidal window at Port Klang |
| 9 | "Berth conflict detected. Feeder cannot depart by 1530 as planned. I need to re-compute: shift 20 containers from sea to road (100 road / 20 sea = 70 truck trips). Road trucks are already cycling — I need to add 4 more trucks on the PPT -> West Coast Highway -> AYE route." | `compute_itt_split(revised_candidates, updated_road, constrained_sea, ...)` | Revised split: 100 road / 20 sea, +$1,500 road cost but avoids $5,000 missed connection |
| 10 | "Revised split ready. This changes the truck dispatch — needs ITT coordinator re-approval." | **HITL Gate** — Present emergency re-split | ITT coordinator approves emergency re-split |
| 11 | "Re-approved. Dispatching 4 additional trucks, updating Tuas loading sequence." | `dispatch_road_itt("OPTETRUCK", 4, "PPT -> West Coast Highway -> AYE -> Tuas Port Boulevard")` + `update_tuas_loading_sequence(...)` | Additional trucks dispatched, Tuas updated |
| 12 | "Incident resolved. Logging deviation: original 80/40 split → revised 100/20 split due to feeder berth conflict. Agent detected at T+21 min, re-computed and re-dispatched within 4 minutes." | Agent logs deviation | Deviation recorded for learning |

### Injected Edge-Case Failure (Demo Feature)

**At Step 8**, the agent detects a feeder berth conflict — a realistic disruption that occurs in approximately 30% of ITT coordination events. The agent's response demonstrates:

1. **Real-time monitoring:** Agent continuously polls PORTNET for feeder status updates
2. **Adaptive reasoning:** Agent re-computes the split under new constraints (feeder delayed)
3. **Cost-benefit analysis:** Agent shows ITT coordinator the cost comparison (+$1,500 road vs. $5,000 missed connection)
4. **Graceful recovery:** Agent dispatches additional trucks and updates Tuas loading sequence without human re-planning
5. **Full audit trail:** Every decision, tool call, and deviation is logged

---

## Acceptance Criteria Verification

- [x] **Exact mock tool JSON signatures defined with parameters and outputs** — 5 tools with full JSON schemas in Section 3
- [x] **Cost model differentiates between cargo tiers** — N/A for ITT (no reefer/DG differentiation in transport mode split), but risk assessment includes DG container handling
- [x] **Realistic multi-party coordination model including downstream destination constraints** — Feeder downstream tidal window at Port Klang integrated into split computation
- [x] **Demo script includes both Happy Path and Injected Edge-Case Failure** — Feeder berth conflict scenario at Step 8

---

## Appendix: Problem Selection Audit Trail

| Phase | Decision | Rationale |
|-------|----------|-----------|
| **Stage 1 Litmus** | 4 problems eliminated (PB-03, PB-05, PB-14, PB-16) | Deterministic rule engines (PB-03, PB-05), micro-ROI (PB-14), pure MILP (PB-16) |
| **Stage 2 Cluster** | C2 selected (score 4.80/5.00) | Highest agentic sweet spot, broadest coverage (7 problems), most compelling demo |
| **Stage 3 Flagship** | PB-12 selected from C2 | Highest system count (5), systemic architecture gap (CITOS disintegration), dual transport mode optimisation |
| **Autonomy** | Tier 2 HITL Exception Solver | HIGH financial risk ($15K–$29K/incident) + multi-party authority boundaries + data asymmetry |
| **Cluster Leverage** | 7 sibling problems addressed by same architecture | Platform generalisation provides $1.26M–$2.08M annual addressable impact |

---

## Sources

- `problems/02-03-problem-bank.md` — PB-12 charter and mock tools
- `problems/02-02-failure-modes.md` — D4 failure mode analysis
- `problem-selection/03-01-litmus-test-scores.md` — Litmus filter and cluster scoring
- `problem-selection/03-02-autonomy-level.md` — Risk profiling and HITL guardrails
- `research/flows/critical-flows.md` — ITT coordination decision flow
- `research/systems/baseline-systems.md` — OptETruck, CITOS, PORTNET profiles
