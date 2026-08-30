---
phase: code-review
reviewed: 2026-08-30T00:00:00Z
depth: deep
files_reviewed: 9
files_reviewed_list:
  - app/agent/confidence.py
  - app/hitl/handler.py
  - app/hitl/gates.py
  - app/frontend/src/views/dashboards/modern/index.tsx
  - app/frontend/src/views/agent-trace/index.tsx
  - app/frontend/src/components/nexus/HitlCard.tsx
  - app/frontend/src/components/nexus/CostBreakdown.tsx
  - app/agent/mock_provider.py
  - app/mocks/data.py
findings:
  critical: 1
  warning: 5
  info: 3
  total: 9
status: issues_found
---

# Code Review Report

**Reviewed:** 2026-08-30
**Depth:** deep
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Deep review of 9 files across the HITL pipeline, confidence/risk scoring, SSE event flow, and frontend rendering. The codebase is well-structured with good resilience patterns (stale resume guards, TOCTOU checks, fallback providers). However, one critical bug exists in the HITL modify validation failure path where the frontend is never notified that its card was dismissed, causing a stuck UI state. Several medium-severity issues relate to SSE timing races, duplicate event publishing, and inconsistent state cleanup.

---

## Critical Issues

### CR-01: HITL modify validation failure does not publish `hitl_resolved` SSE — frontend shows stale card

**File:** `app/hitl/handler.py:186-208`
**Issue:** When a HITL modify decision fails validation (line 199: `if not validation.get("valid")`), the handler clears `hitl_pending` and sets `status = "running"` (lines 206-207), but does NOT call `_publish_resolved("modify")`. The frontend only learns about gate dismissal via the `hitl_resolved` SSE event (see `modern/index.tsx:232-234`). Without this event, the frontend's `hitlGate` state remains set, showing a stale HITL card while the backend has already moved on.

This is a data-loss-class bug: the operator sees a card that can no longer be acted on (the gate is gone server-side), and approving/rejecting it will either error or be silently ignored.

**Fix:**
```python
# In handler.py, the modify validation failure paths (lines 186-208)
# must call _publish_resolved before returning.

# After line 189 (first validation failure path):
state["hitl_pending"] = None
state["status"] = "running"
_publish_resolved("modify_validation_failed")  # ADD THIS
return state

# After line 207 (second validation failure path):
state["hitl_pending"] = None
state["status"] = "running"
_publish_resolved("modify_validation_failed")  # ADD THIS
return state
```

---

## Warnings

### WR-01: `_publish_resolved` races with graph resume — state may be inconsistent when frontend processes event

**File:** `app/hitl/handler.py:89-104`
**Issue:** `_publish_resolved` uses `loop.create_task()` to schedule the SSE publish asynchronously (line 96). This means the SSE event is published *after* the handler returns and the graph resumes. However, the frontend processes the event and clears its HITL card *before* the graph's next node (agent) has started executing. The brief window (~1ms) is usually harmless, but under load or with slow SSE delivery, the frontend could receive `hitl_resolved` before the agent node begins its next reasoning cycle — creating a flash of "no HITL gate" before the next gate appears.

More importantly, if the graph resumes and the agent immediately sets a *new* `hitl_pending` (e.g., escalation), the frontend could miss the new gate because it's still processing the `hitl_resolved` event.

**Fix:** Consider publishing `hitl_resolved` *synchronously* via `asyncio.ensure_future` with a small yield, or add the event to a queue that the graph's next node drains. Alternatively, have the frontend debounce `hitlGate` clearance by ~200ms to avoid flickering.

### WR-02: `hitl_node` publishes both `hitl_card` SSE and `log_trace` (which publishes `trace_entry` SSE) — duplicate HITL messages

**File:** `app/hitl/gates.py:168,179`
**Issue:** `hitl_node` publishes:
1. `hitl_card` SSE event (line 168) — the primary approval card
2. `log_trace(state, "hitl", "show_card", ...)` (line 179) — which itself publishes a `trace_entry` SSE event via `trace.py:75`

The modern dashboard filters the duplicate at `modern/index.tsx:202` (`if (data.node === 'hitl' && data.action === 'show_card') break;`), but this filter is fragile — it requires exact string matching on `node` and `action`. If either value is changed (e.g., `"show_card"` → `"showApprovalCard"`), the duplicate reappears.

The agent-trace view (`agent-trace/index.tsx:67`) does NOT filter these, so it shows duplicate entries for every HITL gate.

**Fix:** Remove the `log_trace` call from `hitl_node` (line 179) since the `hitl_card` SSE event already provides complete information. The trace entry for the HITL card display is redundant — the handler's `log_trace` calls for approve/reject/modify/timeout already record the trace. Alternatively, use a distinct action name like `"card_published"` instead of `"show_card"` to avoid the semantic overlap.

### WR-03: `compute_itt_split_default()` road_breakdown string uses `//` (floor) but `road_trips` uses ceiling division

**File:** `app/mocks/data.py:417,429`
**Issue:** `road_trips` is computed with ceiling division: `(road_containers_20ft + 1) // 2` (line 417). But the display string uses floor division: `road_containers_20ft // 2` (line 429). For odd numbers of 20ft containers, the string shows fewer trips than the actual computation uses.

Example: 21 twenty-foot containers → actual trips = 11, displayed = "10 trips". This causes the cost breakdown display to show incorrect trip counts.

**Fix:**
```python
# Line 429 — use the same ceiling division
f"{road_containers_40ft}x 40ft ({road_containers_40ft} trips) + {road_containers_20ft}x 20ft ({(road_containers_20ft + 1) // 2} trips)"
```

### WR-04: HitlCard modify sends two HTTP requests — potential duplicate modify action

**File:** `app/frontend/src/components/nexus/HitlCard.tsx:43-47`
**Issue:** When submitting a modify decision, the component first calls `hitlRespond(runId, decision, gate!.gate_id, reason)` (line 44), then if `decision === 'modify' && mods`, makes a *second* `fetch('/agent/hitl/respond', ...)` with the modifications (line 46). The first call likely sends the modify without the `modifications` payload, and the second call sends the full payload.

This means:
1. The first call may trigger a modify with no modifications (which could pass validation or fail depending on the validation logic)
2. The second call sends the same modify again
3. The state could be mutated twice, or the second call could be rejected as stale

**Fix:** Remove the first `hitlRespond` call for the modify case and only use the second `fetch` with the full payload. Or better, add the `modifications` to the first `hitlRespond` call and remove the second fetch entirely:
```typescript
async function handleDecision(decision: string) {
    setLoading(true);
    try {
      const mods = decision === 'modify' && modRoad ? { road_containers: parseInt(modRoad, 10) } : undefined;
      const res = await hitlRespond(runId, decision, gate!.gate_id, reason || undefined, mods);
      // ... rest of handler
    }
}
```

### WR-05: `agent-trace/index.tsx` does not clean up SSE when run completes — stale EventSource

**File:** `app/frontend/src/views/agent-trace/index.tsx:58-64,66-79`
**Issue:** The component resolves `runId` from `getActiveRun()` (line 52), then fetches trace data (line 60) and connects SSE (line 66). When the run completes, `getActiveRun()` returns `{ run_id: null, status: 'completed' }`, but the component's `resolvedRunId` state is never cleared — it retains the old run ID. The SSE connection stays open to a completed run, receiving heartbeats but no meaningful data.

The SSE connection should be torn down when the run completes, and the component should show a "Run completed" state instead of "Waiting for trace events...".

**Fix:** Add a `run_complete` event handler to the SSE callback that clears `resolvedRunId`:
```typescript
useSSE(runId, (event: SSEEvent) => {
    if (event.event === 'trace_entry') {
        // existing trace handling...
    }
    if (event.event === 'run_complete') {
        setResolvedRunId(null); // or set to a "completed" sentinel
    }
});
```

---

## Info

### IN-01: Risk thresholds (0.3, 0.6) are consistent across all files — no issue

**Files:** `modern/index.tsx:434-435`, `HitlCard.tsx:225`, `CostBreakdown.tsx:44`
**Issue:** The risk badge thresholds (`risk > 0.6` = High, `risk > 0.3` = Medium, else Low) are consistent across the dashboard header, HitlCard risk display, and CostBreakdown gate detection. This is correct and well-maintained.

**Suggestion:** Extract these thresholds into a shared constant (e.g., `RISK_THRESHOLDS = { high: 0.6, medium: 0.3 }`) to prevent drift if they need to change.

### IN-02: `compute_risk_score()` simplification is safe — no downstream breakage

**File:** `app/agent/confidence.py:135-140`
**Issue:** The function now returns `1 - confidence`. I verified all 21 callers across `nodes.py`, `trace.py`, `gates.py`, and `handler.py`. All callers use the result as a read-only metric (trace entries, card data, logging). No caller depends on escalation/deviation boosts in the risk score itself — those boosts are captured in the *confidence* score via `deterministic_score()` (lines 84-90), which penalizes for `deviation_log` and `escalation`. The risk score is `1 - confidence`, so it naturally incorporates those penalties indirectly.

**No fix needed.**

### IN-03: `mock_provider.py` correctly reads confidence from state and dispatch trucks from road_cap

**File:** `app/agent/mock_provider.py:120,212`
**Issue:** Line 212: `self.state.get("confidence", 0.85)` — reads from state with 0.85 default. Line 120: `road_cap.get("available_trucks", 20)` — reads from road_capacity context with 20 default. Both are correct. The confidence default of 0.85 matches the nominal scenario's expected confidence level, and the truck default of 20 matches the scenario where available trucks are constrained.

**No fix needed.**

---

## Cross-File Analysis

### Import Graph (Reviewed Files)

```
confidence.py ← nodes.py, trace.py, gates.py
handler.py ← gates.py, timeout_scheduler.py
gates.py ← nodes.py (via HITL_GATES)
trace.py ← nodes.py, handler.py, gates.py, monitor.py
sse.py ← handler.py, gates.py, trace.py, nodes.py
mock_provider.py ← (standalone, uses mocks/data.py)
```

### Error Propagation Verified

- `handler.py` wraps all external calls in try/except with structured logging — errors don't crash the graph.
- `gates.py` wraps `log_trace` and SSE publish in try/except — resilient to import failures.
- `trace.py` wraps SSE publish in try/except — trace entries are always appended to state even if SSE fails.
- `timeout_scheduler.py` wraps handler calls and SSE publish — timeout failures halt the workflow gracefully.

### State Mutation Consistency

- `hitl_pending` is cleared in all handler paths except: (1) escalate paths where it's set to HITL-5, (2) error handler in gates.py:259. All paths are consistent.
- `status` transitions are consistent: `"waiting_hitl"` → `"running"` (approve/modify), `"escalated"` (escalate), `"halted"` (halt), `"cancelled"` (cancel), `"holding"` (hold).

---

_Reviewed: 2026-08-30_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
