# Master Problem Charter: Multi-Party ITT Coordination Failure (Cross-Terminal)

**Status:** Locked  
**Flagship Problem:** PB-12  
**Parent Cluster:** C2 — Manual Multi-Party Coordination  
**Last updated:** 2026-08-27  
**Revision:** Gap-aware rewrite — honest inventory of built vs. missing

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

### Tool 6: `receive_webhook` (Event Trigger — T6)

> **T6 is the agent entry point.** It is not a standalone tool the agent calls — it is the FastAPI HTTP endpoint that receives the `ITT_COORDINATION_REQUEST` event and bootstraps the agent's initial state.

```python
# FastAPI endpoint — receives external events, triggers agent
@app.post("/webhook/itt-coordination")
async def receive_webhook(event: ITTCoordinationEvent):
    """
    Webhook endpoint for ITT_COORDINATION_REQUEST events.
    Called by CITOS (PPT) when 50+ containers are ready for cross-terminal transfer.
    Validates payload, creates initial agent state, triggers LangGraph agent.
    """
    # Validation
    assert event.container_count >= 50
    assert event.tuas_vessel_departure > now() + timedelta(hours=2)
    
    # Bootstrap agent state from webhook payload
    initial_state = {
        "event": event,
        "origin_terminal": event.origin_terminal,       # "PPT"
        "destination_terminal": event.destination_terminal, # "TUAS"
        "vessel_id": event.vessel_id,
        "container_count": event.container_count,
        "tuas_vessel_departure": event.tuas_vessel_departure,
        "blocks_affected": event.blocks_affected,
        "dg_containers": event.dg_containers,
        "current_step": "ingest",
        "hitl_pending": [],
        "escalations": [],
        "confidence_scores": [],
        "deviation_log": []
    }
    
    # Trigger LangGraph agent
    result = await agent_graph.ainvoke(initial_state)
    return {"status": "accepted", "run_id": result["run_id"]}

# Pydantic model for webhook payload
class ITTCoordinationEvent(BaseModel):
    event_type: str                    # "ITT_COORDINATION_REQUEST"
    timestamp: str                     # ISO 8601
    source: str                        # "CITOS_PPT"
    priority: str                      # "high" | "critical"
    origin_terminal: str               # "PPT"
    destination_terminal: str          # "TUAS"
    vessel_id: str                     # "MV PACIFIC STAR"
    tuas_vessel_departure: str         # ISO 8601
    container_count: int               # ≥ 50
    containers_ready: int              # ≤ container_count
    blocks_affected: list[str]         # ["B-07", "B-08", ...]
    dg_containers: int                 # ≥ 0
    priority_containers: int           # ≥ 0
    requested_by: str                  # human identifier
    notes: str                         # optional context

# Sample Webhook Trigger (used in demo)
{
    "event_type": "ITT_COORDINATION_REQUEST",
    "timestamp": "2026-08-19T10:30:00+08:00",
    "source": "CITOS_PPT",
    "priority": "high",
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
    "notes": "Priority transhipment for MV PACIFIC STAR. 120 containers ready for cross-terminal ITT."
}
```

### Post-Approval Tools (not yet implemented)

The following tools execute AFTER human approval. They are defined here for completeness but have no implementation.

```python
def dispatch_road_itt(
    optetruck_endpoint: str,
    num_trucks: int,
    route: str
) -> dict:
    """Dispatch prime movers via OptETruck. Requires HITL Gate 2 approval."""
    pass

def request_feeder_hold(
    portnet_endpoint: str,
    feeder_id: str,
    hold_hours: float
) -> dict:
    """Request feeder operator to hold departure. Requires HITL Gate 3 approval.
    NOTE: This is a REQUEST, not a command — feeder operator is an independent carrier.
    """
    pass
```

---

## 4. Safety Guardrails, HITL Gates, Escalation Triggers & Failure Scenarios

### All 5 Mandatory HITL Gates

| Gate | Trigger | Action | Timeout | Timeout Action | Rationale |
|------|---------|--------|---------|----------------|-----------|
| **HITL-1** | Split computed | Approve ITT Split | 30 min | Escalate to Duty Manager | Financial commitment ($10K+) — requires coordinator sign-off |
| **HITL-2** | Truck dispatch ready | Approve Truck Dispatch | 15 min | Cancel Dispatch | State-mutating action on external OptETruck system |
| **HITL-3** | Feeder hold request | Approve Feeder Hold | 15 min | Escalate to Duty Manager | Commercial decision — delays feeder, may miss tidal window |
| **HITL-4** | Loading sequence update | Approve Sequence Update | 10 min | Hold Current Sequence | Affects Tuas QC operations — requires yard planner approval |
| **HITL-5** | Escalation triggered | Escalate to Duty Manager | 30 min | Halt Workflow | Agent cannot resolve — human must intervene directly |

### HITL Gate Card (Primary — HITL-1)

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
│  CONFIDENCE: 0.92 (above threshold 0.85)                    │
│  RISK: Feeder departure window closes 1530 — hold max 1 hr  │
│  MARGIN: 3 hrs before vessel departure (Adequate)           │
├──────────────────────────────────────────────────────────────┤
│  [APPROVE]  [MODIFY SPLIT]  [REJECT]                        │
└──────────────────────────────────────────────────────────────┘
```

### HITL Disapproval Flow

When the human clicks **REJECT** or **MODIFY SPLIT** on any HITL gate:

| Action | Agent Response | Rationale |
|--------|---------------|-----------|
| **REJECT** (no modification) | Agent halts the current plan, logs rejection reason, presents alternative split options (the `alternatives` array from Tool 4), or escalates to Duty Manager if no viable alternatives exist | Human has decided the agent's plan is operationally unacceptable — agent must not force execution |
| **MODIFY SPLIT** (human adjusts road/sea ratio) | Agent re-validates the modified split against constraints (LTA chassis limits, feeder capacity, timeline margin), re-runs Tool 4 with adjusted parameters, presents updated cost analysis, and requests re-approval | Human may have contextual knowledge the agent lacks (e.g., known road works, feeder reliability concerns) |
| **Timeout** (no response within gate timeout) | Agent escalates to Duty Manager per the `timeout_action` column above. If Duty Manager also does not respond within 30 min, agent halts workflow entirely | Prevents indefinite blocking — the system must fail safe, not fail silent |

**Key principle:** The agent NEVER executes a rejected action. Rejection is terminal for that plan iteration. The agent's role is to present alternatives or escalate — not to persuade.

### 7 Escalation Triggers

| # | Trigger | Threshold | Agent Action | Rationale |
|---|---------|-----------|--------------|-----------|
| 1 | Low model confidence | confidence < 0.85 | Escalate to human | Agent uncertain — requires senior judgment |
| 2 | Feeder hold exceeds tidal tolerance | hold > 1.5 hrs | Escalate to duty manager | Feeder may miss downstream tidal window — commercial risk |
| 3 | Financial recovery cost > limit | action cost > $10,000 | Escalate to duty manager | High single-action cost requires sign-off |
| 4 | Data latency exceeds freshness | data age > 30 min | Escalate to human | Operating on stale cross-terminal data |
| 5 | Road ITT capacity below threshold | available trucks < 60% required | Escalate to human | Insufficient road capacity — emergency sea coordination |
| 6 | Feeder operator unresponsive | response time > 15 min | Escalate to human | Cannot confirm availability — must escalate via phone |
| 7 | Conflict between planners | planner recommendations conflict | Escalate to duty manager | Cross-terminal disagreement requires arbitration |

### Confidence Scoring

- **Method:** LLM self-assessment — the agent outputs a confidence score (0.0–1.0) with every decision via structured JSON output (see Gap G-07)
- **Threshold:** 0.85 — below this, the agent automatically escalates (Trigger #1)
- **Logging:** All confidence scores are logged to LangSmith for post-demo analysis
- **Demo value:** Shows the judges that the agent knows when it doesn't know

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

### Demo Infrastructure

| Component | Implementation | Purpose |
|-----------|---------------|---------|
| **Agent framework** | LangGraph v1.2.11 | State machine, tool orchestration, HITL nodes |
| **LLM** | Configurable (Claude Sonnet 4 / GPT-4o / Gemini) | Provider-agnostic via abstraction layer |
| **Backend** | FastAPI + uvicorn | Serves agent + mock APIs + webhook on one port |
| **Mock APIs** | In-process Python functions | Simulates all 5 PSA systems with realistic data |
| **Webhook** | `POST /webhook/itt-coordination` (T6) | Entry point — receives ITT_COORDINATION_REQUEST events |
| **Web UI** | HTML/JS + SSE from FastAPI | Real-time agent decisions streamed to browser |
| **Tracing** | LangSmith free tier | Full graph execution trace, tool calls, HITL events |
| **Config** | YAML per problem | Same agent core, different systems/tools/costs per problem |
| **Deploy** | Docker → Railway/Render (free tier) | Zero infra cost |

### LangSmith Trace Output (Demo Feature)

```
Run: demo-2026-08-23-001
├── [T+0.0s] WEBHOOK: receive_webhook() — ITT_COORDINATION_REQUEST accepted
├── [T+0.0s] node: ingest → Read from CITOS_PPT (2.1s, 1,200 tokens, confidence: 0.95)
├── [T+2.1s] node: ingest → Read from OptETruck (1.8s, 800 tokens, confidence: 0.90)
├── [T+3.9s] node: ingest → Read from Feeder (1.5s, 600 tokens, confidence: 0.88)
├── [T+5.4s] node: decide → LLM: "query_container_readiness" (3.2s, 2,100 tokens, confidence: 0.92)
├── [T+8.6s] node: execute → tool_1 output: 120 containers ready (0.3s)
├── [T+8.9s] node: decide → LLM: "check_road_itt_capacity" (2.8s, 1,800 tokens, confidence: 0.88)
├── [T+11.7s] node: execute → tool_2 output: 20 trucks, 90 min transit (0.4s)
├── [T+12.1s] node: decide → LLM: "check_sea_itt_capacity" (2.5s, 1,600 tokens, confidence: 0.90)
├── [T+14.6s] node: execute → tool_3 output: feeder at 1400, 200 TEU (0.3s)
├── [T+14.9s] node: decide → LLM: "compute_itt_split" (4.1s, 3,200 tokens, confidence: 0.92)
├── [T+19.0s] node: execute → tool_4 output: 80 road / 40 sea, $10,400 (0.2s)
├── [T+19.2s] node: hitl_1 → WAITING: "Approve ITT Split" (awaiting human)
│   └── [T+45.0s] HITL DECISION: APPROVED (25.8s response time)
├── [T+45.0s] node: decide → LLM: "dispatch trucks" (2.0s, 1,400 tokens, confidence: 0.91)
├── [T+47.0s] node: hitl_2 → WAITING: "Approve Truck Dispatch"
│   └── [T+52.0s] HITL DECISION: APPROVED (5.0s response time)
├── [T+52.0s] node: execute → OptETruck dispatch (1.2s)
├── [T+53.2s] node: hitl_3 → WAITING: "Approve Feeder Hold Request"
│   └── [T+60.0s] HITL DECISION: APPROVED (6.8s response time)
├── [T+60.0s] node: execute → Feeder hold request sent (0.8s)
├── ⚠️ [T+81.0s] DEVIATION: Feeder berth conflict detected (step 8)
│   ├── ESCALATION TRIGGER #1: confidence dropped to 0.78 (below 0.85)
│   ├── ESCALATION TRIGGER #2: feeder hold > 1.5 hrs
│   └── Agent re-computes: 80/40 → 100/20 split
├── [T+81.0s] node: hitl_5 → WAITING: "Emergency Re-Split Approval"
│   └── [T+88.0s] HITL DECISION: APPROVED (7.0s response time)
├── [T+88.0s] node: execute → Updated truck dispatch (1.0s)
├── [T+89.0s] node: execute → Updated Tuas loading sequence (0.9s)
└── [T+89.9s] node: complete → Incident resolved, deviation logged

Total: 89.9s wall time | ~18,000 input tokens | ~3,500 output tokens | ~$0.10 (Claude Sonnet 4)
HITL response times: Gate 1 (25.8s), Gate 2 (5.0s), Gate 3 (6.8s), Gate 5 (7.0s)
Escalation triggers fired: #1 (low confidence), #2 (feeder hold), #6 (unresponsive feeder)
Confidence trajectory: 0.95 → 0.90 → 0.88 → 0.92 → 0.91 → 0.78 (deviation) → 0.90 (recovery)
```

---

## 8. Gap Inventory — What Exists vs. What's Missing

> **Purpose:** This section provides an honest, cynical inventory of every gap between the current prototype and the competition-ready system. Each gap is assigned an ID and severity. Phase plans in `.planning/phases/` will address these gaps in detail.

### Severity Definitions

| Severity | Meaning |
|----------|---------|
| **CRITICAL** | Blocks demo functionality — system cannot run without this |
| **HIGH** | Significantly degrades demo quality — judges will notice |
| **MEDIUM** | Reduces polish — affects presentation but not core functionality |
| **LOW** | Nice-to-have — improves code quality but not demo-critical |

### Gap Inventory

| ID | Severity | Gap | Current State | Required State | Phase Plan |
|----|----------|-----|---------------|----------------|------------|
| **G-01** | CRITICAL | **No LangGraph agent core** | Linear async orchestrator (`orchestrator.py`) with `asyncio.gather` — no state machine, no conditional branching, no tool-calling loop | LangGraph StateGraph with INGEST → DECIDE → EXECUTE → HITL → ESCALATE nodes, conditional edges, state checkpointing | Phase 6 |
| **G-02** | CRITICAL | **LLM not wired into decision-making** | `provider.py` (735 lines, 8 providers) exists but is DEAD CODE — never imported by any orchestration logic. The compute_itt_split is deterministic math, not LLM reasoning | LLM drives all tool selection decisions via ReAct loop. The agent queries tools, reasons about results, and decides next actions. Deterministic math (Tool 4) is called BY the LLM, not INSTEAD of it | Phase 6 |
| **G-03** | CRITICAL | **No HITL implementation** | `in_approval/` and `post_approval/` directories are empty. No approval card rendering, no callback mechanism, no timeout handling | 5 HITL gates with approval cards rendered in web UI, callback to agent on approve/reject/modify, timeout escalation | Phase 6 + 7 |
| **G-04** | CRITICAL | **No web UI** | No HTML/CSS/JS files. No SSE streaming. No demo interface. | Web dashboard with: port operations view, execution trace drawer (real-time SSE), HITL approval cards, edge case injection controls | Phase 7 |
| **G-05** | CRITICAL | **Post-approval tools missing** | `dispatch_road_itt` and `request_feeder_hold` are defined in charter but have no implementation | Functional tool implementations that the agent calls after HITL approval | Phase 5 |
| **G-06** | HIGH | **Tool invocation architecture unclear** | Tools run as direct Python function calls (in-process). Mock API HTTP endpoints exist but are unused by the orchestrator | Decision needed: (a) In-process calls (simpler, faster, fine for demo) or (b) HTTP calls to same FastAPI server (more realistic, shows API orchestration). Recommendation: in-process for demo, document as architectural decision | Phase 4 |
| **G-07** | HIGH | **Confidence scoring is deterministic, not LLM-generated** | `_compute_confidence()` in compute_itt_split.py uses hardcoded math (margin, truck ratio, feeder headroom) | LLM outputs structured JSON with confidence score per decision. Deterministic score serves as backup/validation, not primary source | Phase 6 |
| **G-08** | HIGH | **No execution trace / observability** | No LangSmith integration, no deviation logging, no structured trace output | Full execution trace: timestamp, step name, agent reasoning, tool called, arguments, response, risk score, approval status. Streamed to UI and logged to LangSmith | Phase 6 + 7 |
| **G-09** | HIGH | **provider.py not tested end-to-end** | 8 providers implemented but never validated with actual API keys | End-to-end test with at least one provider (Anthropic or OpenAI). Verify: chat works, tool calling works, retry works, fallback works | Phase 4 |
| **G-10** | HIGH | **Webhook duplication** | Two separate webhook implementations: `mocks/webhook.py` (in FastAPI app) and `container_readiness/webhook.py` (standalone). Different schemas, different validation. | Single unified webhook endpoint that receives the event, validates, bootstraps agent state, and triggers the LangGraph agent | Phase 4 |
| **G-11** | HIGH | **Edge cases not connected to agent** | `mocks/edge_cases.py` has `simulate_feeder_conflict()` and `simulate_stale_data()` but they're only importable, not triggered by any API or UI | Edge case injection API endpoint + UI controls. Demo operator clicks "Inject Berth Conflict" → agent receives modified feeder data at step 8 | Phase 7 |
| **G-12** | HIGH | **Tool 5 (update_tuas_loading_sequence) has no tool function** | Schema exists in `schemas.py` but no `update_tuas_loading_sequence()` function implemented | Functional tool that the agent calls after dispatch to update Tuas QC loading sequence | Phase 5 |
| **G-13** | MEDIUM | **prototype/ directory structure is misleading** | Top-level dirs: `pre_approval/`, `in_approval/` (empty), `post_approval/` (empty). Doesn't map to agent architecture. Tool files scattered across nested dirs. | Recommended restructuring: `agent/` (core graph), `tools/` (all tool implementations), `mocks/` (mock servers), `hitl/` (approval gates), `ui/` (frontend), `shared/` (provider, utils), `configs/` | Phase 4 |
| **G-14** | MEDIUM | **No frontend tech stack decision** | Charter says "HTML/JS + SSE from FastAPI" but no decision on framework (vanilla JS, Alpine.js, htmx, React) | Decide: HTML/JS + vanilla SSE (simplest, fastest to build) or Streamlit (quickest prototype but less polished). Given 8 days left: recommend vanilla HTML/JS + SSE | Phase 7 |
| **G-15** | MEDIUM | **No Docker/deploy configuration** | No Dockerfile, no docker-compose.yml, no deployment config | Dockerfile + docker-compose.yml for local dev. Railway/Render config for free-tier deployment | Phase 8 |
| **G-16** | MEDIUM | **No demo video or presentation deck** | No slides, no video recording | 10-slide deck + 10-minute demo video per competition requirements | Phase 8 |
| **G-17** | MEDIUM | **Confidence scoring method unclear** | Charter says "LLM self-assessment" but doesn't specify HOW the LLM outputs structured confidence | Options: (a) JSON mode with confidence field, (b) Prompt instruction to include confidence in response, (c) Post-parse from natural language. Recommend: JSON mode with structured output schema | Phase 6 |
| **G-18** | MEDIUM | **Feeder berth conflict injection method undefined** | No clear mechanism for injecting the edge case during demo | Options: (a) API query parameter `inject_berth_conflict=True` (already in sea_itt_tools.py), (b) Timed injection at step 8, (c) UI button. Recommend: UI button that sets a flag, agent picks up at next feeder query | Phase 7 |
| **G-19** | MEDIUM | **main.py only serves mocks** | `prototype/main.py` is a mock API server (42 lines). Not the unified FastAPI app that should serve agent + mocks + webhook + UI | Unified FastAPI app that mounts: agent routes, mock API routes, webhook endpoint, SSE endpoint, static files (UI) | Phase 4 |
| **G-20** | MEDIUM | **No scenario runner** | No way to trigger the full demo scenario (webhook → agent → tools → HITL → edge case → recovery) from a single action | "Run Demo" button in UI that: sends webhook payload, agent processes, HITL cards appear, edge case injectable at step 8 | Phase 7 |
| **G-21** | LOW | **YAML configs not loaded by agent** | 7 YAML configs exist in `configs/` but the agent/orchestrator doesn't read them. Config data is hardcoded in tool files | Agent loads YAML config at startup, uses it to determine which tools to call, what systems to query, what HITL gates to enforce | Phase 6 |
| **G-22** | LOW | **No unit test coverage** | Only `tests/test_orchestrator.py` exists. No tests for tools, provider, HITL, escalation | Unit tests for all tools, integration test for full pipeline, HITL gate tests, escalation trigger tests | Phase 6 |
| **G-23** | LOW | **No logging/structured output** | Basic `logging.info()` calls. No structured JSON logging for audit trail | Structured JSON logging to stdout + file. Each log entry: timestamp, run_id, step, event_type, payload | Phase 6 |

### LangGraph Decision — Addressed

The team has raised valid questions about whether LangGraph is necessary. Here is the resolution:

| Question | Answer |
|----------|--------|
| **Can the solution be agentic without LangGraph?** | Yes — but the competition explicitly evaluates "ReAct/Plan-and-Execute mechanics, tool orchestration, state management" (Evaluation Criterion 1). A linear pipeline does not demonstrate these. |
| **Is LangGraph overkill?** | For the pre-approval phase (T1→T2→T3→T4), the flow IS largely sequential — LangGraph adds overhead. But for the full lifecycle (ingest → decide → execute → HITL → monitor → re-compute → re-approve), conditional branching is essential. LangGraph handles the HITL pause/resume natively. |
| **What does LangGraph accomplish for the frontend?** | LangGraph itself does nothing for the frontend. The frontend connects via SSE to stream agent state. LangGraph provides the state machine that GENERATES the events the frontend consumes. |
| **Tool call order pre-split — isn't it deterministic?** | T1→T2→T3 IS deterministic (query all systems). But T4→HITL→dispatch→monitor→re-compute is NOT — the agent must decide whether to re-compute, which tools to re-query, and whether to escalate. That's where LangGraph earns its keep. |
| **Post-split — can it be a deterministic pipeline?** | It COULD be. But the demo's drama comes from the feeder berth conflict edge case at step 8, where the agent must dynamically re-plan. A deterministic pipeline can't handle that without hardcoding the recovery path — which defeats the "agentic" requirement. |
| **Recommendation** | Use LangGraph for the full agent lifecycle (G-01). The pre-approval pipeline (T1→T2→T3→T4) can be a simple sub-graph or sequential node. The HITL gates, monitoring loop, and re-computation path use LangGraph's conditional edges. This gives the best of both worlds: simple where possible, agentic where necessary. |

---

## 9. Technical Implementation (Target Architecture)

### Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.11+ | AI ecosystem, fast prototyping |
| Agent framework | LangGraph v1.2.11 | Provider-agnostic, HITL first-class, state checkpointing |
| LLM | Configurable (Claude/GPT-4o/Gemini) | Swap via config change |
| Backend | FastAPI + uvicorn | Serves agent + mock APIs + webhook on one port |
| Database | None | In-memory state + YAML configs + log files |
| Tracing | LangSmith free tier | Full graph execution trace, tool calls, HITL events |
| Frontend | HTML/JS + SSE | Real-time agent decisions streamed to browser |
| Deploy | Docker → Railway/Render free tier | Zero infra cost |

### How T6 (Webhook) Integrates Into the App Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SYSTEMS                             │
│  CITOS (PPT) ──── POST /webhook/itt-coordination ────┐         │
│  OptETruck    ──── (mock API, same port) ─────────────┤         │
│  Feeder       ──── (mock API, same port) ─────────────┤         │
│  PORTNET      ──── (mock API, same port) ─────────────┤         │
│  CITOS (Tuas) ──── (mock API, same port) ─────────────┤         │
└─────────────────────────────────────────────────────── │ ────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  FASTAPI APP (single port 8000)                                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  T6: receive_webhook()                                   │    │
│  │  POST /webhook/itt-coordination                          │    │
│  │                                                          │    │
│  │  1. Validate payload (Pydantic model)                    │    │
│  │  2. Bootstrap initial agent state from event             │    │
│  │  3. Trigger LangGraph agent with initial state           │    │
│  │  4. Return {"status": "accepted", "run_id": "..."}      │    │
│  └──────────────────────┬───────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  LANGGRAPH AGENT (state machine)                         │    │
│  │                                                          │    │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌────────┐  │    │
│  │  │ INGEST  │──▶│ DECIDE  │──▶│EXECUTE  │──▶│HITL    │  │    │
│  │  │ (tools) │   │ (LLM)   │   │(tools)  │   │(gates) │  │    │
│  │  └─────────┘   └─────────┘   └─────────┘   └────────┘  │    │
│  │       │             │             │             │         │    │
│  │       ▼             ▼             ▼             ▼         │    │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌────────┐  │    │
│  │  │ESCALATE │   │LOG      │   │COMPLETE │   │SSE     │  │    │
│  │  │(triggers│   │(deviate)│   │         │   │(stream)│  │    │
│  │  └─────────┘   └─────────┘   └─────────┘   └────────┘  │    │
│  └──────────────────────┬───────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  MOCK APIs (in-process Python functions)                  │    │
│  │  citos_ppt.py, citos_tuas.py, optetruck.py,              │    │
│  │  feeder.py, portnet.py                                    │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  WEB UI (HTML/JS + SSE)                                   │    │
│  │  GET /ui → real-time agent decisions streamed via SSE     │    │
│  │  POST /ui/hitl-response → human approval/rejection        │    │
│  │  POST /ui/inject-edge-case → trigger demo edge case       │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  LANGSMITH (tracing)                                      │    │
│  │  Auto-instrumented: every node, tool call, LLM call       │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Current Prototype Structure (as-built)

```
prototype/
├── main.py                  # Mock API server only (NOT the unified app)
├── path_config.py           # Path resolution
├── __init__.py
├── configs/                 # YAML configs (7 problems) — NOT loaded by agent
│   ├── config_manager.py
│   ├── pb-12-itt.yaml      # Flagship config
│   └── pb-*.yaml           # 6 sibling problem configs
├── shared/
│   └── utils/
│       ├── provider.py      # LLM abstraction (DEAD CODE — not wired in)
│       └── yaml_reader.py   # YAML config loader
├── pre_approval/            # Agent tools (scattered, not integrated)
│   ├── orchestrator.py      # Linear async pipeline (NOT LangGraph)
│   ├── container_readiness/ # T6 webhook (duplicate of mocks/webhook.py)
│   ├── ppt_citos/           # Tool 1 (has its own mock data, router)
│   ├── road_itt/            # Tool 2
│   ├── sea_itt/             # Tool 3 (has its own mock data, router, models)
│   └── ai_optimisation/     # Tool 4 (deterministic math, works standalone)
├── in_approval/             # EMPTY — no HITL implementation
├── post_approval/           # EMPTY — no dispatch/hold tools
├── mocks/                   # Mock API server (5 PSA systems)
│   ├── schemas.py           # Pydantic models (well-defined)
│   ├── webhook.py           # Webhook endpoint (duplicate)
│   ├── edge_cases.py        # Edge case simulators (not connected)
│   ├── citos_ppt.py, citos_tuas.py, optetruck.py, feeder.py, portnet.py
│   └── data.py              # Mock data loader
└── tests/
    └── test_orchestrator.py # Single test file
```

### Target Prototype Structure (recommended)

```
prototype/
├── main.py                  # Unified FastAPI app (agent + mocks + UI + webhook)
├── agent/                   # NEW: LangGraph agent core
│   ├── graph.py             # StateGraph definition (INGEST→DECIDE→EXECUTE→HITL→ESCALATE)
│   ├── state.py             # Agent state TypedDict
│   ├── nodes/               # Graph nodes
│   │   ├── ingest.py        # Data gathering from mock systems
│   │   ├── decide.py        # LLM reasoning + tool selection
│   │   ├── execute.py       # Tool execution
│   │   ├── hitl.py          # HITL gate management
│   │   ├── escalate.py      # Escalation trigger checks
│   │   └── complete.py      # Incident resolution + deviation logging
│   └── trace.py             # LangSmith trace wrapper
├── tools/                   # REORGANIZED: All tool implementations
│   ├── container_readiness.py  # Tool 1
│   ├── road_itt.py             # Tool 2
│   ├── sea_itt.py              # Tool 3
│   ├── compute_split.py        # Tool 4
│   ├── loading_sequence.py     # Tool 5
│   ├── dispatch_road.py        # Post-approval: Tool 6
│   └── feeder_hold.py          # Post-approval: Tool 7
├── hitl/                    # NEW: HITL gate implementation
│   ├── gates.py             # Gate logic (approve/reject/modify/timeout)
│   ├── cards.py             # Approval card rendering
│   └── callbacks.py         # SSE callback for human responses
├── mocks/                   # KEEP: Mock API servers (cleaned up)
│   ├── routers/             # FastAPI routers per system
│   ├── data.py              # Shared mock data
│   └── edge_cases.py        # Edge case injection
├── ui/                      # NEW: Frontend
│   ├── index.html           # Demo dashboard
│   ├── app.js               # SSE client + HITL interaction
│   └── style.css            # Styling
├── shared/
│   └── utils/
│       ├── provider.py      # LLM abstraction (WIRED IN)
│       └── yaml_reader.py
├── configs/                 # YAML configs (loaded by agent)
└── tests/                   # Expanded test suite
```

---

## 10. Build Order (Revised — 8 Days to Submission)

| Day | Focus | Deliverable |
|-----|-------|-------------|
| **1** | Foundation reformation: unified FastAPI app, wire provider.py, test LLM end-to-end | Working FastAPI app with LLM chat verified |
| **2** | LangGraph agent core: StateGraph, INGEST/DECIDE/EXECUTE nodes, tool registration | Agent can receive webhook, call tools, return result |
| **3** | HITL gates: all 5 gates with approval cards, timeout logic, approve/reject/modify flow | Agent pauses at HITL gates, resumes on human response |
| **4** | Post-approval tools: dispatch_road_itt, request_feeder_hold, update_tuas_loading_sequence | Full tool chain works end-to-end |
| **5** | Escalation triggers (7), confidence scoring (LLM-driven), deviation logging | Agent handles all edge cases per Master Charter |
| **6** | Web UI: SSE streaming, HITL approval cards, edge case injection controls, demo scenario runner | Presentable demo interface |
| **7** | End-to-end testing, Docker, deploy to Railway/Render | Live demo URL |
| **8** | Buffer, demo video recording, presentation deck, submission | Competition-ready |

---

## Acceptance Criteria Verification

> **Note:** This checklist distinguishes between *designed* (documented in charter), *partially built* (code exists but broken/not integrated), and *done* (works end-to-end). See Section 8 gap inventory for full status.

### Designed (charter-level, awaiting implementation)

- [ ] **LangGraph agent core with tool-calling loop** — G-01: Charter specifies the graph, but implementation is a linear async orchestrator. Needs full rewrite.
- [ ] **LLM drives all decision making** — G-02: `provider.py` exists (735 lines, 8 providers) but is dead code. No LLM call happens anywhere in the pipeline.
- [ ] **5 HITL gates with approval cards, timeout, approve/reject/modify** — G-03: Gates defined in YAML config and charter, but `in_approval/` and `post_approval/` are empty. Zero implementation.
- [ ] **7 escalation triggers with threshold detection** — Defined in YAML config, but no code evaluates them at runtime.
- [ ] **Confidence scoring via LLM self-assessment** — G-07: Charter says LLM outputs confidence, but current `_compute_confidence()` is deterministic math. Not LLM-driven.
- [ ] **Execution trace (LangSmith) with full graph, tool calls, HITL events** — G-08: No LangSmith integration. No trace output. No deviation logging.
- [ ] **Web UI with real-time SSE streaming, HITL cards, edge case injection** — G-04: No frontend exists. No HTML/CSS/JS files.
- [ ] **HITL disapproval flow** — Designed in Section 4 (reject = halt + alternatives; modify = re-validate + re-approve) but has no implementation to test against.
- [ ] **Demo script: Happy Path + Feeder Berth Conflict edge case at step 8** — Script defined in charter, but no code orchestrates the scenario end-to-end.
- [ ] **Docker deployment to Railway/Render free tier** — No Dockerfile. No deploy config.

### Partially Built (code exists, but broken or not integrated)

- [~] **Tool 1: Container readiness query** — `pre_approval/container_readiness/` has a webhook handler, but it's a duplicate of `mocks/webhook.py`. Not connected to any agent.
- [~] **Tool 2: Road ITT capacity** — `pre_approval/road_itt/optetruck_tools.py` works standalone (510 lines, well-structured). Not wired into agent or orchestrator.
- [~] **Tool 3: Sea ITT capacity** — `pre_approval/sea_itt/sea_itt_tools.py` works standalone (580 lines, tidal feasibility). Not wired into agent.
- [~] **Tool 4: Multi-constraint optimisation** — `pre_approval/ai_optimisation/compute_itt_split.py` works standalone (1148 lines, deterministic math). Not wired into agent. Confidence scoring is deterministic, not LLM-driven.
- [~] **Tool 5: Tuas loading sequence update** — Schema exists in `schemas.py`. No tool function implemented.
- [~] **Tool 6: Webhook (T6)** — Two duplicate implementations (`mocks/webhook.py` and `container_readiness/webhook.py`). Neither triggers an agent.
- [~] **Post-approval tools (dispatch_road_itt, request_feeder_hold)** — Defined in charter Section 3. No implementation.
- [~] **Mock API server** — `prototype/main.py` serves 5 mock systems. Works for standalone tool testing. Not integrated with agent.
- [~] **Edge case simulation** — `mocks/edge_cases.py` has `simulate_feeder_conflict()` and `simulate_stale_data()`. Not connected to any trigger mechanism.
- [~] **YAML config system** — 7 problem configs exist in `configs/`. Agent doesn't read them.
- [~] **LLM provider abstraction** — `shared/utils/provider.py` (735 lines, 8 providers). Never imported by any orchestration code. Not tested with API keys.
- [~] **Pre-approval orchestrator** — `pre_approval/orchestrator.py` (207 lines). Linear async pipeline with `asyncio.gather`. No LLM, no LangGraph, no conditional branching.

### Done (works end-to-end)

- [x] **Mock tool JSON signatures (schemas)** — `mocks/schemas.py` defines Pydantic models for all 5 tools + webhook. Structurally complete.
- [x] **Cost model grounded in Singapore parameters** — Road ITT $150/trip, LTA chassis limits, feeder charter $800/hr, vessel demurrage $2,500/hr. All sourced and audited.
- [x] **Problem selection locked** — PB-12 selected via 5-Point Litmus Test, Cluster C2 scoring (4.80/5.00), and Master Problem Charter.
- [x] **ROI model mathematically verified** — $8,000/incident net savings, $384K–$576K annual flagship, $1.26M–$2.08M cluster addressable.
- [x] **Research phases (1–3) complete** — 4 sectors mapped, 7 baseline systems documented, 16 problem bank, litmus test, autonomy level defined.
- [x] **Gap inventory complete** — Section 8: 23 gaps, severity-classified with current/required state.

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
- `buildplan/tech-stack.md` — Technical implementation plan, LangSmith tracing, YAML config
- `prototype/` — Current codebase (fragmented, see Section 8 gap inventory)
