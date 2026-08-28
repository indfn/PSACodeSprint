# Phase 7: Web UI — PSA Nexus Tactical Console

## Goal
Build the PSA Nexus dashboard — a tactical telemetry operations console with real-time SSE streaming, step-by-step agent trace, run history, HITL approval cards, edge injection controls, and problem switching. Industrial brutalist dark theme. Vanilla HTML/CSS/JS. All old UI bugs eliminated.

## Depends on
Phase 6, Phase 6.7 (admin API), Phase 6.5 (SSE broadcaster, HITL timeout scheduler)

## Requirements
U-01 through U-12 (requirements.md)

## Success Criteria
1. Dashboard loads with tactical telemetry aesthetic — dark CRT, monospace data, visible grid borders, red accent
2. SSE streams agent events in real time with replay buffer and `Last-Event-ID` support
3. HITL cards appear one at a time, approve/reject/modify all work inline (no popups, no hanging cards, no multiple cards)
4. Rejection reason uses inline text field (no browser `prompt()`)
5. Modify expands card with editable fields, submit completes the action
6. Stale HITL returns 422 shown as inline error (not crash)
7. Edge injection sidebar works on both Dashboard and Agent Trace tabs
8. Data visualizer shows live mock API data (containers, trucks, feeder, QC)
9. Agent trace shows human-readable step list with expandable detail
10. History tab shows past runs with expandable traces
11. Problem switcher dropdown in header changes active problem
12. Admin page accessible via `/admin` link (not a tab)
13. Notifications appear as bell icon with dropdown
14. No `prompt()`, no `alert()`, no `confirm()` anywhere
15. 183+ tests still pass (no backend regressions)

---

## Design System — Tactical Telemetry

### Archetype
**Tactical Telemetry & CRT Terminal** — dark mode, high-density tabular data, monospace typography, ASCII framing devices, simulated analog degradation.

### Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| **Background** | `#0A0A0A` | Page bg — deactivated CRT |
| **Surface 1** | `#141414` | Panel/card bg |
| **Surface 2** | `#1C1C1C` | Hover/secondary surface |
| **Border** | `#2A2A2A` | Grid dividers, compartmentalization |
| **Border strong** | `#3A3A3A` | Active/selected states |
| **Text primary** | `#EAEAEA` | White phosphor — primary text |
| **Text secondary** | `#888888` | Metadata, labels |
| **Text muted** | `#555555` | Disabled, hints |
| **Accent red** | `#E61919` | Alerts, escalation, vital highlights, HITL-5 |
| **Status green** | `#4AF626` | Single use: agent online / success status |
| **Warning amber** | `#C89B3C` | Confidence warning, timeout approaching |
| **Mono font** | JetBrains Mono | All data, numbers, codes |
| **Body font** | IBM Plex Mono | Labels, descriptions, secondary text |

### Typography Rules
- **ALL micro-type is UPPERCASE** — labels, nav, metadata, status codes
- **Macro headers** — massive, tight tracking (`-0.04em`), compressed leading (`0.9`)
- **Data numbers** — JetBrains Mono, tabular figures, generous tracking (`0.06em`)
- **No serif anywhere. No Inter anywhere.**

### Layout Principles
- Strict CSS Grid with visible `1px` borders (`#2A2A2A`) between cells
- `border-radius: 0` on everything — mechanical rigidity
- Bimodal density: extreme data clusters vs calculated negative space
- ASCII framing: `[ STATUS ]`, `>>>`, `///`, `+`
- No gradients, no drop shadows, no translucency, no blur

### CRT Effects (Subtle)
- Scanlines: `repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.015) 2px, rgba(255,255,255,0.015) 4px)` on `body::after`
- Grain: SVG noise filter at low opacity (`0.03`) on `body::before`
- Both `pointer-events: none`, fixed position, full viewport
- `@media (prefers-reduced-motion: reduce)` disables all effects

### Accessibility
- `aria-live="polite"` on SSE streaming regions
- `role="alert"` on escalation/error notifications
- `focus-visible` ring on all interactive elements
- 4.5:1+ contrast on all text
- Icon + color for every status (never color-only)

---

## Architecture

### File Structure
```
app/ui/
  index.html      — single-page app (dashboard + trace + history tabs)
  style.css        — all styles (design system tokens as CSS custom properties)
  app.js           — all interactivity (SSE, tabs, HITL, edge controls, history)
  admin.html       — admin page (separate, auth-guarded via API)
  admin.js         — admin interactivity
```

### Why Vanilla HTML/CSS/JS
- No build tools, no npm, no React — instant load, zero dependencies
- FastAPI serves files directly via `StaticFiles`
- Judges see the UI immediately on `localhost:8000`
- Fits the brutalist ethos: raw, functional, no abstraction layers

### Backend Consumption Map

| UI Feature | Backend Endpoint | Method |
|------------|-----------------|--------|
| Start demo | `POST /agent/run-demo` | Fetch |
| SSE stream | `GET /agent/stream/{run_id}` | EventSource |
| HITL respond | `POST /agent/hitl/respond` | Fetch |
| Agent trace | `GET /agent/trace/{run_id}` | Fetch |
| Active problem | `GET /agent/active-problem` | Fetch |
| Switch problem | `POST /agent/switch-problem/{id}` | Fetch |
| Inject edge | `POST /agent/inject-edge-case` | Fetch |
| Reset mocks | `POST /agent/reset-mocks` | Fetch |
| Run history | `GET /webhook/runs` | Fetch |
| Container data | `GET /api/citos/ppt/containers` | Fetch |
| Truck data | `GET /api/optetruck/capacity` | Fetch |
| Feeder data | `GET /api/feeder/FEEDER%20ATLANTIC-03` | Fetch |
| Loading seq | `GET /api/citos/tuas/loading-sequence` | Fetch |
| Notifications | SSE `notification` events | EventSource |

---

## Tab Structure

### Header (persistent across all tabs)
```
+--[PSA NEXTO]-----[PB-12 v]---[confidence: 0.92]---[risk: 0.15]---[bell]---[admin]---+
```
- Left: Logo/title (`PSA NEXTO` in massive type)
- Center: Problem switcher dropdown (`PB-12 ITT` / `PB-01 Berth`)
- Center-right: Live confidence + risk scores (monospace, green/amber/red)
- Right: Bell icon (notification count badge) + Admin link
- Tab bar below: `[DASHBOARD]` `[AGENT TRACE]` `[HISTORY]`
- Active tab: red underline, uppercase

### Tab 1: Dashboard

**Layout: 2-column with top strip**

```
+--[TOP STRIP: Problem: PB-12 ITT Coordination | Systems: PPT, Tuas, OptETruck, Feeder, PortNet]--+
|                                                                                                 |
+--[LEFT COLUMN]------------------------+--[RIGHT COLUMN]---------------------------------------+
| [DATA VISUALIZER]                     | [HITL APPROVAL]                                       |
| [CITOS PPT]                           |                                                                           |
| Containers: ████████████░░ 120/120    |  [Card: Approve ITT Split]                            |
| Ready: 120  DG: 3  Blocks: B-07..14  |  Road: 80 | Sea: 40                                  |
|                                       |  Cost: $10,400 vs $12,000 baseline                   |
| [OPTETRUCK]                           |  [APPROVE] [REJECT] [MODIFY]                         |
| Trucks: ██████████████░░ 50/55        |                                                       |
| Available: 50  Transit: 90min         |  (when reject clicked → inline text field appears)    |
|                                       |  (when modify clicked → card expands with fields)     |
| [FEEDER - ATLANTIC-03]                |                                                       |
| Status: BERTHED @ PPT B12            |  (when no HITL pending → "No pending approvals" msg)  |
| Capacity: ████████░░ 620/800 TEU      |                                                       |
| Depart: 14:00-16:00                   |                                                       |
|                                       |                                                       |
| [TUAS QC]                             |                                                       |
| QC-07: Bay14, Bay12 (road@14:30)     |                                                       |
| QC-08: Bay10, Bay08 (sea@16:30)      |                                                       |
+---------------------------------------+-------------------------------------------------------+
```

**Data Visualizer details:**
- Each API = one block with monospace header (`[CITOS PPT]`, `[OPTETRUCK]`, etc.)
- Status bars: `█` filled, `░` empty — pure CSS `div` with background color
- Numbers: JetBrains Mono, tabular figures
- Green (`#4AF626`) for healthy, amber (`#C89B3C`) for warning, red (`#E61919`) for critical
- Data refreshes: on demo start, after each HITL approval, on manual refresh button
- Fetches from mock API endpoints directly (not from agent state)

**HITL Card details:**
- ONE card visible at a time (the current `hitl_pending` from SSE `hitl_card` events)
- Card structure:
  ```
  +--[HITL-1: APPROVE ITT SPLIT]------------------+
  | Gate: HITL-1 | Timeout: 30min | Action: escalate|
  |                                                   |
  | Road: 80 containers (60 trips, $9,000)           |
  | Sea:  40 containers ($1,400 handling)            |
  | Total: $10,400 vs baseline $12,000               |
  | Savings: $1,600 (13.3%)                          |
  |                                                   |
  | [APPROVE]  [REJECT]  [MODIFY]                    |
  +---------------------------------------------------+
  ```
- **APPROVE**: POST `/agent/hitl/respond` with `decision: "approve"`, card disappears, wait for next
- **REJECT**: Inline text field slides open below buttons: `Reason: [________________] [CONFIRM REJECT] [CANCEL]`
- **MODIFY**: Card expands to show editable fields (e.g., road_containers input, sea_containers input). `[SUBMIT MODIFICATION] [CANCEL]`
- **422 stale**: Error message appears inside card: `HITL TIMED OUT — status: halted` in red
- **Timeout countdown**: Monospace countdown in card header showing remaining time

### Tab 2: Agent Trace

**Layout: Single column, scrollable**

```
+--[AGENT TRACE: run-abc123]---[status: waiting_hitl]---[duration: 12.3s]-----+
|                                                                              |
| [01] INGEST EVENT                                           14:30:01.234    |
|      Received ITT coordination request from CITOS PPT                       |
|      Vessel: MV PACIFIC STAR | Containers: 120 | Priority: high             |
|                                                                              |
| [02] QUERY CONTAINERS                                      14:30:02.156    |
|      Tool: get_itt_candidates (CITOS PPT)                                   |
|      Result: 120 containers ready, 3 DG, 4 blocks affected                  |
|      >>> click to expand full response                                       |
|                                                                              |
| [03] QUERY TRUCKS                                          14:30:03.089    |
|      Tool: check_road_itt_capacity (OptETruck)                              |
|      Result: 50 trucks available, 90min transit, $150/trip                  |
|                                                                              |
| [04] COMPUTE SPLIT                                         14:30:04.201    |
|      Tool: compute_itt_split                                                 |
|      Result: 80 road / 40 sea = $10,400 (saves $1,600)                     |
|                                                                              |
| [05] HITL-1: WAITING APPROVAL                             14:30:04.456    |
|      >>> Approve ITT split (road:80 / sea:40)                               |
|                                                                              |
| [06] DISPATCH ROAD ITT (after approval)                   14:32:15.789    |
|      Tool: dispatch_road_itt                                                 |
|      Result: 60 truck trips dispatched                                      |
|                                                                              |
| ... (more steps)                                                             |
+------------------------------------------------------------------------------+
```

**Trace step structure:**
- Step number: `[01]`, `[02]`, etc. — monospace, red for HITL steps
- Description: UPPERCASE action name (e.g., `QUERY CONTAINERS`)
- Timestamp: right-aligned, monospace
- Tool name + system in parentheses (if tool call)
- Result summary: one-line human readable
- **Click to expand**: full JSON response in `<pre>` block with monospace styling
- **SSE-driven**: steps appear in real time as `trace_entry` events arrive
- **No raw orchestrator logs** — only human-readable summaries

**Step mapping (what each agent action becomes):**

| Agent Action | Trace Label | Details |
|-------------|-------------|---------|
| Webhook received | `INGEST EVENT` | Event type, source, priority, container count |
| Tool call (T1) | `QUERY CONTAINERS` | Tool name, system, result summary |
| Tool call (T2) | `QUERY TRUCKS` | Capacity, transit time |
| Tool call (T3) | `QUERY FEEDER` | Berth status, capacity, departure window |
| Tool call (T4) | `COMPUTE SPLIT` | Road/sea ratio, cost, savings |
| Tool call (T5) | `UPDATE LOADING SEQ` | QC assignments, ETA |
| HITL interrupt | `HITL-N: WAITING` | Gate name, what needs approval |
| HITL decision | `HITL-N: APPROVED/REJECTED` | Decision, reason (if reject) |
| Monitor re-query | `MONITOR: CHECK STATUS` | What changed, deviation detected |
| Re-compute | `RECOMPUTE SPLIT` | New ratio after deviation |
| HITL-5 escalation | `ESCALATION` | Trigger, who it's escalated to |
| Dispatch (post-approval) | `DISPATCH ROAD/FEEDER` | What was dispatched |
| Completion | `COMPLETED` | Final status, total cost, duration |

### Tab 3: History

**Layout: Card grid, scrollable**

```
+--[RUN HISTORY]----------------------------------------------------------------+
|                                                                              |
| +--[run-abc123]---[PB-12 ITT]---[COMPLETED]---[14:30 - 14:35]---[5m 12s]-+ |
| | 120 containers PPT→Tuas | 80/40 split | $10,400 | 5 HITL gates passed   | |
| | >>> click to expand trace                                                | |
| +---------------------------------------------------------------------------+ |
|                                                                              |
| +--[run-def456]---[PB-12 ITT]---[HALTED]---[14:40 - 14:45]---[HITL-5]----+ |
| | Deviation detected: feeder berth conflict | escalated to duty manager    | |
| | >>> click to expand trace                                                | |
| +---------------------------------------------------------------------------+ |
|                                                                              |
| +--[run-ghi789]---[PB-01 BERTH]---[COMPLETED]---[15:00 - 15:02]---[2m]-+   |
| | Berth reassignment completed | 3 vessels affected                      |   |
| | >>> click to expand trace                                              |   |
| +-----------------------------------------------------------------------+   |
+------------------------------------------------------------------------------+
```

**History card structure:**
- Header: run_id, problem ID, status badge (color-coded), timestamp range, duration
- Summary: one-line key outcome
- **Click to expand**: full agent trace (same format as Agent Trace tab)
- **SSE replay**: can replay SSE events from buffer for completed runs
- Data source: `GET /webhook/runs` + `GET /agent/trace/{run_id}`
- Auto-refreshes when new run completes

---

## Edge Injection Sidebar

**Slide-out panel, visible on Dashboard and Agent Trace tabs.**

**Trigger:** Gear icon (`⚙`) in tab bar area, fixed position
**Behavior:** Slides in from right, 320px wide, dark surface (`#141414`)

```
+--[EDGE CONTROLS]--[X]--+
|                          |
| INJECT EDGE CASE         |
|                          |
| [FEEDER BERTH CONFLICT] |
| Mutates feeder data to   |
| conflict state. Affects  |
| next monitor check.      |
| >>> INJECT               |
|                          |
| [STALE DATA]             |
| Sets data age to 25min.  |
| Triggers staleness       |
| guard on next query.     |
| Minutes: [25]            |
| >>> INJECT               |
|                          |
| --- STATUS ---            |
| Last inject: none        |
| Mock state: clean        |
|                          |
| [RESET ALL MOCKS]        |
+--------------------------+
```

**Inject buttons:**
- `POST /agent/inject-edge-case` with `case: "feeder_berth_conflict"` or `case: "stale_data"`
- After inject: status updates to show what was injected
- `POST /agent/reset-mocks` resets everything

**Key fix from old UI:** Edge buttons must actually call the API and show feedback. Old UI buttons were disconnected.

---

## Notification System

**Bell icon in header with dropdown.**

- Bell icon: SVG, no emoji
- Badge: red circle with count number (monospace)
- Dropdown: list of recent notifications (max 20)
- Each notification: message text, parties list, timestamp
- Source: SSE `notification` events + `notification_log` from `app/mocks/data.py`
- Auto-clears badge on open

---

## Sub-Phase Breakdown

### 7.1 — CSS Design System + HTML Shell
**Goal:** Establish the complete design system as CSS custom properties, build the HTML skeleton with all three tabs, header, and navigation.

**Files:** `style.css`, `index.html`

**Tasks:**
1. Create `app/ui/style.css` with CSS custom properties for all design tokens
2. Implement CRT effects (scanlines, grain) as `body::before`/`body::after` pseudo-elements
3. Build `app/ui/index.html` with semantic HTML structure:
   - `<header>` with logo, problem switcher, confidence/risk, bell, admin link
   - `<nav>` with three tab buttons
   - `<main>` with three tab panels (dashboard, trace, history)
   - Edge injection sidebar (hidden by default)
   - Notification dropdown (hidden by default)
4. CSS Grid layout for dashboard (2-column + top strip)
5. CSS Grid layout for trace (single column)
6. CSS Grid layout for history (card grid)
7. All typography: JetBrains Mono + IBM Plex Mono via Google Fonts CDN
8. ASCII decorative elements (`[ STATUS ]`, `>>>`, borders)
9. Focus-visible rings on all interactive elements
10. `prefers-reduced-motion` media query disabling effects

**Verification:** Page loads in browser, all three tabs switch correctly, design tokens apply, CRT effects visible but subtle, fonts load.

### 7.2 — Header + Navigation + Tab Switching
**Goal:** Functional header with problem switcher, live confidence/risk, notification bell, admin link, and tab switching.

**Files:** `app.js` (new), `index.html`, `style.css`

**Tasks:**
1. `app.js` — tab switching logic (click tab → show panel, hide others, update active state)
2. Problem switcher dropdown:
   - Fetch `GET /agent/active-problem` on load
   - Populate dropdown with available problems
   - On change: `POST /agent/switch-problem/{id}`, update header info
3. Confidence + risk display:
   - Default values from active problem
   - Updates via SSE `confidence_update` events
   - Color coding: green (>0.85), amber (0.7-0.85), red (<0.7)
4. Admin link: `<a href="/admin">ADMIN</a>` — separate page
5. Notification bell:
   - Badge count from SSE `notification` events
   - Click to toggle dropdown
   - Dropdown lists recent notifications
   - Clear badge on open

**Verification:** Tab switching works, problem switcher calls API and updates display, confidence updates from SSE, notification bell shows count and dropdown.

### 7.3 — SSE Connection + Event Handling
**Goal:** Robust SSE connection with replay, heartbeats, and event routing to UI components.

**Files:** `app.js`

**Tasks:**
1. `connectSSE(run_id)` function:
   - Creates `EventSource` for `/agent/stream/{run_id}`
   - Handles `Last-Event-ID` header for replay
   - Reconnects on error with exponential backoff
   - Handles heartbeat comments (ignore, keep alive)
2. Event router: dispatches each SSE event type to handler:
   - `agent_thinking` → trace step (human-readable summary)
   - `tool_call` → trace step (tool name + params)
   - `tool_result` → trace step (result summary)
   - `hitl_card` → show HITL card in dashboard
   - `escalation` → notification + trace step
   - `trace_entry` → trace step
   - `confidence_update` → update header confidence
   - `deviation` → notification + trace step
   - `notification` → bell notification
3. Event buffer: store events in memory for history replay
4. Connection status indicator in header (green dot = connected, red = disconnected)

**Verification:** Start demo → SSE connects → events appear in trace in real time → confidence updates → notifications appear in bell.

### 7.4 — HITL Card System (Critical Bug Fix)
**Goal:** Single sequential HITL card with working approve/reject/modify. No popups, no stacking, no hanging cards.

**Files:** `app.js`, `style.css`, `index.html`

**Backend contract:**
- SSE `hitl_card` event data: `{gate_id, gate_name, approval_card, confidence, risk_score, timeout_seconds, timeout_action}`
- `POST /agent/hitl/respond` payload: `{run_id, decision: "approve"|"reject"|"modify", gate_id, reason?, modifications?}`
- Returns: `{status: "waiting_hitl"|"completed", hitl_card?}` or 422 if stale

**Tasks:**
1. HITL card renderer:
   - Only ONE card visible at any time
   - Card shows gate name, description, approval_card data (formatted per gate type)
   - Countdown timer showing remaining time before timeout
   - Three buttons: APPROVE, REJECT, MODIFY
2. Approve flow:
   - Click APPROVE → POST `/agent/hitl/respond` with `decision: "approve"`
   - Card shows "APPROVED" state briefly, then disappears
   - If response has new `hitl_card`, show next card
   - If response status is "completed", show completion state
3. Reject flow:
   - Click REJECT → inline text field appears below buttons
   - Type reason → click CONFIRM REJECT → POST with `decision: "reject", reason: "..."`
   - Or click CANCEL → text field disappears, back to normal card
   - **No browser `prompt()` — everything inline**
4. Modify flow:
   - Click MODIFY → card expands to show editable fields
   - Fields derived from `approval_card` content (e.g., road_containers, sea_containers)
   - Edit values → click SUBMIT MODIFICATION → POST with `decision: "modify", modifications: {...}`
   - Or click CANCEL → collapse back to normal card
   - **Card does NOT hang — submission always closes card**
5. Stale handling:
   - If POST returns 422 → show error message inside card: `[HITL TIMED OUT — status: {status}]`
   - Card stays visible for 5 seconds then disappears
   - No alert, no popup
6. Loading state:
   - While waiting for POST response, buttons show loading state (disabled, spinner text)
   - Prevent double-clicks

**Verification:** Start demo → HITL-1 card appears → approve → card disappears → HITL-2 appears → reject with reason → card disappears → modify with field edit → submit → card disappears → all 5 gates pass or some reject/timeout. No popups. No stacking. No hanging.

### 7.5 — Data Visualizer
**Goal:** Live status bars showing mock API data for each PSA system.

**Files:** `app.js`, `style.css`, `index.html` (dashboard panel)

**Data sources (direct fetch, not from agent state):**
- `GET /api/citos/ppt/containers` → container count, breakdown, DG, blocks
- `GET /api/optetruck/capacity` → trucks available, transit time
- `GET /api/feeder/FEEDER%20ATLANTIC-03` → berth status, capacity, departure
- `GET /api/citos/tuas/loading-sequence` → QC assignments, ETA

**Tasks:**
1. Data fetcher function: fetches all four endpoints in parallel
2. Renderer for each system block:
   - `[CITOS PPT]` — container bar (X/120), DG count, blocks list
   - `[OPTETRUCK]` — truck bar (X/50), transit time, cost/trip
   - `[FEEDER]` — capacity bar (X/800 TEU), berth status, departure window
   - `[TUAS QC]` — QC assignments (QC-07: Bay14, Bay12), ETA
3. Status bar CSS: pure div with `background` for fill, `background: #1C1C1C` for empty
4. Color coding: green (healthy), amber (warning), red (critical)
5. Refresh triggers: demo start, after each HITL approval, manual refresh button
6. Last-updated timestamp per block

**Verification:** Dashboard shows four data blocks with bars and numbers. Data matches mock API responses. Bars update after demo actions.

### 7.6 — Agent Trace (Step-by-Step)
**Goal:** Human-readable step list with expandable detail, driven by SSE events.

**Files:** `app.js`, `style.css`, `index.html` (trace panel)

**Tasks:**
1. Trace step renderer:
   - Each step: number badge, action label (UPPERCASE), timestamp, one-line summary
   - Red badge for HITL steps, green for completions, white for normal
   - Click to expand: full JSON in `<pre>` block
2. SSE event → trace step mapping:
   - `agent_thinking` → step label: `REASONING`, summary: first 100 chars of thought
   - `tool_call` → step label: `TOOL: {tool_name}`, summary: key params
   - `tool_result` → appends to previous tool_call step, shows result summary
   - `hitl_card` → step label: `HITL-N: WAITING`, summary: gate name
   - `trace_entry` → uses `step` and `event_type` from data
   - `escalation` → step label: `ESCALATION`, summary: trigger + who
   - `deviation` → step label: `DEVIATION`, summary: what changed
3. Auto-scroll: new steps appear at bottom, auto-scroll if user is at bottom
4. Step counter in tab header: `[AGENT TRACE: run-abc123] [12 steps] [STATUS]`
5. Empty state: `[ NO TRACE DATA — START A DEMO ]`

**Verification:** Start demo → steps appear in real time → click step → expands to show full detail → scroll back up → auto-scroll resumes when at bottom.

### 7.7 — History Tab
**Goal:** Past run cards with expandable traces, SSE replay capability.

**Files:** `app.js`, `style.css`, `index.html` (history panel)

**Tasks:**
1. Fetch runs on tab open: `GET /webhook/runs`
2. Run card renderer:
   - Header: run_id, problem_id, status badge, timestamp, duration
   - Summary: key outcome (containers, split, cost)
   - Click to expand: full trace (same as Agent Trace format)
3. SSE replay for expanded trace:
   - Replay buffered events from `broadcaster.get_buffered(run_id)`
   - Reconstruct trace steps from buffered events
4. Auto-refresh: poll `/webhook/runs` every 10 seconds when tab is active
5. Empty state: `[ NO RUN HISTORY — START A DEMO ]`
6. Status badges: COMPLETED (green), HALTED (red), WAITING (amber), FAILED (red)

**Verification:** Complete a demo run → history tab shows the run card → click to expand → trace appears. Start another run → history updates automatically.

### 7.8 — Edge Injection Sidebar
**Goal:** Slide-out panel for injecting edge cases, visible on Dashboard and Agent Trace tabs.

**Files:** `app.js`, `style.css`, `index.html`

**Tasks:**
1. Sidebar toggle: gear icon in tab bar → slide-in from right (320px)
2. Inject feeder conflict button:
   - `POST /agent/inject-edge-case` with `case: "feeder_berth_conflict"`
   - Show status feedback after inject
3. Inject stale data button:
   - Minutes input field (default 25)
   - `POST /agent/inject-edge-case` with `case: "stale_data", minutes: X`
   - Show status feedback
4. Reset mocks button:
   - `POST /agent/reset-mocks`
   - Clear inject status
5. Status display: shows current mock state (clean / injected / what case)
6. Close sidebar: X button or click outside

**Verification:** Open sidebar → inject feeder conflict → status shows "injected" → close sidebar → start demo → agent detects conflict → sidebar shows current state. Reset → clean.

### 7.9 — Notification Bell + Dropdown
**Goal:** Bell icon with count badge and notification list.

**Files:** `app.js`, `style.css`, `index.html` (header)

**Tasks:**
1. Bell icon: SVG, no emoji
2. Badge: red circle with count (monospace number)
3. Dropdown on click:
   - List of notifications (max 20)
   - Each: message, parties, timestamp
   - Scrollable if more than 5
4. Source: SSE `notification` events
5. Clear badge on dropdown open
6. Empty state: `[ NO NOTIFICATIONS ]`

**Verification:** During demo, notifications appear in bell dropdown. Count badge updates. Click opens dropdown, badge clears.

### 7.10 — Admin Page
**Goal:** Separate admin page at `/admin` with provider config, API key injection.

**Files:** `app/ui/admin.html`, `app/ui/admin.js`

**Tasks:**
1. `admin.html`: standalone page with same CRT theme
2. Login form: username + password → `POST /api/admin/login`
3. After login: show provider config (provider, model, base_url, api_type)
4. API key injection: masked input + save button → `POST /api/admin/api-key`
5. Provider readiness indicator (green/red)
6. Config editing: inject/confidence.threshold/cost_params
7. No link from dashboard to admin (secret URL `/admin`)

**Verification:** Navigate to `/admin` → login form → enter credentials → see config → inject API key → see readiness update.

### 7.11 — Bug Fixes + Polish
**Goal:** Fix all identified old-UI bugs, add final polish.

**Bugs to fix:**
1. ~~Multiple HITL cards popping up~~ → single card system (7.4)
2. ~~HITL cards don't work~~ → full approve/reject/modify flow (7.4)
3. ~~Modify hangs the card~~ → inline expand + submit (7.4)
4. ~~Rejection uses browser prompt()~~ → inline text field (7.4)
5. ~~Edge injection buttons don't do anything~~ → actual API calls + feedback (7.8)
6. ~~Orchestrator log unreadable~~ → human-readable trace steps (7.6)
7. ~~No data visualization~~ → status bars for mock APIs (7.5)
8. ~~Notifications not integrated~~ → bell dropdown (7.9)

**Polish:**
1. Loading states on all async operations (skeleton loaders)
2. Empty states for all panels (helpful messages)
3. Error states for failed API calls (inline, not alert)
4. Responsive: single column on mobile (<768px)
5. Keyboard navigation: tab through cards, enter to activate
6. Connection status indicator (SSE alive/dead)
7. ASCII decorative borders on all panels
8. `prefers-reduced-motion` respect

---

## Verification Strategy

### Manual Testing Checklist
1. Start demo → dashboard loads, data visualizer shows mock data
2. HITL-1 card appears → approve → card disappears → HITL-2 appears
3. HITL-2 → reject with reason → card disappears
4. Modify → edit field → submit → card disappears
5. All 5 HITL gates pass → run completes
6. Agent trace tab → steps appear in real time → click to expand
7. History tab → completed run appears → click to expand trace
8. Edge sidebar → inject feeder conflict → reset → clean
9. Problem switcher → switch to PB-01 → different tools/gates shown
10. Notification bell → notifications appear during demo
11. Admin page → login → see config → inject API key
12. SSE reconnect → events resume from Last-Event-ID
13. No `prompt()`, `alert()`, `confirm()` anywhere
14. No browser console errors
15. CRT effects visible but readable on projector

### Automated Testing
- All 183 existing tests pass (no backend regressions)
- No new backend changes needed — this is pure frontend

---

## Anti-Patterns (What We're NOT Doing)
- No React, no Next.js, no build tools
- No purple/blue AI gradients
- No emojis in code or UI
- No Inter font
- No `border-radius` (mechanical rigidity)
- No gradients, no drop shadows, no blur/translucency
- No `prompt()`, `alert()`, `confirm()`
- No centered hero sections
- No card stacking
- No generic card patterns (border + shadow + white bg)
- No color-only status indicators (always icon + text + color)
