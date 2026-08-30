# PSA Nexus — Demo Guide (Plain English)

> Open `http://localhost:8000/ui/` → Left menu: Dashboard | Trace | History | Settings — Top bar: menu button + light/dark switch

## 1. Dashboard — The Main Demo
```
Top: job name + how sure AI is (%) + risk [Low green / Medium yellow / High red]
Controls: pick job -> pick situation -> create alert -> run -> approve 4 steps -> handle emergency if needed -> see results -> reset
```

**a) Choose what to show**
- `Job` dropdown → same AI handles different jobs (Move Containers / Fix Berth Delay / etc) — switching swaps the whole checklist instantly
- `Situation` dropdown → Normal / Ship Blocked / Missing Data / Few Trucks — changes the fake data for the run

**b) Create the alert**
- Click `Simulate` → creates an alert card. Before click it says "No event — click Simulate"
- After click card shows: alert type, where it came from, ship name, container count + dangerous goods, route (PPT → Tuas), priority, who asked, departure time → then click `Run` (shows Starting... spinner, then running)

**c) Follow the top progress bar (12 steps)**
```
Alert → Check Containers → Make Plan → Approve Plan → Send Trucks → Approve Trucks → Hold Ship → Approve Hold → Plan Cranes → Approve Cranes → Watch for Problems → Done
```
Grey = waiting, blue ring + clock = now, green tick = done. It moves automatically as you approve.

**d) Buttons during the run**
- `Create Problem` (lightning) → only works mid-run → fakes a ship dock blocked → Ship card turns red → AI spots it → adds Emergency approval at the end
- `Reset` → clears job, progress, log, cost, and all 4 status cards back to dashed "awaiting" — also shows short job ID badge while running
- Help (?) icons on cost + status cards → hover to see plain explanation

## 2. The Approval Pop-ups (center left — you must approve before AI spends money or moves anything)
```
Plan → Trucks → Ship Hold → Crane Order → [if problem injected → Emergency Fix]
```
Every pop-up shows: AI confidence %, risk shield, time left before it auto-escalates, and a box to type why you reject.

1. **Approve the Plan** — "Move 80 by road ($9,000, 60 truck trips) + 40 by sea ($1,400) = $10,400 total, saves $1,600 vs sending all by road ($12,000)" + shows other options → Buttons: `Approve / Reject / Change number` (type how many by road, sea auto-updates)
2. **Approve Trucks** — "Send X trucks, Y trips (e.g. 2 trucks do 2 trips + 1 truck does 1 trip), route West Coast → AYE → Tuas, arrives ~2:30pm, costs $X" + trip breakdown → `Approve / Reject`
3. **Approve Ship Hold** — "Hold ship 1 hour costs $800 ($800/hr), moves departure 2pm → 3pm, tide risk = ok / tight / dangerous, operator said yes/no" → `Approve / Reject`
4. **Approve Crane Order** — "Unload ship MV PACIFIC STAR order: Bay 14 → 12 → 10 → 08, cranes QC-07 → Bay 14 etc, finishes 30 min before ship leaves" → `Approve / Reject`
5. **Emergency Fix** (red, only if ship blocked / low confidence / too expensive) — "Old plan 80/40 $10,400 vs New plan 100/20 $11,200 = +$800 extra, needs +4 trucks, reason: dock blocked" side-by-side → `Approve` to re-plan

## 3. Live Info While AI Works

**Middle — AI Log (Agent Output)**
- Plain English lines with time: "checking containers" (blue) → "inventory ready" (green) → "waiting for your approval" (yellow) → "problem found!" (orange) → "done" (green)
- `Newest / Oldest` button flips order, auto-scrolls, says "Waiting for events — click Run" if empty

**Top Right — Cost Box (changes per step)**
- Normally: Road $ + Sea $ = Total, vs All-Road baseline, green "Save $X (X%)" or red "Over $X", plus table of Other Options (Road/Sea split | Cost | Risk)
- During Trucks step: shows Trucks / Trips / Route / ETA / dispatch cost
- During Ship Hold step: shows Hours / Cost / rate / new departure / tide risk badge
- During Crane step: shows ship name + bay order + crane moves + finish time
- During Emergency: shows Old vs New vs Extra cost side-by-side + reason + truck delta
- ? icon explains: baseline = all trucks, sea is free ship + $35 per container handling only

**Right — 4 Status Cards (fill in as AI checks them — dashed "awaiting" first, then solid + progress bar + colored dot)**
- `Containers Ready` — total units, big (40ft) + small (20ft) count, dangerous goods, blocks, dot green if data fresh (<10 min) / yellow if stale — hover ? for detail
- `Trucks` — available / total, drive time minutes, road = normal/busy, $150 per trip, dot green if many trucks / yellow if few
- `Ship` — how full (used / total), dot green = docked / yellow = free / red = blocked, departure window, hold cost per hour — hover ? explains miss if tide late
- `Cranes` — working / total cranes at destination, berth name, dot green if most cranes free / red if none — shows live crane list when filled

## 4. Trace Page (`/trace` via left menu)
```
Finish a run on Dashboard → click Trace → see full diary
```
- Top: `Run: xxxx` + `Trace (N steps)` + `Newest ↓ / Oldest ↑` button
- Each row: `# | what AI did | type [tool blue / approval yellow / warning red / done green] | time | arrow to expand full detail (JSON)`
- If no run: "No active run — start a demo" or "Waiting for steps..."
- Updates live while job runs

## 5. History Page (`/history` via left menu)
```
All past runs → History
```
- Top: `X runs`
- Each card: job name | status [done green / running blue / failed red / waiting yellow] | start date + time | how long it took (e.g. 43s, 1m 12s)
- Click arrow to expand: full job ID, situation name, summary → `View full trace →` jumps to Trace page for that run
- If none: "No runs yet — start a demo"

## 6. Settings Page (`/admin` via left menu)
```
Login → see AI status → add keys / change AI → logout
```
- **Login card** — username + password + Login button (shows error in red if wrong) — if already logged in, skips to settings
- **AI Ready dot** — green dot + "Ready" or red dot + "Missing key for X" message
- **Add API Key card** — boxes: Provider (anthropic/openai/gemini...) + API Key (hidden) + `Add Key` button → shows "Key added" or error
- **AI Setup card** — `Saved` tick appears after each edit (auto-saves half-second after typing):
  - Primary AI: Provider dropdown, Model name, Web address (leave blank for default), Key name
  - Backup AI: same fields + "None" option (used if primary fails)
- **Key Status row** — small tags `provider: ok / missing`
- **Logout** — top right button clears session

## 7. Quick Demo Script (2 min normal + 1 min problem)
```
Normal: Job=Move Containers + Situation=Normal → Simulate → Run → watch progress bar move + log fill + cost + 4 cards turn from dashed to solid → Approve Plan → Approve Trucks → Approve Ship → Approve Cranes → Watch → Done → open History (see run) → open Trace (expand a step)
Problem: Run again → halfway click Create Problem → Ship card flips to red Blocked → Watch step shows warning → Emergency card Old vs New → Approve → Done
Extra to brag: try Situation=Missing Data (card goes yellow) / switch Job to Fix Berth (only 2 approvals, different cards) / go Settings → change AI brain → Run again with new brain
```
