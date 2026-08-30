# PSA Nexus — Demo Run Test Plan

> **Purpose**: Exhaustive manual test scripts for every feature, scenario, and edge case.
> **Environment**: Dev mode — backend `:8000`, frontend `:5173` (vite proxy)
> **Date**: 2026-08-29

---

## 0. Pre-Flight Checklist

```bash
# Terminal 1: Backend
cd /home/ahnaf/Documents/Projects/PSACodeSprint
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd /home/ahnaf/Documents/Projects/PSACodeSprint/app/frontend
npm run dev

# Terminal 3: Tests (run after each section)
cd /home/ahnaf/Documents/Projects/PSACodeSprint
python3 -m pytest app/tests/ -q --tb=short
```

**Verify both are running:**
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
# Expected: {"status": "healthy", ...}

curl -s http://localhost:5173 | head -5
# Expected: HTML with <div id="root">
```

---

## 1. YAML Ingestion + Problem Selector

### 1.1 All 7 YAMLs Loadable

```bash
# List all problem configs
curl -s http://localhost:8000/agent/registry | python3 -m json.tool
```

- [ ] Response contains 7 problems
- [ ] Each has `id`, `name`, `description`
- [ ] pb-12-itt has `ITT Coordination` name
- [ ] pb-01-berth has `Berth Reassignment` name

**Expected output shape:**
```json
{
  "problems": [
    {"id": "pb-12-itt", "name": "ITT Coordination", "description": "..."},
    {"id": "pb-01-berth", "name": "Berth Reassignment", "description": "..."},
    {"id": "pb-02-dtqc", "name": "...", "description": "..."},
    {"id": "pb-03-yard", "name": "...", "description": "..."},
    {"id": "pb-04-feeder", "name": "...", "description": "..."},
    {"id": "pb-09-expressway", "name": "...", "description": "..."},
    {"id": "pb-10-sea-air", "name": "...", "description": "..."}
  ]
}
```

### 1.2 Problem Dropdown in UI

- [ ] Open `http://localhost:5173`
- [ ] Problem dropdown shows all 7 problems with human-readable names
- [ ] Default selection: `ITT Coordination`
- [ ] Click dropdown → all 7 visible

### 1.3 Switch Problem

```bash
# Switch to pb-01-berth
curl -s -X POST http://localhost:8000/agent/switch-problem/pb-01-berth | python3 -m json.tool
```

- [ ] Response shows `active_problem: "pb-01-berth"`
- [ ] UI dropdown updates to `Berth Reassignment`
- [ ] Agent trace shows problem switch

```bash
# Switch back to pb-12-itt
curl -s -X POST http://localhost:8000/agent/switch-problem/pb-12-itt | python3 -m json.tool
```

- [ ] Response shows `active_problem: "pb-12-itt"`
- [ ] UI dropdown updates to `ITT Coordination`

### 1.4 Active Problem Persistence

```bash
# Verify active problem persists
curl -s http://localhost:8000/agent/active-problem | python3 -m json.tool
```

- [ ] Returns current active problem
- [ ] Matches last switch

---

## 2. Happy Path — Normal Scenario

### 2.1 Create Event

```bash
curl -s -X POST http://localhost:8000/agent/create-event/pb-12-itt | python3 -m json.tool
```

- [ ] Returns `event_id`, `vessel_id`, `container_count`
- [ ] `container_count` is randomized (not always 120)
- [ ] `vessel_id` is realistic (e.g., "MV PACIFIC STAR")
- [ ] Response has `timestamp`, `source`, `priority`

### 2.2 Simulate Webhook via UI

- [ ] Click `▶ Simulate Webhook` button
- [ ] EventCard shows webhook details (vessel, containers, departure)
- [ ] Status cards show "Will populate after webhook event" (awaiting state)
- [ ] Run button appears in EventCard

### 2.3 Run with Normal Scenario

- [ ] Select `Normal` from scenario dropdown
- [ ] Click `Run` button in EventCard
- [ ] WorkflowProgress advances: Event → Ingest → Split → HITL-1
- [ ] HITL-1 card appears with ITT Split Plan (road/sea/cost)
- [ ] Confidence shows ~92% (Normal scenario)
- [ ] Risk score shows low value

### 2.4 HITL-1 Approval

- [ ] Click `Approve` on HITL-1
- [ ] HITL-1 card replaced with HITL-2 card
- [ ] HITL-2 shows Truck Dispatch info
- [ ] Status cards populate: CITOS shows container count, OptETruck shows truck count

### 2.5 HITL-2 Approval

- [ ] Click `Approve` on HITL-2
- [ ] HITL-2 card replaced with HITL-3 card
- [ ] HITL-3 shows Feeder Hold info (hold hours computed from sea_eta)

### 2.6 HITL-3 Approval

- [ ] Click `Approve` on HITL-3
- [ ] HITL-3 card replaced with HITL-4 card
- [ ] HITL-4 shows Tuas Loading Sequence

### 2.7 HITL-4 Approval

- [ ] Click `Approve` on HITL-4
- [ ] HITL-4 card replaced with "Processing…" or completion
- [ ] WorkflowProgress advances to Monitor → Done

### 2.8 Cost Breakdown

- [ ] Cost breakdown shows dynamic values (not hardcoded $10,400)
- [ ] Road cost = trips × $150
- [ ] Sea cost = containers × $35
- [ ] Savings vs baseline shown
- [ ] Cost updates after each HITL gate

### 2.9 Completion

- [ ] WorkflowProgress shows "Done" (stage 12)
- [ ] Agent output shows completion message
- [ ] Status: "completed"
- [ ] Cost breakdown final values stable

---

## 3. HITL Interactions

### 3.1 Modify (HITL-1 Only)

```bash
# Start fresh run
curl -s -X POST http://localhost:8000/agent/reset -H "Content-Type: application/json" | python3 -m json.tool
curl -s -X POST http://localhost:8000/agent/create-event/pb-12-itt | python3 -m json.tool
```

- [ ] Run with Normal scenario
- [ ] At HITL-1, click `Modify`
- [ ] Input field appears for road containers
- [ ] Enter different value (e.g., 70)
- [ ] Click `Approve` with modification
- [ ] Cost breakdown updates to reflect modified split

### 3.2 Reject Flow

- [ ] Start fresh run
- [ ] At HITL-1, click `Reject`
- [ ] Reason textarea appears
- [ ] Enter reason "Insufficient road capacity"
- [ ] Click `Reject` with reason
- [ ] Workflow stops or re-reasons (does NOT advance to HITL-2)
- [ ] Agent output shows rejection message

### 3.3 Reject at HITL-2

- [ ] Start fresh run, approve HITL-1
- [ ] At HITL-2, click `Reject`
- [ ] Workflow stops (does NOT advance to HITL-3)
- [ ] No downstream tools execute (dispatch, hold, tuas)

### 3.4 Reject at HITL-3

- [ ] Start fresh run, approve HITL-1, HITL-2
- [ ] At HITL-3, click `Reject`
- [ ] Workflow stops (does NOT advance to HITL-4)

### 3.5 Timeout Behavior

```bash
# Check timeout scheduler
curl -s http://localhost:8000/agent/active-run | python3 -m json.tool
```

- [ ] Run at HITL gate
- [ ] Wait for timeout (configurable in pb-12-itt.yaml)
- [ ] Timeout triggers escalation
- [ ] HITL card shows timeout action
- [ ] Agent output shows timeout message

---

## 4. Stale/Missing Data Scenario

### 4.1 Run with Stale Scenario

- [ ] Select `Stale/Missing Data` from scenario dropdown
- [ ] Click `Run`
- [ ] Staleness warning appears in agent output
- [ ] Data timestamp shows ~25 minutes old
- [ ] Confidence shows ~80%

### 4.2 Staleness Detection

- [ ] Agent output mentions "stale data" or "data age"
- [ ] Risk score elevated compared to Normal
- [ ] Cost breakdown still computes (not blocked)

### 4.3 Completion

- [ ] Workflow completes despite staleness
- [ ] All HITL gates functional
- [ ] Cost values reasonable

---

## 5. Low Trucks Scenario

### 5.1 Run with Low Trucks Scenario

- [ ] Select `Low Trucks` from scenario dropdown
- [ ] Click `Run`
- [ ] OptETruck shows ~18 available trucks (not 40)
- [ ] Confidence shows ~62%
- [ ] Risk score elevated

### 5.2 Escalation Triggers

- [ ] Low confidence triggers escalation check
- [ ] Agent output mentions escalation or low resource warning
- [ ] Cost breakdown shows fewer road containers
- [ ] More containers shifted to sea

### 5.3 Cost Dynamics

- [ ] Road cost lower (fewer trips)
- [ ] Sea cost higher (more containers)
- [ ] Total cost different from Normal scenario
- [ ] Savings vs baseline still computed

---

## 6. Feeder Berth Conflict Scenario

### 6.1 Run with Feeder Berth Conflict Scenario

- [ ] Select `Feeder Berth Conflict` from scenario dropdown
- [ ] Click `Run`
- [ ] OptETruck shows ~22 available trucks
- [ ] Confidence shows ~75%

### 6.2 Inject Berth Conflict

- [ ] During Monitor phase (after HITL-4), click `⚡ Berth Conflict`
- [ ] Monitor detects berth conflict
- [ ] HITL-5 card appears (Deviation Response)
- [ ] Agent output mentions berth conflict

### 6.3 HITL-5 Approval

- [ ] Click `Approve` on HITL-5
- [ ] Delta dispatch executes (4 trucks)
- [ ] Second Tuas loading sequence updates
- [ ] Workflow completes

### 6.4 Cost Breakdown (Deviation)

- [ ] Shows original + delta costs
- [ ] Total cost higher than Normal
- [ ] Savings vs baseline still positive

---

## 7. SSE Event Stream

### 7.1 Connect to SSE

```bash
# Open SSE stream
curl -N http://localhost:8000/agent/stream/{run_id} 2>&1 | head -50
```

- [ ] Stream connects successfully
- [ ] Events arrive in order

### 7.2 Event Types

Run a full flow and verify these events fire:

| Event | When | Expected Data |
|-------|------|---------------|
| `run_started` | Run begins | `run_id`, `scenario` |
| `trace_entry` | Each node | `node`, `step`, `duration_ms` |
| `tool_result` | Tool completes | `tool_name`, `output`, `confidence` |
| `tool_confirmation` | dispatch/hold/tuas | `tool_name`, `message` |
| `hitl_card` | HITL gate | `gate_id`, `confidence`, `risk_score` |
| `confidence_update` | Confidence changes | `confidence`, `source` |
| `cost_update` | Split computed | `optimal_split`, `total_transport_cost` |
| `run_complete` | Workflow done | `status`, `run_id` |

- [ ] All 8 event types observed
- [ ] No missing events in sequence
- [ ] `tool_result` for: `get_itt_candidates`, `check_road_itt_capacity`, `check_sea_itt_capacity`, `compute_itt_split`

### 7.3 SSE Replay

- [ ] Connect to SSE after run completes
- [ ] Historical events replayed
- [ ] No duplicate events

---

## 8. Reset Lifecycle

### 8.1 Reset During Run

```bash
# Start a run, then reset
curl -s -X POST http://localhost:8000/agent/create-event/pb-12-itt | python3 -m json.tool
# Run the agent, then:
curl -s -X POST http://localhost:8000/agent/reset/{run_id} -H "Content-Type: application/json" | python3 -m json.tool
```

- [ ] Run cancelled
- [ ] HITL timeouts cancelled
- [ ] Problem status reset to idle
- [ ] Frontend shows "No event received" in EventCard
- [ ] Status cards show awaiting state
- [ ] Can start new run immediately

### 8.2 Reset All

```bash
curl -s -X POST http://localhost:8000/agent/reset -H "Content-Type: application/json" | python3 -m json.tool
```

- [ ] All runs cleared
- [ ] SSE broadcaster cleared
- [ ] All HITL timeouts cancelled
- [ ] All problem statuses reset
- [ ] Edge cases cleared
- [ ] Frontend fully reset

### 8.3 Reset via UI

- [ ] Click `↺ Reset` button
- [ ] Frontend calls `resetRun()` or `resetAll()`
- [ ] SSE disconnects
- [ ] UI returns to initial state
- [ ] Can Simulate Webhook again

### 8.4 Stale Resume Rejection

```bash
# Create run, reset, try to resume
curl -s -X POST http://localhost:8000/agent/create-event/pb-12-itt | python3 -m json.tool
curl -s -X POST http://localhost:8000/agent/reset/{run_id} -H "Content-Type: application/json"
# Try to resume old run
curl -s -X POST http://localhost:8000/agent/resume/{run_id} -H "Content-Type: application/json" | python3 -m json.tool
```

- [ ] Returns 422 or error (stale resume rejected)
- [ ] No state corruption

---

## 9. Cost Dynamics

### 9.1 Normal Scenario Costs

Run Normal scenario and verify:

| Metric | Expected |
|--------|----------|
| Road containers | ~80 |
| Sea containers | ~40 |
| Road trips | ~60 |
| Road cost | ~$9,000 (60 × $150) |
| Sea handling | ~$1,400 (40 × $35) |
| Total | ~$10,400 |
| Baseline (all road) | ~$12,000 |
| Savings | ~$1,600 |

- [ ] Values within ±20% of expected
- [ ] Cost breakdown matches HITL-1 card
- [ ] Cost updates dynamically

### 9.2 Low Trucks Costs

| Metric | Expected |
|--------|----------|
| Road containers | ~36 (18 trucks × 2) |
| Sea containers | ~84 |
| Road trips | ~28 |
| Total | ~$7,260 |
| Savings | ~$4,740 |

- [ ] Fewer road containers than Normal
- [ ] More sea containers
- [ ] Lower total cost (less road trips)

### 9.3 Cost vs Baseline

- [ ] Baseline = all-road cost (trips × $150)
- [ ] Optimised = road + sea cost
- [ ] Savings = baseline - optimised
- [ ] ROI section shows per-incident savings

---

## 10. UI Details

### 10.1 Dashboard Layout

- [ ] Left column: EventCard/HITL + AgentOutput
- [ ] Right column: CostBreakdown + 4 SystemStatusCards
- [ ] No view switching (Dashboard always visible)
- [ ] Sidebar tabs: Dashboard, Agent Trace, History, Settings

### 10.2 System Status Cards

- [ ] CITOS: shows container count after ingest
- [ ] OptETruck: shows available trucks after ingest
- [ ] Feeder: shows berth status after ingest
- [ ] QC Terminal: shows crane availability after ingest
- [ ] Cards show "Will populate after webhook event" before run
- [ ] Cards populate progressively via SSE tool_result

### 10.3 Agent Output

- [ ] Shows humanized narrative (not raw JSON)
- [ ] Newest events first (default)
- [ ] Tool results show success/failure indicators
- [ ] Confidence updates reflected

### 10.4 WorkflowProgress

- [ ] 12 stages: Event → Ingest → Split → HITL-1 → Dispatch → HITL-2 → Hold → HITL-3 → Sequence → HITL-4 → Monitor → Done
- [ ] Idle = stage 0 (Event)
- [ ] Advances correctly through workflow
- [ ] HITL-5 does NOT advance progress (falls through to event-based)

### 10.5 Action Bar

- [ ] Problem dropdown: selectable, shows names
- [ ] Simulate Webhook button: creates event
- [ ] Scenario dropdown: Normal, Feeder Berth Conflict, Stale/Missing Data, Low Trucks
- [ ] ⚡ Berth Conflict button: injects edge case
- [ ] ↺ Reset button: full teardown

### 10.6 Browser Tab

- [ ] Title: "PSA Nexus"
- [ ] Dashboard title: "Nexus Dashboard"

---

## 11. Cross-Browser / Multi-Tab

### 11.1 Multiple Tabs

- [ ] Open 2 tabs to `http://localhost:5173`
- [ ] Run in Tab 1
- [ ] Tab 2 shows same state (via `GET /agent/active-run` polling)
- [ ] Approve HITL in Tab 1
- [ ] Tab 2 updates to show HITL-2

### 11.2 SSE Sharing

- [ ] Both tabs receive SSE events
- [ ] No duplicate processing
- [ ] State consistent across tabs

---

## 12. Error Cases

### 12.1 No Event, Click Run

- [ ] Without Simulate Webhook, Run button not available
- [ ] Or Run gracefully handles missing event

### 12.2 Duplicate Run

```bash
# Start run, try to start another
curl -s -X POST http://localhost:8000/agent/run-event -H "Content-Type: application/json" -d '{"event": {...}, "scenario": "nominal", "problem_id": "pb-12-itt"}'
curl -s -X POST http://localhost:8000/agent/run-event -H "Content-Type: application/json" -d '{"event": {...}, "scenario": "nominal", "problem_id": "pb-12-itt"}'
```

- [ ] Second run rejected or queued
- [ ] First run not corrupted

### 12.3 Invalid Scenario

```bash
curl -s -X POST http://localhost:8000/agent/run-event -H "Content-Type: application/json" -d '{"event": {...}, "scenario": "nonexistent", "problem_id": "pb-12-itt"}'
```

- [ ] Falls back to nominal scenario
- [ ] No crash

### 12.4 Network interruption

- [ ] Disconnect network during run
- [ ] Reconnect → SSE reconnects
- [ ] State恢复 from backend

---

## 13. Performance

### 13.1 Run Duration

- [ ] Normal scenario: completes in <30 seconds
- [ ] All scenarios: completes in <60 seconds
- [ ] No hangs at HITL gates

### 13.2 SSE Latency

- [ ] Events arrive within 1 second
- [ ] No significant lag between action and UI update

---

## 14. Sign-Off

| Section | Status | Notes |
|---------|--------|-------|
| 1. YAML Ingestion | | |
| 2. Happy Path | | |
| 3. HITL Interactions | | |
| 4. Stale Scenario | | |
| 5. Low Trucks | | |
| 6. Feeder Berth Conflict | | |
| 7. SSE Events | | |
| 8. Reset Lifecycle | | |
| 9. Cost Dynamics | | |
| 10. UI Details | | |
| 11. Cross-Browser | | |
| 12. Error Cases | | |
| 13. Performance | | |

**Overall**: PASS / FAIL

**Date**: _______________
**Tester**: _______________
