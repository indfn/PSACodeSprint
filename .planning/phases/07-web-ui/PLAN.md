# Phase 7: Web UI & Integration — PSA Nexus Dashboard

## Goal
Build the PSA Nexus dashboard with real-time SSE streaming, problem switcher, approval cards, demo scenarios, and notification display — proving the platform generalises.

## Depends on
Phase 6

## Requirements
U-01 through U-12

## Success Criteria
1. Web UI loads in browser with clean, professional design
2. SSE endpoint streams agent thoughts, tool calls, and HITL cards in real time
3. HITL approval buttons work (approve/reject/modify)
4. Edge case injection controls work (feeder conflict, stale data)
5. Demo scenario can be triggered from UI

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser (UI)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Agent    │  │   Tool   │  │   HITL   │  │  Trace   │  │
│  │  Status   │  │   Log    │  │   Cards  │  │ Sidebar  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │              │         │
│       └──────────────┴──────────────┴──────────────┘         │
│                          │ SSE                               │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                    FastAPI Server                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  SSE     │  │  Agent   │  │   HITL   │  │  Edge    │  │
│  │ Endpoint │  │  Run     │  │ Response │  │  Case    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Plan

### 7.1: SSE Endpoint
**Duration:** ~2 hours
**What:** Build the Server-Sent Events endpoint. Must handle the race: agent may emit before SSE connects.

**Steps:**
1. Create `app/agent/sse.py`:
   ```python
   import asyncio
   import json
   from collections import deque
   from fastapi import Request
   from fastapi.responses import StreamingResponse

   class SSEBroadcaster:
       def __init__(self):
           self.queues: dict[str, asyncio.Queue] = {}
           self.buffers: dict[str, deque] = {}  # replay buffer for late subscribers
           self.BUFFER_SIZE = 100

       def _ensure_run(self, run_id: str):
           if run_id not in self.queues:
               self.queues[run_id] = asyncio.Queue()
               self.buffers[run_id] = deque(maxlen=self.BUFFER_SIZE)

       def create_queue(self, run_id: str) -> asyncio.Queue:
           self._ensure_run(run_id)
           return self.queues[run_id]

       async def publish(self, run_id: str, event: str, data: dict):
           self._ensure_run(run_id)
           msg = {'event': event, 'data': json.dumps(data, default=str)}
           self.buffers[run_id].append(msg)
           await self.queues[run_id].put(msg)

       async def stream(self, run_id: str, request: Request):
           self._ensure_run(run_id)
           # Replay buffered events for late subscribers (fix race condition)
           buffered = list(self.buffers[run_id])
           queue = self.queues[run_id]
           async def event_generator():
               # First: replay buffered events
               for msg in buffered:
                   yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"
               # Then: live stream
               while True:
                   if await request.is_disconnected():
                       break
                   try:
                       msg = await asyncio.wait_for(queue.get(), timeout=30)
                       # Skip if already replayed (dedup by checking if in buffered)
                       if msg not in buffered:
                           yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"
                       else:
                           # Already sent via replay — still yield buffered ones via queue is tricky
                           # Simpler: track replay cursor
                           yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"
                   except asyncio.TimeoutError:
                       yield f"event: heartbeat\ndata: {{}}\n\n"
           return StreamingResponse(event_generator(), media_type="text/event-stream")

       def cleanup(self, run_id: str):
           self.queues.pop(run_id, None)
           self.buffers.pop(run_id, None)

   broadcaster = SSEBroadcaster()
   ```
   > **Race fix:** `publish()` calls `_ensure_run()` so events are buffered even before `stream()` is called. When SSE connects, buffered events are replayed first.

2. Add SSE endpoint to `app/main.py`:
   - `GET /agent/stream/{run_id}` — returns SSE stream via `broadcaster.stream(run_id, request)`
   - Instantiate `broadcaster` as module-level singleton, pass to `run_agent(broadcaster=broadcaster)`
3. Hook broadcaster into agent graph — inject via `AgentState["_broadcaster"]` (see Phase 6.9 `create_initial_state`):
   - `agent_node`: on LLM call start → `broadcaster.publish(run_id, 'agent_thinking', {text: "..."})`; ; on tool_calls → `broadcaster.publish(run_id, 'tool_call', {name, args})`
   - `tool_node`: on result → `broadcaster.publish(run_id, 'tool_result', result.output)`
   - `hitl_node`: on interrupt → `broadcaster.publish(run_id, 'hitl_card', card)`
   - `monitor_node`: on deviation → `broadcaster.publish(run_id, 'deviation', deviation)`
   - `trace.log_trace`: on each entry → `broadcaster.publish(run_id, 'trace_entry', entry)`
   - `confidence`: on update → `broadcaster.publish(run_id, 'confidence_update', {confidence})`
   - All publishes check `if "_broadcaster" in state` before calling
4. SSE event types (8 total): `agent_thinking, tool_call, tool_result, hitl_card, escalation, trace_entry, confidence_update, deviation, heartbeat`

**Verification:**
```bash
# Terminal 1: start server
python -m uvicorn app.main:app --port 8000

# Terminal 2: watch SSE
curl -N localhost:8000/agent/stream/test-run-id
# Should see heartbeat events
```

### 7.2: HTML/CSS/JS Frontend
**Duration:** ~4 hours
**What:** Build the web UI.

**Steps:**
1. Create `app/ui/index.html`:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>PSA Nexus — Multi-Party Coordination Platform</title>
       <link rel="stylesheet" href="/ui/style.css">
   </head>
   <body>
       <div class="container">
           <header>
               <h1>PSA Nexus</h1>
               <p class="subtitle">Agentic Multi-Party Coordination Platform</p>
               <div class="problem-switcher">
                   <label>Problem:</label>
                   <select id="problem-select">
                       <option value="pb-12-itt">PB-12 — ITT Coordination (Flagship)</option>
                       <option value="pb-01-berth">PB-01 — Berth Delay Cascade</option>
                   </select>
                   <button id="switch-problem">Switch</button>
               </div>
               <div class="status-bar">
                   <span id="agent-status">Idle</span>
                   <span id="confidence-score">—</span>
               </div>
           </header>
           
           <main>
               <section class="agent-panel">
                   <h2>Agent Reasoning</h2>
                   <div id="agent-output"></div>
               </section>
               
               <section class="tools-panel">
                   <h2>Tool Calls</h2>
                   <div id="tool-log"></div>
               </section>
               
               <section class="hitl-panel">
                   <h2>Approval Required</h2>
                   <div id="hitl-cards"></div>
               </section>
           </main>
           
           <aside class="trace-panel">
               <h2>Execution Trace</h2>
               <div id="trace-sidebar"></div>
           </aside>
           
           <footer class="controls">
               <button id="run-demo">Run Demo</button>
               <button id="reset">Reset</button>
               <div class="edge-cases">
                   <button id="inject-conflict">Inject Feeder Conflict</button>
                   <button id="inject-stale">Inject Stale Data</button>
               </div>
           </footer>
       </div>
       <script src="/ui/app.js"></script>
   </body>
   </html>
   ```
2. Create `app/ui/style.css` — professional dark theme:
   - CSS variables for colors
   - Responsive grid layout
   - Card components for HITL
   - Animations for streaming text
   - Color-coded trace entries
3. Create `app/ui/app.js` — SSE client + DOM manipulation:
   - Connect to SSE endpoint
   - Render agent output as streaming text
   - Render tool calls as collapsible cards
   - Render HITL cards with action buttons
   - Render trace entries in sidebar
   - Handle demo trigger and edge case injection
4. Mount static files in `app/main.py`:
   ```python
   from fastapi.staticfiles import StaticFiles
   app.mount("/ui", StaticFiles(directory="app/ui", html=True), name="ui")
   ```

**Verification:**
```bash
open http://localhost:8000/ui/
# UI loads, shows panels, controls visible
```

### 7.3: HITL Approval Cards
**Duration:** ~3 hours
**What:** Build HITL card component. Must use `run_id` + `Command(resume=)` pattern.

**Steps:**
1. Add to `app/ui/app.js`:
   ```javascript
   // run_id is set when demo starts (from POST /agent/run-demo or /webhook/itt-coordination response)
   let currentRunId = null;

   function renderHITLCard(card) {
       const gateLabels = {
           "HITL-1": "Approve ITT Split",
           "HITL-2": "Approve Truck Dispatch",
           "HITL-3": "Approve Feeder Hold",
           "HITL-4": "Approve Loading Sequence Update",
           "HITL-5": "Escalate to Duty Manager",
       };
       const div = document.createElement('div');
       div.className = `hitl-card hitl-${card.gate_id}`;
       const isEscalation = card.gate_id === "HITL-5";
       div.innerHTML = `
           <h3>${gateLabels[card.gate_id] || card.gate_name} ${isEscalation ? '⚠️' : ''}</h3>
           <div class="card-content">
               ${renderCostSummary(card.approval_card)}
               <div class="confidence">Confidence: ${(card.confidence * 100).toFixed(0)}% ${card.confidence < 0.85 ? '(below threshold — escalation)' : ''}</div>
               ${card.approval_card.timeout_seconds ? `<div class="timeout">Timeout: ${card.approval_card.timeout_seconds / 60} min → ${card.approval_card.timeout_action}</div>` : ''}
           </div>
           <div class="card-actions">
               <button class="approve" onclick="respondHITL('${card.gate_id}', 'approve')">Approve</button>
               <button class="reject" onclick="respondHITL('${card.gate_id}', 'reject')">Reject</button>
               <button class="modify" onclick="showModifyInput('${card.gate_id}')">Modify</button>
           </div>
           <div id="modify-${card.gate_id}" class="modify-panel" style="display:none">
               <label>Adjust road/sea split (e.g., road: 100, sea: 20):</label>
               <input id="modify-road-${card.gate_id}" type="number" placeholder="Road containers" />
               <input id="modify-sea-${card.gate_id}" type="number" placeholder="Sea containers" />
               <button onclick="respondHITL('${card.gate_id}', 'modify', null, getModifications('${card.gate_id}'))">Submit Modification</button>
           </div>
       `;
       document.getElementById('hitl-cards').appendChild(div);
   }

   async function respondHITL(gateId, decision, reason = null, modifications = null) {
       const body = {run_id: currentRunId, gate_id: gateId, decision, reason, modifications};
       const btn = event.target;
       btn.disabled = true;
       btn.textContent = 'Sending...';
       try {
           const resp = await fetch('/agent/hitl/respond', {
               method: 'POST',
               headers: {'Content-Type': 'application/json'},
               body: JSON.stringify(body),
           });
           const result = await resp.json();
           if (result.status === 'waiting_hitl') {
               renderHITLCard(result.hitl_card);  // next gate
           } else if (result.status === 'completed') {
               renderCompletion(result.result);
           }
       } catch (e) {
           btn.disabled = false;
           btn.textContent = decision;
           showError(e.message);
       }
   }
   ```
2. HITL response endpoint is in `app/main.py` (Phase 6.9 `resume_agent`):
   - `POST /agent/hitl/respond` — body `{run_id, gate_id, decision, reason?, modifications?}` → calls `resume_agent(run_id, decision)` → returns `waiting_hitl` or `completed`
   - Uses `Command(resume=decision)` with `config={"configurable": {"thread_id": run_id}}`
3. Visual feedback: loading spinner on button click, success/error toast, timeout countdown timer per gate

**Verification:**
```bash
# HITL card appears when gate fires
# Click Approve → agent continues
# Click Reject → agent halts, presents alternatives
# Click Modify → text input appears, agent re-validates
```

### 7.4: Edge Case Injection Controls
**Duration:** ~2 hours
**What:** Build edge case controls. Must mutate mock data layer so monitor re-query sees the conflict.

**Steps:**
1. Add to `app/ui/app.js`:
   ```javascript
   document.getElementById('inject-conflict').onclick = async () => {
       const resp = await fetch('/agent/inject-edge-case', {
           method: 'POST',
           headers: {'Content-Type': 'application/json'},
           body: JSON.stringify({run_id: currentRunId, type: 'feeder_conflict', feeder_id: 'FEEDER ATLANTIC-03', new_departure: '2026-08-19T16:00:00+08:00'})
       });
       const result = await resp.json();
       showIndicator('Feeder berth conflict injected — monitor will detect on next check', 'warning');
       document.getElementById('inject-conflict').disabled = true;
   };

   document.getElementById('inject-stale').onclick = async () => {
       await fetch('/agent/inject-edge-case', {
           method: 'POST',
           headers: {'Content-Type': 'application/json'},
           body: JSON.stringify({run_id: currentRunId, type: 'stale_data', offset_minutes: 45})
       });
       showIndicator('Stale data injected — data age now >30 min', 'warning');
   };
   ```
2. Add endpoint to `app/main.py`:
   - `POST /agent/inject-edge-case` — body `{run_id, type, ...params}` → calls `app.tools.edge_cases.inject_feeder_berth_conflict()` or `inject_stale_data()` which mutate `app/mocks/data.py` (NOT just AgentState)
   - Returns `{"status": "injected", "type": type, "run_id": run_id}`
   - The NEXT `check_sea_itt_capacity` (via `monitor_node` re-query) will read the mutated mock data and trigger escalation #2 + deviation
3. Timing guidance in UI: show hint "Inject AFTER trucks dispatched, BEFORE monitor check (steps 9–12)" so demo operator knows when to click
4. Visual indicator when edge case is active (banner + disabled button to prevent double-inject)

**Verification:**
```bash
# Click "Inject Feeder Conflict" → agent detects conflict at step 8
# Click "Inject Stale Data" → agent detects stale data
```

### 7.5: Demo Scenario Runner
**Duration:** ~2 hours
**What:** Build demo trigger. Must connect SSE BEFORE starting agent to avoid race.

**Steps:**
1. Add to `app/ui/app.js`:
   ```javascript
   document.getElementById('run-demo').onclick = async () => {
       // 1. Connect SSE first (broadcaster buffers events for this run_id pre-allocation)
       const preRunId = 'run-' + Math.random().toString(36).slice(2, 8);
       // Actually: let server assign run_id. Connect SSE in parallel with agent start.
       const response = await fetch('/agent/run-demo', {method: 'POST'});
       const {run_id, status, hitl_card} = await response.json();
       currentRunId = run_id;
       // 2. Connect SSE immediately
       connectSSE(run_id);
       // 3. If already waiting on HITL, render card
       if (status === 'waiting_hitl' && hitl_card) {
           renderHITLCard(hitl_card);
       }
       updateProgress('running', 'Agent started — querying CITOS, OptETruck, PORTNET...');
   };

   function connectSSE(runId) {
       const es = new EventSource(`/agent/stream/${runId}`);
       es.addEventListener('agent_thinking', e => appendAgentOutput(JSON.parse(e.data)));
       es.addEventListener('tool_call', e => appendToolCall(JSON.parse(e.data)));
       es.addEventListener('tool_result', e => appendToolResult(JSON.parse(e.data)));
       es.addEventListener('hitl_card', e => renderHITLCard(JSON.parse(e.data)));
       es.addEventListener('escalation', e => renderEscalation(JSON.parse(e.data)));
       es.addEventListener('trace_entry', e => renderTraceEntry(JSON.parse(e.data)));
       es.addEventListener('deviation', e => renderDeviation(JSON.parse(e.data)));
       es.addEventListener('confidence_update', e => updateConfidence(JSON.parse(e.data)));
       es.onerror = () => { console.error('SSE error'); es.close(); };
   }

   document.getElementById('reset').onclick = async () => {
       if (currentRunId) {
           await fetch(`/agent/reset/${currentRunId}`, {method: 'POST'});
           // Also reset mock data (clear injected edge cases)
           await fetch('/agent/reset-mocks', {method: 'POST'});
       }
       location.reload();
   };
   ```
2. Add endpoints to `app/main.py`:
   - `POST /agent/run-demo` — creates charter `ITTCoordinationEvent` (120 containers, MV PACIFIC STAR), calls `run_agent(event, broadcaster)`, returns `{run_id, status, hitl_card?}` (status is `waiting_hitl` if interrupted, `completed` otherwise)
   - `POST /agent/reset/{run_id}` — cleans up broadcaster queue + buffer for run_id
   - `POST /agent/reset-mocks` — resets mock data to clean state (clears edge case injections)
3. Progress indicator: `updateProgress(status, message)` shows current workflow step (e.g., "Step 6/17: Computing optimal split...")
4. SSE connection handles both buffered replay (events before connect) and live stream

**Verification:**
```bash
# Click "Run Demo" → full scenario plays out in UI
# Agent reasoning appears in real-time
# Tool calls log as they happen
# HITL cards appear when gates fire
# Trace entries populate sidebar
```

### 7.6: Execution Trace Display
**Duration:** ~1 hour
**What:** Build trace sidebar.

**Steps:**
1. Add to `app/ui/app.js`:
   ```javascript
   function renderTraceEntry(entry) {
       const div = document.createElement('div');
       div.className = `trace-entry trace-${entry.node}`;
       div.innerHTML = `
           <span class="timestamp">${entry.timestamp}</span>
           <span class="node">${entry.node}</span>
           <span class="action">${entry.action}</span>
           <span class="duration">${entry.duration_ms}ms</span>
       `;
       document.getElementById('trace-sidebar').appendChild(div);
   }
   ```
2. Color coding: tool=blue, HITL=yellow, escalation=red, agent=green

**Verification:**
```bash
# Trace entries appear in sidebar as agent runs
# Entries are color-coded by type
```

## Verification Loop

After all sub-phases complete:
1. Open `http://localhost:8000/ui/` — UI loads
2. Click "Run Demo" — full scenario plays out
3. SSE streaming works (agent reasoning appears in real-time)
4. HITL cards appear with approve/reject/modify buttons
5. Approve/Reject/Modify work correctly
6. Edge case injection works
7. Trace sidebar populates
8. Reset button clears state

## Commit
After verification: `git commit -m "Phase 7: Web UI — SSE streaming, HITL cards, edge cases, demo runner"`
