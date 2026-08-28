# Phase 7: Web UI & Integration — PSA Nexus Dashboard

## Goal
Build the PSA Nexus dashboard — a command-center grade, dark-mode OLED operations console with real-time SSE streaming, problem switcher, approval cards, demo scenarios, and notification display — proving the platform generalises while scoring high on visual polish and demo impact.

## Depends on
Phase 6, Phase 6.7 (admin API)

## Requirements
U-01 through U-12

## Success Criteria
1. Web UI loads in browser with command-center polish (dark OLED, bento hierarchy, staggered reveal — not generic card stack)
2. SSE endpoint streams agent thoughts, tool calls, and HITL cards in real time with replay buffer
3. HITL approval buttons work (approve/reject/modify) with loading / empty / error / tactile states
4. Edge case injection controls work (feeder conflict, stale data) with timing hint + per-run isolation
5. Demo scenario can be triggered from UI with buffer-replay race fix + progress indicator
6. Trace sidebar + notification panel live-update with color + icon cues (not color-only)
7. Problem switcher (all 7 problems) updates tool/gate list live
8. Admin page at `/admin` shows provider config, allows editing, API key injection (auth-guarded)

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
| **Typography display** | `Geist` / `Satoshi` `tracking-tighter leading-none` | `text-4xl md:text-5xl` — Inter banned, serif banned for dashboards. Load via Google Fonts CDN `@import url(...)` in CSS (not `next/font`). |
| **Typography mono** | `JetBrains Mono` / `Geist Mono` | All numbers: cost `$10.4K`, confidence `0.85`, timestamps, `duration_ms` — cock-pit precision |
| **Radius** | `rounded-[1.5rem]` cards / `rounded-full` pills | Diffusion shadow `shadow-[0_20px_40px_-15px_rgba(0,0,0,0.4)]` — tinted to bg |
| **Motion** | `spring stiffness:100 damping:20` + `will-change: transform` | Hardware-accelerated `transform`/`opacity` only; respect `prefers-reduced-motion` |
| **Layout** | `max-w-[1400px] mx-auto` / `min-h-[100dvh]` / CSS Grid `grid-cols-12` | Grid over flex-calc; asymmetric `2fr 1fr` bento; single column `w-full px-4` <768px; `top-4 left-4 right-4` floating header; no `h-screen` |

**Effects stack:** liquid-glass refraction (inner border + inset shadow), spotlight border on hover (cursor-tracked radial), skeletal shimmer loaders, staggered `staggerChildren 80ms` waterfall, perpetual breathing dot on `agent_status`, typewriter for `agent_thinking`, float for HITL cards, mesh gradient ambient bg via fixed pseudo-element `pointer-events-none`. `prefers-reduced-motion` CSS: `@media (prefers-reduced-motion: reduce){ *{animation:none!important;transition:none!important}}` disables all loops and transitions.

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
**Duration:** ~0 hours (already built in Phase 6.5)
**What:** SSE endpoint with replay buffer, typed events, Last-Event-ID support. Built in Phase 6.5 — `app/agent/sse.py` + `GET /agent/stream/{run_id}` in `app/main.py`.
**Status:** ✅ DONE — no implementation needed.

**Frontend注意事项 (for Phase 7.2 JS):**
- Heartbeats arrive as SSE comments (`: heartbeat\n\n`), NOT as `event: heartbeat` — use `es.onmessage` as fallback catch-all for keep-alive, or ignore (comments don't trigger `onmessage` either; they're protocol-level). Simplest: do nothing — heartbeats keep the connection alive without triggering JS handlers.
- Events include `id` field (monotonic counter) — `EventSource` auto-sends `Last-Event-ID` on reconnect, replay picks up from there.
- 10 event types: `agent_thinking`, `tool_call`, `tool_result`, `hitl_card`, `escalation`, `trace_entry`, `confidence_update`, `deviation`, `notification`, `heartbeat`(comment).
- SSE endpoint: `GET /agent/stream/{run_id}?lastEventId=N` or `Last-Event-ID` header.

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
     <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
     <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
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
             <!-- Populated dynamically from GET /agent/problems or hardcoded fallback -->
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

       <!-- Tool chips: populated by problem switcher — separate from live tool log -->
       <section id="tool-chips" class="flex flex-wrap gap-2" aria-label="Active tools for current problem"></section>

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
2. Create `app/ui/style.css` — Tailwind v3/v4 via CDN build (check `package.json` first; if no Tailwind, use standalone `@import "tailwindcss"` + utilities). Include: `@import` Geist + JetBrains Mono from Google Fonts (not `next/font`), CSS vars for tokens, `stagger` keyframes (`@keyframes in {from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}` + `animation-delay: calc(var(--i)*80ms)`), shimmer gradient, focus rings, `prefers-reduced-motion` guard:
   ```css
   @media (prefers-reduced-motion: reduce) {
     *, *::before, *::after {
       animation-duration: 0.01ms !important;
       animation-iteration-count: 1 !important;
       transition-duration: 0.01ms !important;
     }
   }
   ```
3. Create `app/ui/app.js` — SSE client + DOM with staggered orchestration (all motion `transform`/`opacity` only, spring `100/20` if Framer avoided inline. Handle skeletal loaders: on `run-demo` click show 3 shimmer skeletons in `#tool-log` until first `tool_call` arrives; empty HITL shows composed empty state with CTA icon (Phosphor `ph-check-circle`), not blank div.
4. **Mount in `app/main.py`:**
   - **FIRST:** Remove the placeholder routes (lines 608–617): delete `@app.get("/ui/")`, `@app.get("/ui/{path:path}")`, and the `ui_placeholder` function.
   - **THEN:** Add `from fastapi.staticfiles import StaticFiles` and mount: `app.mount("/ui", StaticFiles(directory="app/ui", html=True), name="ui")`
   - Add redirect: `@app.get("/")` → `RedirectResponse("/ui/")`
   - **IMPORTANT:** The placeholder MUST be removed — FastAPI matches routes top-down, and the catch-all `/{path:path}` would intercept before StaticFiles.

**Verification:**
```bash
open http://localhost:8000/ui/  # dark OLED, bento asymmetry, staggered reveal, no layout shift, 375/768/1024/1440 all clean
# Lighthouse: no 4.5:1 failures, focus rings visible via Tab, prefers-reduced-motion respected
```

### 7.3: HITL Approval Cards — Spotlight + Tactile States
**Duration:** ~3 hours
**What:** Build approval cards as the demo's climax moment. Must use `run_id` + `Command(resume=)` while looking premium — spotlight border, tactile push, and full state coverage (loading/empty/error).

**Design upgrade:** Cards sit outside the grid in a full-width stage (variance 8), spotlight follows cursor, not flat yellow/blue card; status expressed via icon+text+color, never color alone.

**SSE hitl_card payload shape** (from `app/hitl/gates.py`):
```json
{
  "gate_id": "HITL-1",
  "gate_name": "Approve ITT Split",
  "approval_card": { "gate_id": "...", "cost_breakdown": {...}, "optimal_split": {...}, "alternatives": [...] },
  "confidence": 0.92,
  "risk_score": 0.08,
  "timeout_seconds": 1800,
  "timeout_action": "escalate"
}
```
Note: `confidence`, `timeout_seconds`, `timeout_action` are at **top level** (not inside `approval_card`).

**Steps:**
1. In `app/ui/app.js`:
   ```javascript
   let currentRunId = null;
   const _hitlTimers = {};  // gate_id → interval_id for countdown cleanup

   function renderHITLCard(card) {
     const labels = { "HITL-1":"Approve ITT Split", "HITL-2":"Approve Truck Dispatch", "HITL-3":"Approve Feeder Hold", "HITL-4":"Approve Loading Sequence", "HITL-5":"Escalate to Duty Manager" };
     const isEsc = card.gate_id === "HITL-5";
     const wrap = document.createElement('div');
     wrap.className = "group relative overflow-hidden rounded-[1.5rem] border border-white/10 bg-white/[0.02] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] transition hover:border-white/15";
     wrap.addEventListener('mousemove', e => {
       const r = wrap.getBoundingClientRect();
       wrap.style.setProperty('--mx', `${e.clientX - r.left}px`);
       wrap.style.setProperty('--my', `${e.clientY - r.top}px`);
     });
     // Use top-level timeout_seconds (not card.approval_card.timeout_seconds)
     const timeoutSec = card.timeout_seconds || 1800;
     const timeoutAction = card.timeout_action || 'escalate';
     wrap.innerHTML = `
       <div class="pointer-events-none absolute -inset-px opacity-0 group-hover:opacity-100 transition duration-300" style="background: radial-gradient(400px 200px at var(--mx) var(--my), rgba(34,197,94,0.12), transparent 60%)"></div>
       <div class="flex items-start justify-between gap-4">
         <h3 class="text-sm font-semibold tracking-tight">${labels[card.gate_id] || card.gate_name} ${isEsc ? '<span class="ml-2 inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-xs text-red-300 border border-red-500/20"><i data-ph="warning"></i> Escalation</span>' : ''}</h3>
         <span class="font-mono text-xs tabular-nums text-slate-400">${card.gate_id}</span>
       </div>
       <div class="mt-3 grid grid-cols-12 gap-4 text-sm">
         <div class="col-span-12 md:col-span-8 space-y-2">
           <div class="font-mono tabular-nums">${renderCostSummary(card)}</div>
           <div class="flex items-center gap-2 text-xs ${card.confidence < 0.85 ? 'text-amber-300' : 'text-slate-400'}">
             <i data-ph="${card.confidence < 0.85 ? 'warning-circle' : 'check-circle'}" class="h-4 w-4"></i>
             Confidence ${(card.confidence * 100).toFixed(0)}% ${card.confidence < 0.85 ? '(below threshold — triggers escalation)' : ''}
           </div>
           <div class="font-mono text-xs text-slate-500">Timeout ${Math.round(timeoutSec / 60)} min → ${timeoutAction} • <span class="countdown" data-timeout="${timeoutSec}"></span></div>
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
     startCountdown(wrap, timeoutSec);
   }

   async function respondHITL(gateId, decision, reason = null, mods = null) {
     const btn = event.currentTarget;
     const orig = btn.textContent;
     btn.disabled = true;
     btn.innerHTML = '<span class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></span> Sending…';
     try {
       const r = await fetch('/agent/hitl/respond', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ run_id: currentRunId, gate_id: gateId, decision, reason, modifications: mods })
       });
       const j = await r.json();
       if (r.ok && j.status === 'waiting_hitl') renderHITLCard(j.hitl_card);
       else if (r.ok && j.status === 'completed') renderCompletion(j.result);
       else if (!r.ok && r.status === 422) showError(j.detail || 'HITL already timed out (stale)', 'alert');
       else if (!r.ok) showError(j.detail || 'HITL request failed', 'alert');
       wrapCountDownCleanup(gateId);
     } catch (e) {
       btn.disabled = false;
       btn.textContent = orig;
       showError(e.message, 'alert');
     }
   }

   // --- Helper stubs (implementer fills in) ---
   function renderCostSummary(card) {
     // card.optimal_split = {road: N, sea: N}, card.approval_card.cost_breakdown = {...}
     const split = card.optimal_split || card.approval_card?.optimal_split || {};
     const road = split.road ?? '—';
     const sea = split.sea ?? '—';
     return `<span class="text-slate-300">Road ${road} / Sea ${sea}</span>`;
   }
   function attachHITLHandlers(wrap, card) {
     wrap.querySelector('.approve').onclick = () => respondHITL(card.gate_id, 'approve');
     wrap.querySelector('.reject').onclick = () => respondHITL(card.gate_id, 'reject', prompt('Rejection reason:'));
     wrap.querySelector('.modify').onclick = () => {
       document.getElementById(`modify-${card.gate_id}`).classList.toggle('hidden');
     };
   }
   function startCountdown(wrap, timeoutSec) {
     const el = wrap.querySelector('.countdown');
     if (!el) return;
     let remaining = timeoutSec;
     const iid = setInterval(() => {
       remaining--;
       if (remaining <= 0) { clearInterval(iid); el.textContent = '0:00 (timed out)'; return; }
       const m = Math.floor(remaining / 60);
       const s = remaining % 60;
       el.textContent = `${m}:${String(s).padStart(2, '0')}`;
     }, 1000);
     _hitlTimers[card.gate_id] = iid;
   }
   function wrapCountDownCleanup(gateId) {
     if (_hitlTimers[gateId]) { clearInterval(_hitlTimers[gateId]); delete _hitlTimers[gateId]; }
   }
   function getModifications(gateId) {
     const road = parseInt(document.getElementById(`modify-road-${gateId}`)?.value) || 0;
     const sea = parseInt(document.getElementById(`modify-sea-${gateId}`)?.value) || 0;
     return { road, sea };
   }
   function showError(msg, type) {
     const banner = document.createElement('div');
     banner.className = 'rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-200';
     banner.setAttribute('role', 'alert');
     banner.innerHTML = `<i data-ph="warning" class="mr-2"></i>${msg}`;
     document.getElementById('hitl-cards').prepend(banner);
     setTimeout(() => banner.remove(), 8000);
   }
   function showBanner(msg, type) {
     const cls = type === 'warning' ? 'border-amber-500/20 bg-amber-500/10 text-amber-200' : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-200';
     const banner = document.createElement('div');
     banner.className = `rounded-xl border ${cls} px-4 py-3 text-sm`;
     banner.innerHTML = `<i data-ph="${type === 'warning' ? 'warning' : 'check-circle'}" class="mr-2"></i>${msg}`;
     document.getElementById('hitl-cards').prepend(banner);
     setTimeout(() => banner.remove(), 6000);
   }
   function renderCompletion(result) {
     document.getElementById('agent-status').textContent = 'Completed';
     document.getElementById('agent-output').innerHTML = `<div class="text-emerald-400 font-medium">Agent completed successfully</div><pre class="mt-2 text-xs text-slate-400 overflow-auto">${JSON.stringify(result, null, 2).slice(0, 500)}</pre>`;
   }
   function pulseDeviation() {
     const el = document.getElementById('agent-status');
     el.classList.add('text-amber-400');
     setTimeout(() => el.classList.remove('text-amber-400'), 2000);
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

### 7.5: Demo Scenario Runner — Buffer-Replay + Cinematic Progress
**Duration:** ~2 hours
**What:** Build the demo trigger with race-free event delivery via replay buffer and a progress rail that feels like a mission timeline.
**Design:** Progress is a sticky horizontal rail (`divide-y` not card) with step dots that fill via spring; `Run Demo` has magnetic micro pull (JS `useMotionValue`-free: CSS `transform` lerp), perpetual shimmer when idle.

**Race fix explained:** The `POST /agent/run-demo` endpoint runs the agent synchronously (awaiting to first HITL interrupt or completion). SSE events are published during execution and buffered by `SSEBroadcaster`. After the fetch returns, `connectSSE(runId)` connects and replays all buffered events. No events are lost — the replay buffer handles late-connecting subscribers.

**Steps:**
1. In `app/ui/app.js`:
   ```javascript
   const STEPS = ["Ingest","Query PPT","Query Road","Query Sea","Optimize","HITL-1","HITL-2","HITL-3","Dispatch","Tuas Update","HITL-4","Monitor","Re-plan","HITL-5","Delta Dispatch","Final Tuas","Complete"];

   function updateProgress(stepIdx, label) {
     document.getElementById('agent-status').textContent = `Step ${stepIdx + 1}/17: ${label}`;
     document.querySelectorAll('[data-step]').forEach((el, i) => {
       el.classList.toggle('bg-emerald-500', i <= stepIdx);
       el.classList.toggle('bg-white/10', i > stepIdx);
     });
   }

   document.getElementById('run-demo').onclick = async () => {
     document.getElementById('run-demo').disabled = true;
     document.getElementById('run-demo').innerHTML = '<span class="animate-pulse">Launching…</span>';
     // Show skeletons while waiting for fetch
     showToolSkeletons();
     const res = await fetch('/agent/run-demo', { method: 'POST' });
     const { run_id, status, hitl_card } = await res.json();
     currentRunId = run_id;
     connectSSE(run_id);
     if (status === 'waiting_hitl' && hitl_card) renderHITLCard(hitl_card);
     updateProgress(0, 'Agent started — querying CITOS, OptETruck, PORTNET…');
   };

   function connectSSE(runId) {
     const es = new EventSource(`/agent/stream/${runId}`);
     es.addEventListener('agent_thinking', e => { appendAgentOutput(JSON.parse(e.data), true); });
     es.addEventListener('tool_call', e => appendToolCall(JSON.parse(e.data)));
     es.addEventListener('tool_result', e => {
       appendToolResult(JSON.parse(e.data));
       if (JSON.parse(e.data).tool === 'dispatch_road_itt') armEdgeControls();
     });
     es.addEventListener('hitl_card', e => renderHITLCard(JSON.parse(e.data)));
     es.addEventListener('escalation', e => renderEscalation(JSON.parse(e.data)));
     es.addEventListener('trace_entry', e => renderTraceEntry(JSON.parse(e.data)));
     es.addEventListener('deviation', e => { renderDeviation(JSON.parse(e.data)); pulseDeviation(); });
     es.addEventListener('confidence_update', e => updateConfidence(JSON.parse(e.data)));
     es.addEventListener('notification', e => onNotification(JSON.parse(e.data)));
     // Heartbeats are SSE comments (: heartbeat\n\n) — they keep the connection alive
     // but don't trigger addEventListener. No handler needed.
     // EventSource auto-retries on error — do NOT call es.close().
     es.onerror = () => { showError('Stream interrupted — reconnecting…', 'polite'); };
   }

   function showToolSkeletons() {
     const log = document.getElementById('tool-log');
     log.innerHTML = '';
     for (let i = 0; i < 3; i++) {
       const sk = document.createElement('div');
       sk.className = 'h-16 rounded-xl animate-pulse bg-white/5';
       log.appendChild(sk);
     }
   }
   ```
2. Endpoints: `POST /agent/run-demo` (charter event 120 containers) → `{run_id, status, hitl_card?}`, `POST /agent/reset/{run_id}` + `POST /agent/reset-mocks`.
3. Skeleton while waiting: show 2 shimmer bars in `#agent-output` and 3 tool skeletons until first `tool_call` — no blank screen.

**Verification:** click Run Demo → skeletons → fetch returns → SSE connects → buffered events replay → typewriter text streams → tool calls fill rail → HITL cards appear without missing early events.

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
   // Populate problem dropdown dynamically on page load
   const PROBLEM_LABELS = {
     'pb-12-itt': 'PB-12 — ITT Coordination (Flagship)',
     'pb-01-berth': 'PB-01 — Berth Delay Cascade',
     'pb-02-dtqc': 'PB-02 — DTQC Contamination',
     'pb-04-feeder': 'PB-04 — Feeder Schedule Cascade',
     'pb-09-expressway': 'PB-09 — Expressway Gridlock',
     'pb-10-sea-air': 'PB-10 — Sea-Air Bifurcation',
     'pb-11-customs': 'PB-11 — Customs Clearance Block',
   };

   function populateProblemSelect() {
     const sel = document.getElementById('problem-select');
     sel.innerHTML = '';
     for (const [id, label] of Object.entries(PROBLEM_LABELS)) {
       const opt = document.createElement('option');
       opt.value = id;
       opt.textContent = label;
       sel.appendChild(opt);
     }
   }

   async function loadActiveProblem() {
     try {
       const res = await fetch('/agent/active-problem');
       const data = await res.json();
       const sel = document.getElementById('problem-select');
       if (data.active_problem_id) sel.value = data.active_problem_id;
       renderToolChips(data.tools || []);
       renderGateChips(data.hitl_gates || []);
     } catch (e) { /* ignore — default selection stays */ }
   }

   async function switchProblem(id) {
     const btn = document.getElementById('switch-problem');
     btn.disabled = true; btn.textContent = 'Switching…';
     try {
       const res = await fetch(`/agent/switch-problem/${id}`, { method: 'POST' });
       const j = await res.json();
       renderProblemBanner(j.problem_id, j.systems, j.tools, j.hitl_gates);
       renderToolChips(j.tools);
       renderGateChips(j.hitl_gates);
     } finally {
       btn.disabled = false; btn.textContent = 'Switch';
     }
   }

   function renderToolChips(tools) {
     const el = document.getElementById('tool-chips'); // separate from #tool-log (live tool calls)
     el.innerHTML = tools.map((t, i) =>
       `<span style="--i:${i}" class="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-mono tabular-nums animate-[in_300ms_both]">${t}</span>`
     ).join(' ');
   }

   function renderGateChips(gates) {
     // Render HITL gate labels as chips below tool chips
     const el = document.getElementById('tool-chips');
     const chips = gates.map((g, i) =>
       `<span style="--i:${i + 10}" class="inline-flex items-center gap-1 rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-xs font-mono text-amber-200 animate-[in_300ms_both]">${g}</span>`
     ).join(' ');
     el.innerHTML += chips;
   }

   function renderProblemBanner(problemId, systems, tools, gates) {
     let banner = document.getElementById('problem-banner');
     if (!banner) {
       banner = document.createElement('div');
       banner.id = 'problem-banner';
       banner.className = 'rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-200 px-4 py-2 text-sm text-center animate-[slideDown_300ms_both]';
       document.querySelector('.max-w-\\[1400px\\]').prepend(banner);
     }
     banner.textContent = `Now running: ${PROBLEM_LABELS[problemId] || problemId} — ${(systems || []).length} systems, ${(tools || []).length} tools, ${(gates || []).length} gates`;
   }

   // Wire up
   document.getElementById('switch-problem').onclick = () => switchProblem(document.getElementById('problem-select').value);
   populateProblemSelect();
   loadActiveProblem();
   ```
2. Visual: banner `rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-200` with spring slide; tool list 5↔8 chips morph; gate chips use amber styling.

**Verification:** PB-12 (5 gates, 8 tools, CITOS/OptETruck/PORTNET/Feeder/PORTNET) ↔ PB-01 (2 gates, 5 tools, VTIS/OptEVoyage) — chips + banner + dropdown update without reload.

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

### 7.9: Admin Config Page (`/admin`)
**Duration:** ~2 hours
**What:** Build the admin UI at `/admin` (not linked from main dashboard, accessible via direct URL). Shows provider/model/base_url/api key status/confidence threshold/cost_params. Allows editing with auth guard (admin/admin123). API keys are write-only (never displayed).
**Depends on:** 6.7 (admin API — ✅ done), 7.2 (design system established)
**Backend endpoints (already built):**
- `POST /api/admin/login` → session cookie
- `GET /api/admin/config` → global LLM config + active problem summary
- `POST /api/admin/config` → write provider/model/base_url to llm.yaml + confidence to problem YAML
- `GET /api/admin/config/problem` → per-problem cost_params, constraints, escalation_triggers, confidence
- `POST /api/admin/config/problem` → write per-problem config fields
- `POST /api/admin/api-key` → inject API key into .env + os.environ (never echoes key)
- `GET /api/admin/config/status` → API key status (no auth)

**Steps:**
1. Create `app/ui/admin.html` — standalone admin page (same dark OLED design system):
   ```html
   <!doctype html>
   <html lang="en" class="dark">
   <head>
     <meta charset="utf-8" />
     <meta name="viewport" content="width=device-width, initial-scale=1" />
     <title>PSA Nexus — Admin Config</title>
     <link rel="stylesheet" href="/ui/style.css" />
     <link rel="preconnect" href="https://fonts.googleapis.com" />
     <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
     <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
   </head>
   <body class="min-h-[100dvh] bg-[#020617] text-slate-50 antialiased">
     <!-- Login form (shown when not authenticated) -->
     <div id="login-screen" class="max-w-sm mx-auto mt-20 p-6 rounded-[1.5rem] bg-[#0F172A] border border-white/10">
       <h2 class="text-lg font-semibold tracking-tight mb-4">Admin Login</h2>
       <input id="login-user" type="text" placeholder="Username" class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm mb-3 focus-visible:ring-2 focus-visible:ring-emerald-500 outline-none" />
       <input id="login-pass" type="password" placeholder="Password" class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm mb-4 focus-visible:ring-2 focus-visible:ring-emerald-500 outline-none" />
       <button id="login-btn" class="w-full rounded-full bg-emerald-500 px-4 py-2 text-sm font-medium text-slate-950 hover:bg-emerald-400 cursor-pointer">Login</button>
       <div id="login-error" class="mt-2 text-sm text-red-400 hidden"></div>
     </div>

     <!-- Config panels (shown after login) -->
     <div id="config-screen" class="hidden max-w-[800px] mx-auto mt-10 px-4 space-y-6">
       <h1 class="text-xl font-semibold tracking-tight">PSA Nexus — Admin Config</h1>

       <!-- Global LLM Config -->
       <section class="rounded-[1.5rem] bg-[#0F172A] border border-white/10 p-5 space-y-4">
         <h2 class="text-xs font-medium tracking-widest uppercase text-slate-400">Global LLM Provider</h2>
         <div class="grid grid-cols-2 gap-4">
           <div>
             <label class="text-xs text-slate-400">Provider</label>
             <select id="cfg-provider" class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm mt-1 focus-visible:ring-2 focus-visible:ring-emerald-500 outline-none">
               <option value="anthropic">Anthropic</option><option value="openai">OpenAI</option>
               <option value="gemini">Gemini</option><option value="deepseek">DeepSeek</option>
               <option value="ollama">Ollama (local)</option><option value="vllm">vLLM (local)</option>
               <option value="lmstudio">LM Studio (local)</option><option value="custom">Custom (OpenAI-compat)</option>
             </select>
           </div>
           <div><label class="text-xs text-slate-400">Model</label><input id="cfg-model" class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm mt-1 focus-visible:ring-2 focus-visible:ring-emerald-500 outline-none" /></div>
           <div><label class="text-xs text-slate-400">Base URL</label><input id="cfg-base-url" class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm mt-1 focus-visible:ring-2 focus-visible:ring-emerald-500 outline-none" placeholder="(optional)" /></div>
           <div><label class="text-xs text-slate-400">Confidence Threshold</label><input id="cfg-threshold" type="number" step="0.01" min="0" max="1" class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm mt-1 focus-visible:ring-2 focus-visible:ring-emerald-500 outline-none" /></div>
         </div>
         <div class="flex items-center gap-3">
           <button id="cfg-save" class="rounded-full bg-emerald-500 px-4 py-1.5 text-sm font-medium text-slate-950 hover:bg-emerald-400 cursor-pointer">Save</button>
           <span id="cfg-status" class="text-xs text-slate-400"></span>
         </div>
       </section>

       <!-- API Key Injection -->
       <section class="rounded-[1.5rem] bg-[#0F172A] border border-white/10 p-5 space-y-4">
         <h2 class="text-xs font-medium tracking-widest uppercase text-slate-400">API Key</h2>
         <div id="api-key-status" class="text-xs text-slate-400 font-mono"></div>
         <div class="grid grid-cols-2 gap-4">
           <div>
             <label class="text-xs text-slate-400">Provider</label>
             <select id="key-provider" class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm mt-1 focus-visible:ring-2 focus-visible:ring-emerald-500 outline-none">
               <option value="anthropic">Anthropic</option><option value="openai">OpenAI</option>
               <option value="gemini">Gemini</option><option value="deepseek">DeepSeek</option>
             </select>
           </div>
           <div><label class="text-xs text-slate-400">API Key</label><input id="key-value" type="password" class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-sm mt-1 focus-visible:ring-2 focus-visible:ring-emerald-500 outline-none" placeholder="sk-..." /></div>
         </div>
         <button id="key-inject" class="rounded-full bg-emerald-500 px-4 py-1.5 text-sm font-medium text-slate-950 hover:bg-emerald-400 cursor-pointer">Inject Key</button>
       </section>

       <!-- Per-Problem Config -->
       <section class="rounded-[1.5rem] bg-[#0F172A] border border-white/10 p-5 space-y-4">
         <h2 class="text-xs font-medium tracking-widest uppercase text-slate-400">Per-Problem Config</h2>
         <div id="problem-config-display" class="text-xs text-slate-400 font-mono whitespace-pre-wrap"></div>
       </section>
     </div>
     <script src="/ui/admin.js"></script>
   </body>
   </html>
   ```
2. Create `app/ui/admin.js` — login flow + config CRUD:
   ```javascript
   async function adminLogin() {
     const user = document.getElementById('login-user').value;
     const pass = document.getElementById('login-pass').value;
     try {
       const r = await fetch('/api/admin/login', {
         method: 'POST', headers: {'Content-Type':'application/json'},
         body: JSON.stringify({username: user, password: pass})
       });
       if (r.ok) {
         document.getElementById('login-screen').classList.add('hidden');
         document.getElementById('config-screen').classList.remove('hidden');
         loadConfig();
       } else {
         document.getElementById('login-error').textContent = 'Invalid credentials';
         document.getElementById('login-error').classList.remove('hidden');
       }
     } catch (e) { /* network error */ }
   }
   async function loadConfig() {
     const r = await fetch('/api/admin/config', {credentials: 'same-origin'});
     if (r.status === 401 || r.status === 403) { document.getElementById('login-screen').classList.remove('hidden'); document.getElementById('config-screen').classList.add('hidden'); return; }
     const data = await r.json();
     document.getElementById('cfg-provider').value = data.llm.provider;
     document.getElementById('cfg-model').value = data.llm.model;
     document.getElementById('cfg-base-url').value = data.llm.base_url;
     document.getElementById('cfg-threshold').value = data.active_problem.confidence_threshold;
     // API key status
     const ks = document.getElementById('api-key-status');
     ks.innerHTML = Object.entries(data.api_key_status).map(([k,v]) => `${k}: <span class="${v==='set'?'text-emerald-400':'text-amber-400'}">${v}</span>`).join(' · ');
   }
   async function saveConfig() {
     await fetch('/api/admin/config', {
       method: 'POST', credentials: 'same-origin',
       headers: {'Content-Type':'application/json'},
       body: JSON.stringify({
         llm: { provider: document.getElementById('cfg-provider').value, model: document.getElementById('cfg-model').value, base_url: document.getElementById('cfg-base-url').value },
         confidence_threshold: parseFloat(document.getElementById('cfg-threshold').value)
       })
     });
     document.getElementById('cfg-status').textContent = 'Saved — provider changes take effect on next agent run';
     setTimeout(() => document.getElementById('cfg-status').textContent = '', 5000);
   }
   async function injectKey() {
     await fetch('/api/admin/api-key', {
       method: 'POST', credentials: 'same-origin',
       headers: {'Content-Type':'application/json'},
       body: JSON.stringify({ provider: document.getElementById('key-provider').value, key: document.getElementById('key-value').value })
     });
     document.getElementById('key-value').value = '';
     loadConfig(); // refresh status
   }
   document.getElementById('login-btn').onclick = adminLogin;
   document.getElementById('cfg-save').onclick = saveConfig;
   document.getElementById('key-inject').onclick = injectKey;
   ```
3. Mount in `app/main.py`: Add route `@app.get("/admin")` that serves `admin.html` from `app/ui/`:
   ```python
   from fastapi.responses import FileResponse
   @app.get("/admin", tags=["Admin"])
   async def admin_page():
       return FileResponse("app/ui/admin.html")
   ```
   **Note:** This is a separate route from the `admin_router` prefix (`/api/admin/*`). No conflict.

**Verification:** Open `/admin` → login form → enter admin/admin123 → see provider config → edit provider → save → status confirms "next agent run" → inject API key → status shows ✅.

## Verification Loop

After all sub-phases:
1. `http://localhost:8000/ui/` — dark OLED, bento, mesh ambient, no layout shift on mobile Safari (`min-h-[100dvh]`), no horizontal scroll.
2. Run Demo — typewriter streams token-by-token, skeletons → content waterfall 80ms, heartbeat keeps alive, early events replayed via buffer.
3. HITL — spotlight card + tactile push + countdown + tab-focus ring + `aria-live` announcement; approve/reject/modify/stale (422 caught) all work.
4. Edge inject — amber pulse arms after dispatch, per-run isolation verified.
5. Trace — mono numbers, color+icon legend, divide-y density, smooth scroll, tooltip JSON.
6. Switch — all 7 problems in dropdown, tool/gate chips stagger, banner spring.
7. Notifications — bell overshoot, feed live.
8. `http://localhost:8000/admin` — login → config → save → API key inject.
9. Lighthouse/a11y — 4.5:1 passes, 375/768/1024/1440 clean, `prefers-reduced-motion` disables loops, no emoji icons, no `h-screen`, no pure black.

## Commit
After verification: `git commit -m "Phase 7: Web UI — Nexus dashboard (OLED bento, liquid glass, spotlight HITL, typewriter SSE)"`
