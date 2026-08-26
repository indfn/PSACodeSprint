# Phase 7: Web UI & Integration — PSA Nexus Dashboard

## Goal
Build the PSA Nexus dashboard — a command-center grade, dark-mode OLED operations console with real-time SSE streaming, problem switcher, approval cards, demo scenarios, and notification display — proving the platform generalises while scoring high on visual polish and demo impact.

## Depends on
Phase 6

## Requirements
U-01 through U-12

## Success Criteria
1. Web UI loads in browser with command-center polish (dark OLED, bento hierarchy, staggered reveal — not generic card stack)
2. SSE endpoint streams agent thoughts, tool calls, and HITL cards in real time with replay buffer
3. HITL approval buttons work (approve/reject/modify) with loading / empty / error / tactile states
4. Edge case injection controls work (feeder conflict, stale data) with timing hint + per-run isolation
5. Demo scenario can be triggered from UI with SSE-first race fix + progress indicator
6. Trace sidebar + notification panel live-update with color + icon cues (not color-only)
7. Problem switcher (PB-12 ↔ PB-01) updates tool/gate list live

## Design System — PSA Nexus Command Center

**Source:** `ui-ux-pro-max` (`logistics operations dashboard dark mode` + `port logistics command center`) + `design-taste-frontend` overrides (variance 8 / motion 6 / density 4). Persisted token set for `html-tailwind` (vanilla JS, no framework lock-in).

| Token | Value | Usage |
|-------|-------|-------|
| **Mode** | Dark OLED | Capped to OLED power + eye comfort; no light-mode default |
| **Background** | `#020617` (slate-950) | Page bg — never pure black `#000000` |
| **Surface 1** | `#0F172A` (slate-900) | Card / panel bg |
| **Surface 2** | `#1E293B` (slate-800) | Hover / secondary surface |
| **Border** | `border-white/10` + `shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]` | Liquid-glass refraction edge — not flat `border-gray-200` |
| **Text primary** | `#F8FAFC` (slate-50) | Headlines — `7:1` contrast on `#020617` |
| **Text muted** | `#94A3B8` (slate-400) | Secondary — minimum `#94A3B8`, never below |
| **Accent (single)** | `#22C55E` emerald (sat <80%) | Sole accent: CTA, success, confidence high — no AI purple/blue glow, no second accent |
| **Semantic** | emerald (success) / amber (warning) / red (escalation) + icon + label | Never color-only — icon + text accompanies every status |
| **Typography display** | `Geist` / `Satoshi` `tracking-tighter leading-none` | `text-4xl md:text-5xl` — Inter banned, serif banned for dashboards |
| **Typography mono** | `JetBrains Mono` / `Geist Mono` | All numbers: cost `$10.4K`, confidence `0.85`, timestamps, `duration_ms` — cock-pit precision |
| **Radius** | `rounded-[1.5rem]` cards / `rounded-full` pills | Diffusion shadow `shadow-[0_20px_40px_-15px_rgba(0,0,0,0.4)]` — tinted to bg |
| **Motion** | `spring stiffness:100 damping:20` + `will-change: transform` | Hardware-accelerated `transform`/`opacity` only; respect `prefers-reduced-motion` |
| **Layout** | `max-w-[1400px] mx-auto` / `min-h-[100dvh]` / CSS Grid `grid-cols-12` | Grid over flex-calc; asymmetric `2fr 1fr` bento; single column `w-full px-4` <768px; `top-4 left-4 right-4` floating header; no `h-screen` |

**Effects stack:** liquid-glass refraction (inner border + inset shadow), spotlight border on hover (cursor-tracked radial), skeletal shimmer loaders, staggered `staggerChildren 80ms` waterfall, perpetual breathing dot on `agent_status`, typewriter for `agent_thinking`, float for HITL cards, mesh gradient ambient bg via fixed pseudo-element `pointer-events-none`.

**Anti-patterns enforced:** no emoji icons (Phosphor `@phosphor-icons/web` or SVG primitives, `stroke 1.5` uniform), no scale hover that shifts layout, no center-hero, no 3-equal-cards row, no `h-screen`, no `z-50` spam, no custom cursor, no Inter, no generic names, cursor-pointer on every clickable.

**Accessibility:** `aria-live="polite"` on streaming regions, `role="alert"` on escalation/error, `focus-visible:ring` on all interactive, keyboard nav for cards, 4.5:1 text contrast, icon+color for every status.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser (UI) — Bento 2.0                │
│  max-w-[1400px] mx-auto  │  mesh gradient + glass refraction  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Agent    │  │   Tool   │  │   HITL   │  │  Trace   │  │
│  │  Status   │  │   Log    │  │   Cards  │  │ Sidebar  │  │
│  │+live dot │  │ shimmer  │  │ spotlight│  │ divide-y │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │  aria-live  │  stagger    │  spring     │         │
│       └──────────────┴──────────────┴──────────────┘         │
│                          │ SSE (EventSource)                 │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                    FastAPI Server                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  SSE     │  │  Agent   │  │   HITL   │  │  Edge    │  │
│  │ Endpoint │  │  Run     │  │ Response │  │  Case    │  │
│  │+replay  │  │+stream  │  │+Command │  │+mutate  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Plan

### 7.1: SSE Endpoint (with Replay Buffer + Typed Events)
**Duration:** ~2 hours
**What:** Build the Server-Sent Events endpoint with studio-grade streaming UX. Must handle the race: agent may emit before SSE connects — plus accessibility for screen readers.
**Design upgrade:** `aria-live="polite"` regions for streamed text, heartbeat as keep-alive not spinner, buffered replay so judge never misses early reasoning.

**Steps:**
1. Create `app/agent/sse.py`:
   ```python
   import asyncio, json
   from collections import deque
   from fastapi import Request
   from fastapi.responses import StreamingResponse

   class SSEBroadcaster:
       def __init__(self):
           self.queues: dict[str, asyncio.Queue] = {}
           self.buffers: dict[str, deque] = {}
           self.BUFFER_SIZE = 100
       def _ensure_run(self, run_id: str):
           if run_id not in self.queues:
               self.queues[run_id] = asyncio.Queue()
               self.buffers[run_id] = deque(maxlen=self.BUFFER_SIZE)
       async def publish(self, run_id: str, event: str, data: dict):
           self._ensure_run(run_id)
           msg = {'event': event, 'data': json.dumps(data, default=str)}
           self.buffers[run_id].append(msg)
           await self.queues[run_id].put(msg)
       async def stream(self, run_id: str, request: Request):
           self._ensure_run(run_id)
           buffered = list(self.buffers[run_id])
           queue = self.queues[run_id]
           async def gen():
               for msg in buffered:
                   yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"
               while True:
                   if await request.is_disconnected(): break
                   try:
                       msg = await asyncio.wait_for(queue.get(), timeout=30)
                       yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"
                   except asyncio.TimeoutError:
                       yield f"event: heartbeat\ndata: {{}}\n\n"
           return StreamingResponse(gen(), media_type="text/event-stream")
       def cleanup(self, run_id: str):
           self.queues.pop(run_id, None); self.buffers.pop(run_id, None)
   broadcaster = SSEBroadcaster()
   ```
   > **Race fix:** `publish()` buffers via `_ensure_run()` so replay works even before `stream()` connects.

2. Add `GET /agent/stream/{run_id}` in `app/main.py` — returns `broadcaster.stream(run_id, request)`.
3. Hook 10 typed events from graph via singleton `broadcaster` (not serialised into checkpoint): `agent_thinking` (typewriter payload), `tool_call`, `tool_result`, `hitl_card`, `escalation`, `trace_entry`, `confidence_update`, `deviation`, `notification`, `heartbeat`. All check `broadcaster` exists before publish.
4. Accessibility contract: each SSE payload includes `aria` hint; frontend renders streamed chunks into `aria-live="polite"` container — no 10s spinner before first token (UX fix: streaming token-by-token).

**Verification:**
```bash
curl -N localhost:8000/agent/stream/test-run-id  # heartbeat every 30s
# With real run: events replayed even if SSE connects 2s late
```

### 7.2: HTML/CSS/JS Frontend — Command Console (Bento 2.0 + Liquid Glass)
**Duration:** ~5 hours (was 4h — add polish time)
**What:** Build the vanilla HTML/Tailwind console as a visually striking, non-generic operations dashboard. Functional spec unchanged; visual execution upgraded from flat card stack to asymmetric bento with perpetual motion.

**Design directives (taste 8/6/4):**
- **Structure:** Single `max-w-[1400px] mx-auto px-4 md:px-6` container. Asymmetric grid: `grid grid-cols-12 gap-5` — row 1: status `col-span-12 lg:col-span-8` + confidence `col-span-12 lg:col-span-4` (2:1 offset, not 3 equal cards); row 2: agent reasoning `lg:col-span-7` + tool log `lg:col-span-5` (split screen); row 3: HITL stage full-width spotlight; sidebar trace `lg:col-span-4` glued via `divide-y divide-white/10` (no boxed card when density high).
- **Shell:** Floating header `top-4 left-4 right-4 z-30` with `backdrop-blur-xl bg-slate-950/70 border border-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]` refraction. Body `min-h-[100dvh] bg-[#020617] text-slate-50` with mesh gradient via `before:fixed before:inset-0 before:-z-10 before:opacity-[0.04]` radial blobs (lava-lamp, `pointer-events-none`).
- **Typography:** Load `Geist` + `JetBrains Mono` via `next/font` CDN import. `h1 text-3xl tracking-tighter font-semibold`, `h2 text-sm font-medium tracking-widest uppercase text-slate-400`, body `text-[15px] leading-relaxed text-slate-300 max-w-[65ch]`, numbers `font-mono tabular-nums` for `$10,400`, `0.85`, `90 min`.
- **Cards:** Not generic — `rounded-[1.5rem] bg-[#0F172A] border border-white/10 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.4)]` diffusion. Spotlight: on `mousemove` track cursor → `radial-gradient` border glow via JS (no outer neon glow).
- **Motion (hardware-accelerated):** Parent wrapper `staggerChildren 80ms` waterfall (Framer or CSS `animation-delay: calc(var(--i)*80ms)`), each card `initial: {opacity:0, y:12} animate: {opacity:1, y:0} transition: spring 100/20`, `transform`/`opacity` only, `will-change: transform` sparingly, `prefers-reduced-motion` disables loops.
- **Perpetual micro:** status dot `animate-pulse` breathing, agent thinking shimmer `bg-gradient-to-r from-transparent via-white/10 to-transparent` sweep, empty tool log shows skeleton `h-16 rounded-xl animate-pulse bg-white/5` (not spinner).
- **Interaction:** every clickable `cursor-pointer transition-colors duration-200`, `:hover border-white/15`, `:active scale-[0.98] -translate-y-[1px]`.

**Steps:**
1. Create `app/ui/index.html` — surgical upgrade of skeleton (keep IDs for Phase 6 wiring, upgrade markup):
   ```html
   <!doctype html>
   <html lang="en" class="dark">
   <head>
     <meta charset="utf-8" />
     <meta name="viewport" content="width=device-width, initial-scale=1" />
     <title>PSA Nexus — Multi-Party Coordination Platform</title>
     <link rel="stylesheet" href="/ui/style.css" />
     <link rel="preconnect" href="https://fonts.googleapis.com" />
   </head>
   <body class="min-h-[100dvh] bg-[#020617] text-slate-50 antialiased selection:bg-emerald-500/20">
     <div class="fixed inset-0 -z-10 pointer-events-none opacity-[0.04]" aria-hidden="true"
          style="background: radial-gradient(600px 600px at 20% 10%, #22C55E 0%, transparent 60%), radial-gradient(800px 800px at 90% 30%, #0EA5E9 0%, transparent 60%)"></div>

     <header class="sticky top-4 z-30 max-w-[1400px] mx-auto px-4">
       <div class="flex items-center justify-between gap-4 rounded-[1.5rem] border border-white/10 bg-slate-950/70 backdrop-blur-xl px-5 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
         <div class="flex items-center gap-3">
           <span class="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" aria-hidden="true"></span>
           <h1 class="text-[15px] font-semibold tracking-tighter">PSA Nexus</h1>
           <span class="hidden sm:inline text-xs tracking-widest uppercase text-slate-400">Agentic Multi-Party Coordination Platform</span>
         </div>
         <div class="flex items-center gap-2">
           <label for="problem-select" class="text-xs tracking-widest uppercase text-slate-400">Problem</label>
           <select id="problem-select" class="rounded-full bg-white/5 border border-white/10 px-3 py-1.5 text-sm cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500">
             <option value="pb-12-itt">PB-12 — ITT Coordination (Flagship)</option>
             <option value="pb-01-berth">PB-01 — Berth Delay Cascade</option>
           </select>
           <button id="switch-problem" class="rounded-full bg-emerald-500 px-4 py-1.5 text-sm font-medium text-slate-950 hover:bg-emerald-400 active:scale-[0.98] transition cursor-pointer">Switch</button>
         </div>
       </div>
     </header>

     <div class="max-w-[1400px] mx-auto px-4 md:px-6 py-6 space-y-5">
       <section class="grid grid-cols-12 gap-5" id="stagger-root" style="--stagger: 80ms">
         <div class="col-span-12 lg:col-span-8 rounded-[1.5rem] bg-[#0F172A] border border-white/10 p-5 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.4)]">
           <h2 class="text-xs font-medium tracking-widest uppercase text-slate-400">Agent Status</h2>
           <div id="agent-status" class="mt-2 flex items-center gap-2 text-sm" aria-live="polite">Idle</div>
           <div id="agent-output" class="mt-4 min-h-[88px] text-[15px] leading-relaxed text-slate-300" aria-live="polite"></div>
         </div>
         <div class="col-span-12 lg:col-span-4 rounded-[1.5rem] bg-[#0F172A] border border-white/10 p-5">
           <h2 class="text-xs font-medium tracking-widest uppercase text-slate-400">Confidence</h2>
           <div id="confidence-score" class="mt-2 font-mono text-3xl tabular-nums">—</div>
           <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-white/5"><div id="confidence-bar" class="h-full w-0 bg-emerald-500 transition-all duration-500"></div></div>
         </div>
       </section>

       <section class="grid grid-cols-12 gap-5">
         <div class="col-span-12 lg:col-span-7 rounded-[1.5rem] bg-[#0F172A] border border-white/10 p-5">
           <h2 class="text-xs font-medium tracking-widest uppercase text-slate-400">Tool Calls</h2>
           <div id="tool-log" class="mt-3 space-y-2 divide-y divide-white/5" aria-live="polite"></div>
         </div>
         <aside class="col-span-12 lg:col-span-5 rounded-[1.5rem] bg-[#0F172A] border border-white/10 p-5">
           <h2 class="text-xs font-medium tracking-widest uppercase text-slate-400">Execution Trace</h2>
           <div id="trace-sidebar" class="mt-3 max-h-[420px] overflow-auto space-y-1 pr-1" aria-live="polite"></div>
         </aside>
       </section>

       <section id="hitl-cards" class="rounded-[1.5rem] border border-white/10 bg-[#0F172A] p-5 min-h-[120px]" aria-live="polite">
         <h2 class="text-xs font-medium tracking-widest uppercase text-slate-400">Approval Required</h2>
         <div class="mt-3 text-sm text-slate-400 empty-state">Awaiting agent — approvals appear here</div>
       </section>

       <section class="flex flex-wrap items-center gap-3">
         <button id="run-demo" class="rounded-full bg-emerald-500 px-6 py-2.5 text-sm font-medium text-slate-950 hover:bg-emerald-400 active:scale-[0.98] transition cursor-pointer">Run Demo</button>
         <button id="reset" class="rounded-full border border-white/10 bg-white/5 px-5 py-2.5 text-sm text-slate-200 hover:bg-white/10 cursor-pointer">Reset</button>
         <span class="text-xs tracking-widest uppercase text-slate-500">Edge injection</span>
         <button id="inject-conflict" class="rounded-full border border-amber-500/20 bg-amber-500/10 px-4 py-2 text-sm text-amber-200 hover:bg-amber-500/20 cursor-pointer">Inject Feeder Conflict</button>
         <button id="inject-stale" class="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300 hover:bg-white/10 cursor-pointer">Inject Stale Data</button>
         <span id="edge-hint" class="text-xs text-slate-500">Inject after dispatch, before monitor check (steps 9–12)</span>
       </section>

       <section id="notification-panel" class="rounded-[1.5rem] border border-white/10 bg-[#0F172A] p-5 hidden">
         <h2 class="text-xs font-medium tracking-widest uppercase text-slate-400">Notifications</h2>
         <ul id="notification-list" class="mt-3 space-y-2 text-sm" aria-live="polite"></ul>
       </section>
     </div>
     <script type="module" src="/ui/app.js"></script>
   </body>
   </html>
   ```
2. Create `app/ui/style.css` — Tailwind v3/v4 via CDN build (check `package.json` first; if no Tailwind, use standalone `@import "tailwindcss"` + utilities). Include: `@import` Geist + JetBrains Mono, CSS vars for tokens, `stagger` keyframes (`@keyframes in {from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}` + `animation-delay: calc(var(--i)*80ms)`), shimmer gradient, focus rings, `prefers-reduced-motion` guard (`@media (prefers-reduced-motion: reduce){ *{animation:none!important;transition:none!important}}`).
3. Create `app/ui/app.js` — SSE client + DOM with staggered orchestration (all motion `transform`/`opacity` only, spring `100/20` if Framer avoided inline. Handle skeletal loaders: on `run-demo` click show 3 shimmer skeletons in `#tool-log` until first `tool_call` arrives; empty HITL shows composed empty state with CTA icon (Phosphor `ph-check-circle`), not blank div.
4. Mount in `app/main.py`: `app.mount("/ui", StaticFiles(directory="app/ui", html=True), name="ui")` + `app.get("/", redirect="/ui/")`.

**Verification:**
```bash
open http://localhost:8000/ui/  # dark OLED, bento asymmetry, staggered reveal, no layout shift, 375/768/1024/1440 all clean
# Lighthouse: no 4.5:1 failures, focus rings visible via Tab, prefers-reduced-motion respected
```

### 7.3: HITL Approval Cards — Spotlight + Tactile States
**Duration:** ~3 hours
**What:** Build approval cards as the demo's climax moment. Must use `run_id` + `Command(resume=)` while looking premium — spotlight border, tactile push, and full state coverage (loading/empty/error).

**Design upgrade:** Cards sit outside the grid in a full-width stage (variance 8), spotlight follows cursor, not flat yellow/blue card; status expressed via icon+text+color, never color alone.

**Steps:**
1. In `app/ui/app.js`:
   ```javascript
   let currentRunId = null;
   function renderHITLCard(card){
     const labels={ "HITL-1":"Approve ITT Split","HITL-2":"Approve Truck Dispatch","HITL-3":"Approve Feeder Hold","HITL-4":"Approve Loading Sequence","HITL-5":"Escalate to Duty Manager" };
     const isEsc = card.gate_id==="HITL-5";
     const wrap=document.createElement('div');
     wrap.className="group relative overflow-hidden rounded-[1.5rem] border border-white/10 bg-white/[0.02] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] transition hover:border-white/15";
     // spotlight radial via --mx/--my CSS vars on mousemove (no reflow)
     wrap.addEventListener('mousemove', e=>{
       const r=wrap.getBoundingClientRect();
       wrap.style.setProperty('--mx', `${e.clientX - r.left}px`);
       wrap.style.setProperty('--my', `${e.clientY - r.top}px`);
     });
     wrap.innerHTML=`
       <div class="pointer-events-none absolute -inset-px opacity-0 group-hover:opacity-100 transition duration-300" style="background: radial-gradient(400px 200px at var(--mx) var(--my), rgba(34,197,94,0.12), transparent 60%)"></div>
       <div class="flex items-start justify-between gap-4">
         <h3 class="text-sm font-semibold tracking-tight">${labels[card.gate_id]||card.gate_name} ${isEsc?'<span class="ml-2 inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-xs text-red-300 border border-red-500/20"><i data-ph="warning"></i> Escalation</span>':''}</h3>
         <span class="font-mono text-xs tabular-nums text-slate-400">${card.gate_id}</span>
       </div>
       <div class="mt-3 grid grid-cols-12 gap-4 text-sm">
         <div class="col-span-12 md:col-span-8 space-y-2">
           <div class="font-mono tabular-nums">${renderCostSummary(card.approval_card)}</div>
           <div class="flex items-center gap-2 text-xs ${card.confidence<0.85?'text-amber-300':'text-slate-400'}">
             <i data-ph="${card.confidence<0.85?'warning-circle':'check-circle'}" class="h-4 w-4"></i>
             Confidence ${(card.confidence*100).toFixed(0)}% ${card.confidence<0.85?'(below threshold — triggers escalation)':''}
           </div>
           <div class="font-mono text-xs text-slate-500">Timeout ${Math.round(card.approval_card.timeout_seconds/60)} min → ${card.approval_card.timeout_action} • <span class="countdown" data-timeout="${card.approval_card.timeout_seconds}"></span></div>
         </div>
         <div class="col-span-12 md:col-span-4 flex flex-col gap-2">
           <button class="approve inline-flex items-center justify-center gap-2 rounded-full bg-emerald-500 px-4 py-2 text-sm font-medium text-slate-950 hover:bg-emerald-400 active:scale-[0.98] -translate-y-px transition cursor-pointer">Approve</button>
           <button class="reject rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm hover:bg-white/10 cursor-pointer">Reject</button>
           <button class="modify rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm hover:bg-white/10 cursor-pointer">Modify</button>
         </div>
       </div>
       <div id="modify-${card.gate_id}" class="hidden mt-4 rounded-xl border border-white/10 bg-black/20 p-3">
         <label class="text-xs tracking-widest uppercase text-slate-400">Adjust split (road / sea)</label>
         <div class="mt-2 grid grid-cols-2 gap-2">
           <input id="modify-road-${card.gate_id}" type="number" placeholder="Road" class="rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-emerald-500 outline-none" />
           <input id="modify-sea-${card.gate_id}" type="number" placeholder="Sea" class="rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-emerald-500 outline-none" />
         </div>
         <button onclick="respondHITL('${card.gate_id}','modify',null,getModifications('${card.gate_id}'))" class="mt-2 rounded-full bg-emerald-500 px-4 py-1.5 text-sm font-medium text-slate-950 cursor-pointer">Submit Modification</button>
       </div>`;
     document.getElementById('hitl-cards').appendChild(wrap);
     attachHITLHandlers(wrap, card);
     startCountdown(wrap, card.approval_card.timeout_seconds);
   }
   async function respondHITL(gateId, decision, reason=null, mods=null){
     const btn=event.currentTarget; const orig=btn.textContent;
     btn.disabled=true; btn.innerHTML='<span class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></span> Sending…';
     try{
       const r=await fetch('/agent/hitl/respond',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({run_id:currentRunId, gate_id:gateId, decision, reason, modifications:mods})});
       const j=await r.json();
       if(j.status==='waiting_hitl') renderHITLCard(j.hitl_card);
       else if(j.status==='completed') renderCompletion(j.result);
       else if(j.status==='stale') showError(j.error, 'alert');
       wrapCountDownCleanup(gateId);
     }catch(e){ btn.disabled=false; btn.textContent=orig; showError(e.message,'alert'); }
   }
   ```
   - Load Phosphor icons: `<script src="https://unpkg.com/@phosphor-icons/web"></script>` — uniform `1.5` stroke, never emoji.
2. HITL endpoint wiring unchanged (`POST /agent/hitl/respond` → `resume_agent` → `Command(resume=)` with `thread_id: run_id`).
3. State coverage: **Loading** = shimmer skeleton `animate-pulse` matching card height inside `#hitl-cards` before first card; **Empty** = composed illustration + "Awaiting agent — approvals appear here" + subtle pulse dot; **Error** = `role="alert"` banner with icon+text; **Tactile** = buttons `:active scale-[0.98] -translate-y-[1px]`.

**Verification:**
- HITL card appears with spotlight hover, tactile push, countdown ticks down, tab-focus ring visible, screen reader announces via `aria-live`.
- Approve/Reject/Modify all route correctly; stale after timeout shows `role="alert"`.

### 7.4: Edge Case Injection Controls — Per-Run, Visible, Guarded
**Duration:** ~2 hours
**What:** Build injection as a deliberate operator action, not a hidden dev button — muted-to-active, timing-hinted, and per-run isolated.
**Design:** Inactive = `bg-white/5 border-white/10`; on arm after dispatch = `bg-amber-500/10 border-amber-500/20 text-amber-200` with subtle pulse; disabled after inject.

**Steps:**
1. In `app/ui/app.js`:
   ```javascript
   function armEdgeControls(){ document.getElementById('inject-conflict').classList.add('!bg-amber-500/10','!border-amber-500/20','!text-amber-200','animate-pulse'); document.getElementById('edge-hint').classList.remove('hidden'); }
   // call armEdgeControls() on SSE `tool_result` where tool is dispatch_road_itt
   document.getElementById('inject-conflict').onclick = async ()=>{
     const r=await fetch('/agent/inject-edge-case',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({run_id:currentRunId,type:'feeder_conflict',feeder_id:'FEEDER ATLANTIC-03',new_departure:'2026-08-19T16:00:00+08:00'})});
     showBanner('Feeder berth conflict injected — monitor will detect on next check','warning');
     document.getElementById('inject-conflict').disabled=true;
   };
   ```
2. Backend: `POST /agent/inject-edge-case` mutates `app/mocks/data.py` (not `AgentState`) so `monitor_node` T3 re-query sees `berth_status: conflict` → escalation #2 + deviation.
3. Reset: `POST /agent/reset-mocks` clears isolation between runs (07.1 harness does this per test).

**Verification:** inject → next monitor cycle shows `deviation` SSE + amber banner; second run without inject stays `berth_status: available`.

### 7.5: Demo Scenario Runner — SSE-First + Cinematic Progress
**Duration:** ~2 hours
**What:** Build the demo trigger with race-free SSE and a progress rail that feels like a mission timeline.
**Design:** Progress is a sticky horizontal rail (`divide-y` not card) with step dots that fill via spring; `Run Demo` has magnetic micro pull (JS `useMotionValue`-free: CSS `transform` lerp), perpetual shimmer when idle.

**Steps:**
1. In `app/ui/app.js`:
   ```javascript
   const STEPS=["Ingest","Query PPT","Query Road","Query Sea","Optimize","HITL-1","HITL-2","HITL-3","Dispatch","Tuas Update","HITL-4","Monitor","Re-plan","HITL-5","Delta Dispatch","Final Tuas","Complete"];
   function updateProgress(stepIdx, label){
     document.getElementById('agent-status').textContent = `Step ${stepIdx+1}/17: ${label}`;
     document.querySelectorAll('[data-step]').forEach((el,i)=>{
       el.classList.toggle('bg-emerald-500', i<=stepIdx);
       el.classList.toggle('bg-white/10', i>stepIdx);
     });
   }
   document.getElementById('run-demo').onclick = async ()=>{
     document.getElementById('run-demo').disabled=true;
     document.getElementById('run-demo').innerHTML='<span class="animate-pulse">Launching…</span>';
     const res=await fetch('/agent/run-demo',{method:'POST'});
     const {run_id, status, hitl_card}=await res.json();
     currentRunId=run_id; connectSSE(run_id);
     if(status==='waiting_hitl'&&hitl_card) renderHITLCard(hitl_card);
     updateProgress(0,'Agent started — querying CITOS, OptETruck, PORTNET…');
   };
   function connectSSE(runId){
     const es=new EventSource(`/agent/stream/${runId}`);
     es.addEventListener('agent_thinking', e=>{ appendAgentOutput(JSON.parse(e.data), true); }); // typewriter
     es.addEventListener('tool_call', e=> appendToolCall(JSON.parse(e.data)));
     es.addEventListener('tool_result', e=>{ appendToolResult(JSON.parse(e.data)); if(JSON.parse(e.data).tool==='dispatch_road_itt') armEdgeControls(); });
     es.addEventListener('hitl_card', e=> renderHITLCard(JSON.parse(e.data)));
     es.addEventListener('escalation', e=> renderEscalation(JSON.parse(e.data)));
     es.addEventListener('trace_entry', e=> renderTraceEntry(JSON.parse(e.data)));
     es.addEventListener('deviation', e=>{ renderDeviation(JSON.parse(e.data)); pulseDeviation(); });
     es.addEventListener('confidence_update', e=> updateConfidence(JSON.parse(e.data)));
     es.addEventListener('heartbeat', ()=>{});
     es.onerror=()=>{ es.close(); showError('Stream interrupted — reconnecting…','polite'); };
   }
   ```
2. Endpoints: `POST /agent/run-demo` (charter event 120 containers) → `{run_id, status, hitl_card?}`, `POST /agent/reset/{run_id}` + `POST /agent/reset-mocks`.
3. Skeleton while waiting: show 2 shimmer bars in `#agent-output` and 3 tool skeletons until first `tool_call` — no blank screen.

**Verification:** click Run Demo → skeletons → typewriter text streams → tool dots fill rail → HITL cards appear without missing early events (replay buffer).

### 7.6: Execution Trace Display — Dense, Scannable, Not Boxed
**Duration:** ~1 hour
**What:** Build trace as cockpit-density data — not a boxed list. Uses `divide-y` and mono typography.

**Design (density 4 → 7 when trace many):** No card per entry. `divide-y divide-white/5`, `font-mono text-xs tabular-nums`, color dot + label, timestamp `HH:MM:SS.mmm`, layout via `grid grid-cols-[auto_1fr_auto]`.

**Steps:**
1. In `app/ui/app.js`:
   ```javascript
   function renderTraceEntry(entry){
     const dot={agent:'bg-emerald-500', tool:'bg-sky-500', hitl:'bg-amber-400', escalation:'bg-red-500', monitor:'bg-violet-500', deviation:'bg-orange-500', notification:'bg-fuchsia-500'}[entry.node]||'bg-white/20';
     const row=document.createElement('div');
     row.className="grid grid-cols-[auto_1fr_auto] items-center gap-3 py-2 text-xs";
     row.innerHTML=`<span class="h-1.5 w-1.5 rounded-full ${dot} ${entry.node==='agent'?'animate-pulse':''}"></span>
       <span class="font-mono tabular-nums text-slate-300">${entry.node} · ${entry.action}</span>
       <span class="font-mono tabular-nums text-slate-500">${entry.timestamp?.slice(11,19)??''} · ${entry.duration_ms??0}ms · risk ${Number(entry.risk_score??entry.result?.risk_score??0).toFixed(2)}</span>`;
     row.title = JSON.stringify(entry.result??entry, null, 2);
     document.getElementById('trace-sidebar').appendChild(row);
     row.scrollIntoView({behavior:'smooth', block:'nearest'});
   }
   ```
2. Legend bar above sidebar: green=agent, sky=tool, amber=HITL, red=escalation, violet=monitor, fuchsia=notification — text+dot, never color-only.

**Verification:** trace rows render with mono numbers, breathing green dot on agent, smooth auto-scroll, tooltip shows full JSON.

### 7.7: Problem Switcher — Platform Proof, Not a Dropdown
**Duration:** ~2 hours
**What:** Build the switcher as a visible platform mutation — tool/gate list morphs via layout transition, not just a select value change.
**Design:** Switch triggers `layout` spring; exiting tool chips fade out, entering chips stagger in 60ms; banner `Now running: PB-01 Berth Delay` slides down with `AnimatePresence` style.

**Steps:**
1. In `app/ui/app.js`:
   ```javascript
   async function switchProblem(id){
     const btn=document.getElementById('switch-problem'); btn.disabled=true; btn.textContent='Switching…';
     const res=await fetch(`/agent/switch-problem/${id}`,{method:'POST'});
     const j=await res.json();
     renderProblemBanner(j.problem_id, j.systems, j.tools, j.hitl_gates);
     renderToolChips(j.tools); renderGateChips(j.hitl_gates);
     btn.disabled=false; btn.textContent='Switch';
   }
   function renderToolChips(tools){
     const el=document.getElementById('tool-log'); // reuse or new #tool-chips
     el.innerHTML = tools.map((t,i)=>`<span style="--i:${i}" class="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-mono tabular-nums animate-[in_300ms_both]" >${t}</span>`).join(' ');
   }
   ```
2. Visual: banner `rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-200` with spring slide; tool list 5↔8 chips morph.

**Verification:** PB-12 (5 gates, CITOS/OptETruck/PORTNET) ↔ PB-01 (2 gates, VTIS/OptEVoyage) — chips + banner update without reload.

### 7.8: Notification Display — Bell + Live Feed
**Duration:** ~1 hour
**What:** Show `notify_parties` dispatches live — bell with count badge that overshoots (spring 100/20), feed with parties + message + timestamp.
**Design:** Bell `ph-bell` Phosphor, badge `bg-emerald-500 text-slate-950` popping via `scale 0→1.2→1` spring; feed rows `divide-y`, each with party pills `rounded-full bg-white/5 border-white/10`.

**Steps:**
1. In `app/ui/app.js`:
   ```javascript
   let notifCount=0;
   function onNotification(data){
     notifCount++; document.getElementById('notification-panel').classList.remove('hidden');
     const badge=document.getElementById('notif-badge');
     badge.textContent=notifCount; badge.classList.remove('hidden');
     badge.animate([{transform:'scale(0)'},{transform:'scale(1.2)'},{transform:'scale(1)'}],{duration:300, easing:'cubic-bezier(0.16,1,0.3,1)'});
     const li=document.createElement('li');
     li.className="flex items-center justify-between gap-3 py-2";
     li.innerHTML=`<span class="flex flex-wrap gap-1">${data.parties.map(p=>`<span class="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-xs">${p}</span>`).join('')}</span>
       <span class="text-xs text-slate-400 font-mono tabular-nums">${data.timestamp?.slice(11,19)??''}</span>
       <span class="text-sm text-slate-200">${data.message}</span>`;
     document.getElementById('notification-list').prepend(li);
   }
   // wire: es.addEventListener('notification', e=> onNotification(JSON.parse(e.data)));
   ```

**Verification:** `notify_parties` → bell badge pops + feed row appears + SSE `notification` event.

## Verification Loop

After all sub-phases:
1. `http://localhost:8000/ui/` — dark OLED, bento, mesh ambient, no layout shift on mobile Safari (`min-h-[100dvh]`), no horizontal scroll.
2. Run Demo — typewriter streams token-by-token, skeletons → content waterfall 80ms, heartbeat keeps alive, early events replayed.
3. HITL — spotlight card + tactile push + countdown + tab-focus ring + `aria-live` announcement; approve/reject/modify/stale all work.
4. Edge inject — amber pulse arms after dispatch, per-run isolation verified.
5. Trace — mono numbers, color+icon legend, divide-y density, smooth scroll, tooltip JSON.
6. Switch — tool/gate chips stagger, banner spring.
7. Notifications — bell overshoot, feed live.
8. Lighthouse/a11y — 4.5:1 passes, 375/768/1024/1440 clean, `prefers-reduced-motion` disables loops, no emoji icons, no `h-screen`, no pure black.

## Commit
After verification: `git commit -m "Phase 7: Web UI — Nexus dashboard (OLED bento, liquid glass, spotlight HITL, typewriter SSE)"`
