---
status: testing
phase: 06-agent-core
source: [.planning/phases/06-agent-core/PLAN.md, .planning/phases/06-agent-core/06-REVIEW.md]
started: 2026-08-28T11:30:00+08:00
updated: 2026-08-28T11:30:00+08:00
---

## Current Test

number: 7
name: HITL Stale Resume Rejected (422) and Gate Alias Normalization
expected: |
  (a) Start run, approve HITL-1 normally -> not stale. (b) Simulate halted: POST /agent/hitl/respond for a run manually set to halted (or inject timeout) then late approve with gate_id "HITL-1" or alias "hitl_1" -> returns 422 detail "already timed out". (c) After HITL-1 approved and now waiting HITL-2, resending old HITL-1 gate_id does NOT block HITL-2 approve (different gate not stale). Verifies is_hitl_stale normalization lower+replace -/_.
awaiting: user response

## Tests

### 1. Cold Start Smoke Test
expected: |
  Kill any running server. Clear temp state (if any). Start the application from scratch: `uvicorn app.main:app --port 8000`. Server boots without errors, `GET /health` returns {"status":"ok"}, and `GET /docs` loads.
result: pass
reported: "both load, but i had to edit the url to get to the health and docs paths. they all load though"
note: navigation via /ui/ placeholder requires manual edit to /health and /docs — not a failure, endpoints work

### 2. Webhook Valid Triggers Agent (HITL-1)
expected: |
  POST /webhook/itt-coordination with valid PB-12 event (120 containers, vessel MV PACIFIC STAR, tuas_vessel_departure = now+12h, 4 blocks). Returns 200 with {run_id, status:"waiting_hitl", hitl_card:{gate_id:"HITL-1", gate_name:"Approve ITT Split", cost_breakdown:{optimal_split:{road_containers:80, sea_containers:40, total_transport_cost:10400}}, confidence ~0.92, risk_score, timeout_seconds:1800}}. GET /webhook/runs/{run_id} shows same state. No 500.
result: pass
reported: "yes it works"

### 3. HITL Approve Flow Through to Dispatch and Tuas
expected: |
  Using run_id from Test 2: POST /agent/hitl/respond {run_id, decision:"approve", gate_id:"HITL-1"} -> returns waiting_hitl for HITL-2. Approve HITL-2 -> waiting HITL-3. Approve HITL-3 -> agent calls dispatch_road_itt + request_feeder_hold (both succeed, status dispatched). Next auto-calls update_tuas_loading_sequence -> HITL-4 card appears (Approve Loading Sequence Update, timeout 600). Approve HITL-4 -> status leaves waiting_hitl (monitor runs, then either completed or HITL-5 if deviation). Each HITL card shows cost, confidence, risk_score, alternatives.
result: pass
reported: "hitl-4 should be working — user confirmed HITL-1 card correct and full sequence runs to HITL-4"

### 4. Webhook Invalid Returns 422 Not 500
expected: |
  POST /webhook/itt-coordination with (a) container_count=10 (<50), (b) tuas_vessel_departure in the past (now-1h), (c) containers_ready=200 > container_count=120. Each returns 422 (422 for a/b, 422 for c — not 500). 422 body detail mentions container_count / tuas_vessel_departure / containers_ready. Valid event still works after these rejects.
result: pass
reported: "all 422"

### 5. End-to-End Happy Path via HTTP + SSE (10 steps, $10,400)
expected: |
  Fresh run: connect SSE first GET /agent/stream/{run_id} (should replay buffered hitl_card later). Then run full flow via webhook + 4 approves (as Test 3). Verify: trace via GET /agent/trace/{run_id} has >=12 entries, every entry has risk_score (0.0-1.0) and confidence, deviation_log == [], cost_vs_baseline baseline 12000 optimised 10400 savings 1600, roi per_incident 8000, and SSE stream contained 8+ event types: agent_thinking, tool_call, tool_result, hitl_card, trace_entry. Total wall time ~35-45s.
result: pass
reported: "yes — confirmed total_transport_cost 10400 via 10400 search after guidance about cost_per_trip"

### 6. Deviation Injection → Monitor → Re-compute 100/20 → HITL-5
expected: |
  Start fresh run, approve to HITL-4 but BEFORE approving HITL-4: POST /agent/inject-edge-case {case:"feeder_berth_conflict", feeder_id:"FEEDER ATLANTIC-03", run_id}. Then approve HITL-4. Monitor node re-queries T3, detects deviation (berth_status conflict, type feeder_berth_conflict), logs deviation_log[0] with impact "feeder delayed", re-computes split to road 100 / sea 20 total $11,200, drops confidence to 0.78 then after HITL-5 approve to 0.90, fires escalation, presents HITL-5 Emergency Re-Split card (cost impact +$800, delta +4 trucks). Approve HITL-5 -> delta dispatch and second T5 succeed, deviation_log persists, trace contains deviation_detected with risk_score ~0.47.
result: pass
reported: "doesn't go to waiting_hitl hitl-5 — fixed via app/tools/base.py:31 forwarding _run_id to execute for per-run override, retry after fix: yes goes to HITL-5"
note: CR-02 per-run isolation bug, fixed, verified via TestClient run-2780b2ae deviation_log len 1 road 100

### 2. Webhook Valid Triggers Agent (HITL-1)
expected: |
  POST /webhook/itt-coordination with valid PB-12 event (120 containers, vessel MV PACIFIC STAR, tuas_vessel_departure = now+12h, 4 blocks). Returns 200 with {run_id, status:"waiting_hitl", hitl_card:{gate_id:"HITL-1", gate_name:"Approve ITT Split", cost_breakdown:{optimal_split:{road_containers:80, sea_containers:40, total_transport_cost:10400}}, confidence ~0.92, risk_score, timeout_seconds:1800}}. GET /webhook/runs/{run_id} shows same state. No 500.
result: [pending]

### 3. HITL Approve Flow Through to Dispatch and Tuas
expected: |
  Using run_id from Test 2: POST /agent/hitl/respond {run_id, decision:"approve", gate_id:"HITL-1"} -> returns waiting_hitl for HITL-2. Approve HITL-2 -> waiting HITL-3. Approve HITL-3 -> agent calls dispatch_road_itt + request_feeder_hold (both succeed, status dispatched). Next auto-calls update_tuas_loading_sequence -> HITL-4 card appears (Approve Loading Sequence Update, timeout 600). Approve HITL-4 -> status leaves waiting_hitl (monitor runs, then either completed or HITL-5 if deviation). Each HITL card shows cost, confidence, risk_score, alternatives.
result: [pending]

### 4. Webhook Invalid Returns 422 Not 500
expected: |
  POST /webhook/itt-coordination with (a) container_count=10 (<50), (b) tuas_vessel_departure in the past (now-1h), (c) containers_ready=200 > container_count=120. Each returns 422 (422 for a/b, 422 for c — not 500). 422 body detail mentions container_count / tuas_vessel_departure / containers_ready. Valid event still works after these rejects.
result: [pending]

### 5. End-to-End Happy Path via HTTP + SSE (10 steps, $10,400)
expected: |
  Fresh run: connect SSE first GET /agent/stream/{run_id} (should replay buffered hitl_card later). Then run full flow via webhook + 4 approves (as Test 3). Verify: trace via GET /agent/trace/{run_id} has >=12 entries, every entry has risk_score (0.0-1.0) and confidence, deviation_log == [], cost_vs_baseline baseline 12000 optimised 10400 savings 1600, roi per_incident 8000, and SSE stream contained 8+ event types: agent_thinking, tool_call, tool_result, hitl_card, trace_entry. Total wall time ~35-45s.
result: [pending]

### 6. Deviation Injection → Monitor → Re-compute 100/20 → HITL-5
expected: |
  Start fresh run, approve to HITL-4 but BEFORE approving HITL-4: POST /agent/inject-edge-case {case:"feeder_berth_conflict", feeder_id:"FEEDER ATLANTIC-03", run_id}. Then approve HITL-4. Monitor node re-queries T3, detects deviation (berth_status conflict, type feeder_berth_conflict), logs deviation_log[0] with impact "feeder delayed", re-computes split to road 100 / sea 20 total $11,200, drops confidence to 0.78 then after HITL-5 approve to 0.90, fires escalation, presents HITL-5 Emergency Re-Split card (cost impact +$800, delta +4 trucks). Approve HITL-5 -> delta dispatch and second T5 succeed, deviation_log persists, trace contains deviation_detected with risk_score ~0.47.
result: [pending]

### 7. HITL Stale Resume Rejected (422) and Gate Alias Normalization
expected: |
  (a) Start run, approve HITL-1 normally -> not stale. (b) Simulate halted: POST /agent/hitl/respond for a run manually set to halted (or inject timeout) then late approve with gate_id "HITL-1" or alias "hitl_1" -> returns 422 detail "already timed out". (c) After HITL-1 approved and now waiting HITL-2, resending old HITL-1 gate_id does NOT block HITL-2 approve (different gate not stale). Verifies is_hitl_stale normalization lower+replace -/_.
result: [pending]

### 8. HITL MODIFY Re-computes Tool 4 (CR-01 Fix)
expected: |
  Fresh run waiting HITL-1: POST /agent/hitl/respond {run_id, decision:"modify", gate_id:"HITL-1", modifications:{road_containers:100, sea_containers:20}} -> does NOT crash with "asyncio.run inside loop". Instead re-validates, re-runs compute_itt_split with new constraints, updates split_result to the modified 100/20 split, re-presents same HITL-1 card with updated cost_breakdown. Approve after modify completes to HITL-2.
result: [pending]

### 9. Resilience: Rate-Limit Retry, Timeout vs 503, Hallucinated Tool, Partial Batch
expected: |
  (a) Mock 429 provider -> chat_with_rate_limit retries 1s then 2s then falls back (logged llm_rate_limit_fallback) and still completes. (b) Single tool batch with one timeout (e.g., check_road_itt_capacity with timeout) + one success -> partial batch continues, both tool_results present, timeout entry has fallback_used true and distinct error "timeout" vs 503 entry error "service unavailable". (c) Hallucinated tool name (non_existent_tool_xyz) -> trace contains hallucinated_tool event, agent returns retry message with Available tools: [...], no crash. (d) SSE replay: after 2 events, reconnect with Last-Event-ID=1 replays 2..N.
result: [pending]

### 10. Concurrency Isolation + Container Truncation Correctness (CR-02)
expected: |
  Start 3 concurrent runs via asyncio.gather(run_agent with vessel_id MV CONCURRENT-0/1/2): each gets distinct run_id, buffers in broadcaster isolated (get_buffered per run_id), tool_results per run not leaked. Also verify truncation: after get_itt_candidates, GET /agent/trace/{run_id} shows tool_results output containers_truncated_total=120 and containers length 5, but context.candidates total_containers=120 and weight_bounds guardrail still detects bad weight at index 100 (if injected) — optimiser cost still $10,400 from full 120.
result: [pending]

## Summary

total: 10
passed: 5
issues: 0
pending: 5
skipped: 0

## Gaps

[none yet]
