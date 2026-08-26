# Phase 6: Agent Core (LangGraph)

## Goal
Build the LangGraph agent graph with tool-calling loop, 5 HITL gates, 7 escalation triggers, and confidence scoring — the brain of the demo.

## Depends on
Phase 5

## Requirements
A-01 through A-23 (+ resilience: rate limit, stale resume, webhook validation, risk_score in trace)

## Success Criteria
1. LangGraph StateGraph defined with all nodes and edges (including monitor + resilience)
2. Agent reasons via LLM (with rate-limit retry + fallback), selects tools, processes results
3. All 5 HITL gates pause via `interrupt()` and resume via `Command(resume=)` with `thread_id`; stale resume rejected
4. All 7 escalation triggers detect threshold breaches; risk_score in every TraceEntry
5. Confidence + risk_score propagated through state; threshold 0.85
6. Execution trace (with risk_score, fallback_used, hallucinated_tool) + deviation_log + structured logging
7. End-to-end: webhook (422 on invalid) → agent → tools (timeout vs 503 distinct, partial batch) → HITL → monitor → deviation → re-plan → result

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph StateGraph                      │
│                                                              │
│  ┌─────────┐    ┌──────────┐    ┌─────────┐                │
│  │  START   │───▶│  agent   │───▶│  tools  │──┐             │
│  └─────────┘    │  (LLM)   │◀───│ (exec)  │  │             │
│                 └────┬─────┘    └─────────┘  │             │
│                      │                        │             │
│                      ▼                        │             │
│                 ┌──────────┐                  │             │
│                 │  HITL    │─── approve ─────┘             │
│                 │  gate    │─── reject ──▶ agent (retry)   │
│                 │ (interrupt)│─── modify ──▶ agent (retry)  │
│                 └────┬─────┘                                │
│                      │ timeout                              │
│                      ▼                                      │
│                 ┌──────────┐                                │
│                 │escalation│───▶ agent (with context)       │
│                 └──────────┘                                │
│                      │                                      │
│                      ▼                                      │
│                 ┌──────────┐                                │
│                 │  END     │                                │
│                 └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

## Plan

### 6.1: State Schema Design
**Duration:** ~1 hour
**What:** Define the LangGraph state schema. Must include ALL charter bootstrap fields (Section 3 T6) plus execution fields.

**Steps:**
1. Create `app/agent/__init__.py`
2. Create `app/agent/state.py`:
   ```python
   from typing import TypedDict, Optional, Annotated
   import operator

   class AgentState(TypedDict):
       # Conversation
       messages: Annotated[list, operator.add]  # required for LangGraph message passing
       # Tool results
       tool_results: dict  # {tool_call_id: ToolResult}
       pending_tool_calls: list  # tool calls awaiting execution
       # HITL
       hitl_pending: Optional[dict]  # current HITLGate awaiting interrupt
       hitl_history: list  # past HITLDecision entries
       # Confidence & escalation
       confidence: float  # current confidence score (0.0–1.0)
       escalation: Optional[dict]  # active escalation
       # Observability
       trace: list  # list[TraceEntry] — node entry/exit, tool calls, HITL events
       deviation_log: list  # list[dict] — why original plan failed + recovery
       # Config & identity
       problem_config: dict  # loaded YAML ProblemConfig (from app/configs/problem_config.py)
       run_id: str  # unique run identifier — also used as LangGraph thread_id
       status: str  # running | waiting_hitl | escalated | completed | failed | cancelled | holding | halted
       # Charter bootstrap context (Section 3 T6 — 11 fields)
       context: dict  # {event, origin_terminal, destination_terminal, vessel_id, container_count, tuas_vessel_departure, blocks_affected, dg_containers, current_step, candidates, road_capacity, sea_capacity, split_result, split_alternatives, dispatched, monitored, ...}
       # SSE streaming (injected at runtime, not persisted in checkpoint)
       # _broadcaster: SSEBroadcaster  (optional, not in TypedDict — passed via config)
       # _run_id: str
   ```
3. Create `app/agent/state_models.py`:
   - `TraceEntry(node, action, result, timestamp, duration_ms, confidence, run_id)`
   - `HITLDecision(gate_id, decision, reason, modifications, timestamp)`
   - `Escalation(trigger, severity, message, timestamp, action)`

**Verification:**
```bash
python -c "from app.agent.state import AgentState; print(AgentState.__annotations__)"
```

### 6.2: System Prompt & Tool Definitions (Templated — Not Hardcoded to PB-12)
**Duration:** ~2 hours
**What:** Write the system prompt templated from `ProblemConfig` so Nexus works for any C2 problem.

**Steps:**
1. Create `app/agent/prompts.py`:
   ```python
   def build_system_prompt(config: ProblemConfig) -> str:
       return f"""You are PSA Nexus — an agentic coordinator for PSA Singapore.
   Problem: {config.problem.name} ({config.problem.id}) — {config.problem.sector}
   Description: {config.problem.description}
   Available systems: {', '.join(s['name'] for s in config.systems)}
   Available tools: {', '.join(t['name'] for t in config.tools)}
   Cost params: {config.cost_params}
   Rules:
   - When you have a recommendation, generate an approval card (HITL gate).
   - If confidence < {config.confidence.threshold}, request HITL approval (Trigger #1).
   - Escalation rules: {config.escalation_triggers}
   - Output confidence as 0.0–1.0 in structured JSON.
   - Output tool calls as structured JSON.
   """
   def build_agent_messages(state: AgentState) -> list[dict]:
       config = state["problem_config"]
       system = build_system_prompt(config)
       return [{"role": "system", "content": system}] + state["messages"]
   ```
2. Create `app/agent/tool_schemas.py`:
   - LLM-compatible tool definitions (OpenAI function-calling format)
   - Import schemas from `app/tools/registry.py` — dynamically reflects current problem's tools

**Verification:**
```bash
python -c "from app.agent.prompts import SYSTEM_PROMPT; print(SYSTEM_PROMPT[:100])"
python -c "from app.agent.tool_schemas import get_tool_schemas; print(len(get_tool_schemas()))"
```

### 6.3: Agent Node (LLM Reasoning)
**Duration:** ~3 hours
**What:** Build the core agent node.

**Steps:**
1. Create `app/agent/nodes.py`:
   ```python
   async def agent_node(state: AgentState) -> AgentState:
       # 1. Build messages from state
       messages = build_agent_messages(state)
       
        # 2. Call LLM with tool schemas — MUST adapt per provider family
        from app.shared.tool_adapter import adapt_tools_for_provider
        from app.shared.provider import get_provider_name  # or state["_provider"] set from ProblemConfig.llm.provider
        provider_name = state.get("_provider") or state.get("problem_config", {}).get("llm", {}).get("provider", "anthropic")
        raw_schemas = registry.get_schemas()
        tool_schemas = adapt_tools_for_provider(raw_schemas, provider_name)
        # Also publish SSE agent_thinking before the call
        broadcaster = state.get("_broadcaster")
        if broadcaster:
            await broadcaster.publish(state["_run_id"], "agent_thinking", {"messages": messages[-1] if messages else {}})
        response = await provider.chat(messages, tools=tool_schemas)
       
        # 3. Process response — validate tool_calls against registry before accepting
        if response.tool_calls:
            # Validate: filter hallucinated tools (unknown name / invalid args)
            valid_calls, invalid_calls = [], []
            for tc in response.tool_calls:
                if registry.get_tool(tc.get("name","")) is None:
                    invalid_calls.append(tc)
                    # Log fallback: unknown tool → trace + return error ToolResult instead of crashing
                    state['trace'].append({"event": "hallucinated_tool", "tool_name": tc.get("name"), "available": registry.list()})
                else:
                    valid_calls.append(tc)
            if invalid_calls and not valid_calls:
                # All calls hallucinated → ask LLM to retry with correct tool list
                state['messages'].append({"role": "user", "content": f"Unknown tools: {[c['name'] for c in invalid_calls]}. Available tools: {registry.list()}. Retry with a valid tool."})
                state['status'] = 'running'
            elif valid_calls:
                state['pending_tool_calls'] = valid_calls
                state['status'] = 'calling_tools'
        elif response.hitl_card:
            state['hitl_pending'] = response.hitl_card
            state['status'] = 'waiting_hitl'
        else:
            state['status'] = 'completed'

        # 4. Update trace — include risk_score (CodeSprint Phase 4.3 requires it)
        risk_score = compute_risk_score(state)  # from escalation triggers + confidence, 0.0–1.0
        state['trace'].append(TraceEntry(node="agent", action="reason", result={"tool_calls": response.tool_calls, "risk_score": risk_score}, duration_ms=latency_ms, confidence=response.confidence or state['confidence']))

        # 5. Update confidence + check escalation triggers immediately
        state['confidence'] = response.confidence if response.confidence is not None else state['confidence']
        triggered = check_escalations(state)  # Phase 6.6 — if any fire, set escalation + hitl_pending=HITL-5
        if triggered:
            state['escalation'] = triggered[0]
            state['hitl_pending'] = HITL_GATES["HITL-5"]
       
       return state
   ```
2. Wire provider.py for LLM calls
3. Handle streaming (optional for Phase 6, required for Phase 7)

**Verification:**
```bash
pytest app/tests/test_agent_node.py -v
```

### 6.4: Tool Execution Node
**Duration:** ~1 hour
**What:** Build the tool execution node.

**Steps:**
1. Add to `app/agent/nodes.py`:
   ```python
   async def tool_node(state: AgentState) -> AgentState:
       # 1. Read pending tool calls
       tool_calls = state.get('pending_tool_calls', [])
       
        # 2. Execute each tool — with post-approval guard + timeout + fallback + fallback_used flag
        for call in tool_calls:
            tool = registry.get_tool(call['name'])
            # Post-approval guard: dispatch/hold require prior HITL approve
            if tool and tool.post_approval:
                gate_map = {"dispatch_road_itt": "HITL-2", "request_feeder_hold": "HITL-3"}
                gate_id = gate_map.get(call['name'], "")
                if not has_approval(state, gate_id):
                    result = ToolResult(output={"error": f"HITL {gate_id} approval required before {call['name']}"}, confidence=0.0,
                                        metadata={"tool_name": call['name'], "error": "hitl_required", "timestamp": now(), "duration_ms": 0})
                    state['trace'].append({"event": "tool_blocked_hitl", "tool": call['name'], "gate": gate_id})
                    state['tool_results'][call['id']] = result
                    continue
            # Execute with timeout (distinct from 503 — timeout is latency, 503 is server error)
            try:
                result = await asyncio.wait_for(registry.call(call['name'], **call['args'], _run_id=state.get("run_id","")), timeout=tool.timeout_seconds if tool else 30)
            except asyncio.TimeoutError:
                # Try fallback (e.g. cached_road_capacity) before escalating
                fb_name = FALLBACKS.get(call['name'])
                if fb_name and registry.get_tool(fb_name):
                    result = await registry.call(fb_name, **call['args'])
                    result.metadata["fallback_used"] = True
                    result.metadata["original_error"] = "timeout"
                    state['trace'].append({"event": "tool_timeout_fallback", "tool": call['name'], "fallback": fb_name})
                else:
                    result = ToolResult(output={"error": f"Tool {call['name']} timed out"}, confidence=0.0,
                                        metadata={"tool_name": call['name'], "error": "timeout", "fallback_used": False, "timestamp": now(), "duration_ms": 30000})
                    state['escalation'] = {"trigger": "tool_timeout", "tool": call['name']}
            except Exception as exc:
                # 503 / API error → same fallback logic
                fb_name = FALLBACKS.get(call['name'])
                if fb_name and registry.get_tool(fb_name):
                    result = await registry.call(fb_name, **call['args'])
                    result.metadata["fallback_used"] = True
                    result.metadata["original_error"] = str(exc)
                    state['trace'].append({"event": "tool_error_fallback", "tool": call['name'], "error": str(exc), "fallback": fb_name})
                else:
                    result = ToolResult(output={"error": str(exc)}, confidence=0.0,
                                        metadata={"tool_name": call['name'], "error": str(exc), "fallback_used": False, "timestamp": now()})
            # Handle partial batch: if one tool in batch failed but others succeeded, continue (don't abort whole batch)
            state['tool_results'][call['id']] = result
            state['messages'].append({"role": "tool", "tool_call_id": call['id'], "content": json.dumps(result.output)})

        # 3. Update trace — include risk_score + fallback flag
        for cid, res in state['tool_results'].items():
            risk = compute_risk_score(state)
            state['trace'].append(TraceEntry(node="tool", action="call_tool", result={"tool": res.metadata.get("tool_name"), "output": res.output, "risk_score": risk, "fallback_used": res.metadata.get("fallback_used", False)}, duration_ms=res.metadata.get("duration_ms", 0), confidence=res.confidence))
            # SSE publish per tool result
            bc = state.get("_broadcaster")
            if bc:
                await bc.publish(state["_run_id"], "tool_result", {"tool": res.metadata.get("tool_name"), "output": res.output, "risk_score": risk})
       
       # 4. Clear pending calls
       state['pending_tool_calls'] = []
       state['status'] = 'running'
       
       return state
   ```

**Verification:**
```bash
pytest app/tests/test_tool_node.py -v
```

### 6.5: HITL Gate Implementation
**Duration:** ~4 hours
**What:** Implement the 5 HITL gates as LangGraph `interrupt()` inside a single `hitl` node.

> **Charter gates (Section 4):**

> | Gate | Name | Trigger | Timeout | Timeout Action |
> |------|------|---------|---------|----------------|
> | HITL-1 | Approve ITT Split | split computed | 30 min | Escalate to Duty Manager |
> | HITL-2 | Approve Truck Dispatch | truck dispatch ready | 15 min | Cancel Dispatch |
> | HITL-3 | Approve Feeder Hold | feeder hold request ready | 15 min | Escalate to Duty Manager |
> | HITL-4 | Approve Loading Sequence Update | Tuas QC sequence update ready | 10 min | Hold Current Sequence |
> | HITL-5 | Escalate to Duty Manager | escalation fired | 30 min | Halt Workflow (if Duty Manager silent 30 min → halt entirely) |

**Steps:**
1. Create `app/hitl/__init__.py`
2. Create `app/hitl/models.py`:
   ```python
   @dataclass
   class HITLGate:
       gate_id: str          # "HITL-1" .. "HITL-5"
       gate_name: str        # "Approve ITT Split" etc.
       trigger: str          # charter trigger condition
       description: str
       approval_card: dict   # structured card data (cost, confidence, risk, margin)
       timeout_seconds: int  # 1800 / 900 / 900 / 600 / 1800
       timeout_action: str   # "escalate" / "cancel_dispatch" / "hold_sequence" / "halt"
       options: list[str]    # ['approve', 'reject', 'modify']

   @dataclass
   class HITLDecision:
       gate_id: str
       decision: str  # 'approve', 'reject', 'modify'
       reason: Optional[str]
       modifications: Optional[dict]  # for MODIFY: adjusted road/sea ratio
       timestamp: str

   HITL_GATES: dict[str, HITLGate] = {
       "HITL-1": HITLGate(gate_id="HITL-1", gate_name="Approve ITT Split", trigger="split computed", timeout_seconds=1800, timeout_action="escalate", ...),
       "HITL-2": HITLGate(gate_id="HITL-2", gate_name="Approve Truck Dispatch", trigger="truck dispatch ready", timeout_seconds=900, timeout_action="cancel_dispatch", ...),
       "HITL-3": HITLGate(gate_id="HITL-3", gate_name="Approve Feeder Hold", trigger="feeder hold request ready", timeout_seconds=900, timeout_action="escalate", ...),
       "HITL-4": HITLGate(gate_id="HITL-4", gate_name="Approve Loading Sequence Update", trigger="Tuas QC sequence update ready", timeout_seconds=600, timeout_action="hold_sequence", ...),
       "HITL-5": HITLGate(gate_id="HITL-5", gate_name="Escalate to Duty Manager", trigger="escalation fired", timeout_seconds=1800, timeout_action="halt", ...),
   }
   ```
3. Create `app/hitl/gates.py` — single `hitl_node` using correct LangGraph interrupt:
   ```python
   from langgraph.types import interrupt, Command

   # Canonical interrupt payload — frontend reads BOTH top-level and card-level keys
   # Shape: {gate_id, gate_name, approval_card: {cost, confidence, risk_score, margin, timeout_seconds, timeout_action, ...},
   #         confidence, risk_score, timeout_seconds, timeout_action}
   # SSE hitl_card event publishes the SAME shape so dashboard renderHITLCard works whether from SSE or webhook response.

   def build_approval_card(gate: dict, state: AgentState) -> dict:
       risk_score = compute_risk_score(state)  # 0.0–1.0 from triggers + confidence
       return {
           "gate_id": gate["gate_id"],
           "gate_name": gate["gate_name"],
           "cost_breakdown": state.get("context", {}).get("split_result", {}),
           "confidence": state.get("confidence", 0.0),
           "risk_score": risk_score,
           "margin_minutes": state.get("context", {}).get("margin_minutes", 0),
           "timeout_seconds": gate["timeout_seconds"],
           "timeout_action": gate["timeout_action"],
           "alternatives": state.get("context", {}).get("split_alternatives", []),
       }

   def hitl_node(state: AgentState) -> Command:
       gate = state["hitl_pending"]  # HITLGate dict set by agent_node
       card = build_approval_card(gate, state)

       # Publish via SSE broadcaster (singleton from app.agent.sse)
       from app.agent.sse import broadcaster  # single source — not state["_broadcaster"]
       await broadcaster.publish(state["run_id"], "hitl_card", {
           "gate_id": gate["gate_id"],
           "gate_name": gate["gate_name"],
           "approval_card": card,
           "confidence": state.get("confidence", 0.0),
           "risk_score": card["risk_score"],
           "timeout_seconds": gate["timeout_seconds"],
           "timeout_action": gate["timeout_action"],
       })

       # Correct LangGraph HITL pattern — not 5 separate nodes
       decision = interrupt({
           "gate_id": gate["gate_id"],
           "gate_name": gate["gate_name"],
           "approval_card": card,
           "confidence": state.get("confidence", 0.0),
           "risk_score": card["risk_score"],
           "timeout_seconds": gate["timeout_seconds"],
           "timeout_action": gate["timeout_action"],
       })
       # PAUSE — resume: graph.ainvoke(Command(resume={"decision": "approve", ...}), config={"configurable": {"thread_id": run_id}})

       # Guard: if state already terminal (timeout fired → halted/cancelled), reject late resume
       if state.get("status") in ("halted", "cancelled", "holding"):
           # Late resume after timeout — return terminal state, don't re-enter handler
           return state
       return handle_hitl_response(state, gate, decision)
   ```
4. Create `app/hitl/handler.py`:
   ```python
   def handle_hitl_response(state: AgentState, gate: dict, decision: dict) -> AgentState:
       d = decision["decision"]  # "approve" | "reject" | "modify"

       if d == "approve":
           state["hitl_history"].append(HITLDecision(gate_id=gate["gate_id"], decision="approve", ...))
           state["hitl_pending"] = None
           state["status"] = "running"
           # Log to trace + structured log
           return state

       elif d == "reject":
           # Charter: log reason, present alternatives[] from Tool 4, or escalate if no alternatives
           state["hitl_history"].append(HITLDecision(gate_id=gate["gate_id"], decision="reject", reason=decision.get("reason"), ...))
           alternatives = state.get("context", {}).get("split_alternatives", [])
           if alternatives:
               # Add rejection + alternatives to messages so agent re-reasons
               state["messages"].append({"role": "user", "content": f"HITL {gate['gate_id']} REJECTED: {decision.get('reason')}. Alternatives: {json.dumps(alternatives)}. Propose next steps."})
               state["hitl_pending"] = None
               state["status"] = "running"
           else:
               # No alternatives → escalate to Duty Manager (HITL-5)
               state["escalation"] = {"trigger": "hitl_rejection_no_alternatives", "gate_id": gate["gate_id"], "severity": "high"}
               state["hitl_pending"] = HITL_GATES["HITL-5"]
               state["status"] = "escalated"
           return state

       elif d == "modify":
           # Charter: re-validate vs LTA/feeder/timeline constraints, re-run Tool 4, present updated cost, re-request approval
           modifications = decision.get("modifications", {})  # e.g., {"road_containers": 100, "sea_containers": 20}
           # Validate: LTA chassis limits, feeder capacity, timeline margin
           validation = validate_split_modification(modifications, state)
           if not validation["valid"]:
               state["messages"].append({"role": "user", "content": f"MODIFY validation failed: {validation['error']}. Re-propose."})
               return state
           # Re-run Tool 4 with modified params
           new_result = compute_itt_split_with_modifications(modifications, state)
           state["context"]["split_result"] = new_result["optimal_split"]
           state["context"]["split_alternatives"] = new_result["alternatives"]
           # Re-present same gate with updated card
           state["hitl_pending"] = gate  # will re-enter hitl_node
           state["messages"].append({"role": "user", "content": f"Re-computed split per MODIFY: {json.dumps(new_result['optimal_split'])}. Re-approve."})
           return state

       elif d == "timeout":
           # Per-gate timeout_action: escalate / cancel_dispatch / hold_sequence / halt
           action = gate["timeout_action"]
           if action == "escalate":
               state["escalation"] = {"trigger": "hitl_timeout", "gate_id": gate["gate_id"], "timeout_action": "escalate"}
               state["hitl_pending"] = HITL_GATES["HITL-5"]
           elif action == "cancel_dispatch":
               state["status"] = "cancelled"
               state["trace"].append({"event": "hitl_timeout_cancel_dispatch", "gate_id": gate["gate_id"]})
           elif action == "hold_sequence":
               state["status"] = "holding"
               state["trace"].append({"event": "hitl_timeout_hold_sequence", "gate_id": gate["gate_id"]})
           elif action == "halt":
               state["status"] = "halted"
           # Second-level: if Duty Manager also silent 30 min → halt entirely (handled by HITL-5 timeout)
           return state
   ```
5. Gate card rendering: `build_approval_card(gate, state)` generates structured JSON per charter §4 card template (cost breakdown, confidence, risk, margin) for SSE streaming to UI

**Verification:**
```bash
pytest app/tests/test_hitl.py -v
```

### 6.6: Escalation Trigger Implementation
**Duration:** ~3 hours
**What:** Implement the 7 escalation triggers exactly as defined in charter Section 4.

> **Charter triggers (authoritative):**

> | # | Trigger | Threshold | Action |
> |---|---------|-----------|--------|
> | 1 | Low model confidence | `confidence < 0.85` | escalate to human |
> | 2 | Feeder hold exceeds tidal tolerance | `hold_duration > 1.5 hrs` | escalate to Duty Manager |
> | 3 | Financial recovery cost > limit | `action_cost > $10,000` | escalate to Duty Manager |
> | 4 | Data latency exceeds freshness | `data_age > 30 min` | escalate to human |
> | 5 | Road ITT capacity below threshold | `available_trucks < 60% required` | escalate to human |
> | 6 | Feeder operator unresponsive | `feeder_response_time > 15 min` | escalate to human |
> | 7 | Conflict between planners | planner recommendations conflict | escalate to Duty Manager |

**Steps:**
1. Create `app/agent/escalation.py`:
   ```python
   TRIGGERS: dict[str, Callable] = {
       'low_confidence':        lambda state: check_low_confidence(state, threshold=0.85),
       'feeder_hold_exceeded':  lambda state: check_feeder_hold(state, threshold_hours=1.5),
       'cost_exceeded':         lambda state: check_cost_exceeded(state, threshold_dollars=10000),
       'data_stale':            lambda state: check_data_stale(state, threshold_minutes=30),
       'road_capacity_low':     lambda state: check_road_capacity(state, threshold_ratio=0.6),
       'feeder_unresponsive':   lambda state: check_feeder_unresponsive(state, threshold_minutes=15),
       'planner_conflict':      lambda state: check_planner_conflict(state),
   }

   def check_low_confidence(state) -> bool:
       return state.get("confidence", 1.0) < 0.85

   def check_feeder_hold(state, threshold_hours=1.5) -> bool:
       hold = state.get("context", {}).get("feeder_hold_hours", 0)
       return hold > threshold_hours

   def check_cost_exceeded(state, threshold_dollars=10000) -> bool:
       cost = state.get("context", {}).get("action_cost", 0)
       return cost > threshold_dollars

   def check_data_stale(state, threshold_minutes=30) -> bool:
       # Compare tool result timestamps vs now
       for result in state.get("tool_results", {}).values():
           age_min = (now() - result.metadata.get("timestamp", now())).total_seconds() / 60
           if age_min > threshold_minutes:
               return True
       return False

   def check_road_capacity(state, threshold_ratio=0.6) -> bool:
       required = state.get("context", {}).get("required_trucks", 0)
       available = state.get("context", {}).get("available_trucks", 0)
       return required > 0 and (available / required) < threshold_ratio

   def check_feeder_unresponsive(state, threshold_minutes=15) -> bool:
       elapsed = state.get("context", {}).get("feeder_response_elapsed_minutes", 0)
       return elapsed > threshold_minutes

   def check_planner_conflict(state) -> bool:
       # HITL-5 escalation: if hitl_history has conflicting approve/reject on same gate
       return state.get("context", {}).get("planner_conflict", False)

   def check_escalations(state) -> list[Escalation]:
       triggered = []
       for name, check in TRIGGERS.items():
           if check(state):
               action = "escalate_to_human" if name in ("low_confidence", "data_stale", "road_capacity_low", "feeder_unresponsive") else "escalate_to_duty_manager"
               triggered.append(Escalation(trigger=name, action=action, severity="high", message=f"Trigger {name} fired"))
       return triggered
   ```
2. Each trigger reads from `AgentState.context` / `tool_results` / `confidence`, returns bool with correct charter threshold
3. Called inside `agent_node` after each tool batch — if any trigger fires, set `state["escalation"]` and route to `hitl` node with HITL-5
4. When escalation fires: set `hitl_pending = HITL_GATES["HITL-5"]`, status `escalated`, interrupt with escalation card

**Verification:**
```bash
pytest app/tests/test_escalation.py -v
```

### 6.7: Confidence Scoring
**Duration:** ~2 hours
**What:** Implement confidence scoring.

**Steps:**
1. Create `app/agent/confidence.py`:
   ```python
   async def compute_confidence(state, provider) -> float:
       # Primary: LLM self-assessment via structured JSON output
       prompt = f"Rate your confidence in this plan (0.0-1.0) as JSON {{confidence: float}}: {state.get('context', {}).get('split_result', state['context'])}"
       try:
           response = await provider.chat([{'role': 'user', 'content': prompt}])
           llm_confidence = extract_confidence(response.content)  # parse JSON confidence field
       except Exception:
           llm_confidence = None
       det_confidence = deterministic_score(state)
       return llm_confidence if llm_confidence is not None else det_confidence

   def deterministic_score(state) -> float:
       # Score based on: data freshness, tool result quality, constraint satisfaction, margin headroom
       ...

   def compute_risk_score(state) -> float:
       """CodeSprint Phase 4.3 requires risk_score in trace. Derived from confidence + active triggers."""
       # risk_score = 1 - confidence, boosted by escalation count
       base = 1.0 - state.get("confidence", 1.0)
       escalations = len(state.get("escalation", []) if isinstance(state.get("escalation"), list) else ([state["escalation"]] if state.get("escalation") else []))
       return min(1.0, base + escalations * 0.15)
   ```
2. Threshold: 0.85 for auto-approve, below triggers HITL (Trigger #1)
3. `compute_risk_score()` called in `agent_node` + `tool_node` + `hitl_node` and written to `TraceEntry.risk_score`
4. Propagated through state at each step

**Verification:**
```bash
pytest app/tests/test_confidence.py -v
```

### 6.8: Execution Trace + Structured Logging
**Duration:** ~2 hours (+30 min for logging)
**What:** Implement execution trace logging + structured JSON logging (G-23) + input validation guardrails.

**Steps:**
1. Create `app/agent/trace.py`:
   ```python
   @dataclass
   class TraceEntry:
       timestamp: str
       run_id: str
       node: str  # 'agent', 'tool', 'hitl', 'escalation', 'monitor'
       action: str  # 'reason', 'call_tool', 'show_card', 'escalate', 'deviation', 'monitor_check', 'fallback', 'hallucinated_tool', 'rate_limited'
       result: dict  # includes risk_score, fallback_used, confidence
       duration_ms: float
       confidence: float
       risk_score: float  # CodeSprint Phase 4.3 required — computed from confidence + escalation count

   def log_trace(state, node, action, result, duration_ms):
       entry = TraceEntry(
           timestamp=datetime.now(timezone.utc).isoformat(),
           run_id=state.get("run_id", ""),
           node=node,
           action=action,
           result={**result, "risk_score": compute_risk_score(state)} if isinstance(result, dict) else result,
           duration_ms=duration_ms,
           confidence=state.get('confidence', 0.0),
           risk_score=compute_risk_score(state),
       )
       state['trace'].append(entry)
       structured_log("trace", run_id=state["run_id"], node=node, action=action, result=result, risk_score=entry.risk_score)
       # Publish via singleton broadcaster (not state["_broadcaster"] — avoids checkpoint serialization)
       from app.agent.sse import broadcaster
       try:
           asyncio.create_task(broadcaster.publish(state["run_id"], "trace_entry", entry.__dict__))
       except RuntimeError:
           pass  # no event loop in test
       return state

   def export_trace(state) -> dict:
       return {
           'run_id': state['run_id'],
           'entries': [e if isinstance(e, dict) else e.__dict__ for e in state['trace']],
           'deviation_log': state.get('deviation_log', []),
           'summary': {
               'total_steps': len(state['trace']),
               'total_duration_ms': sum(e.get('duration_ms', 0) if isinstance(e, dict) else e.duration_ms for e in state['trace']),
               'tools_called': [e for e in state['trace'] if (e.get('node') if isinstance(e, dict) else e.node) == 'tool'],
               'hitl_events': [e for e in state['trace'] if (e.get('node') if isinstance(e, dict) else e.node) == 'hitl'],
               'escalations': [e for e in state['trace'] if (e.get('node') if isinstance(e, dict) else e.node) == 'escalation'],
               'deviations': state.get('deviation_log', []),
               'confidence_trajectory': [e.get('confidence', 0) if isinstance(e, dict) else e.confidence for e in state['trace']],
           }
       }
   ```
2. Create `app/shared/logging.py` — structured JSON logging (G-23):
   ```python
   import json, logging, sys
   from datetime import datetime, timezone

   def structured_log(event_type: str, run_id: str = "", step: str = "", **payload):
       entry = {
           "timestamp": datetime.now(timezone.utc).isoformat(),
           "run_id": run_id,
           "step": step,
           "event_type": event_type,
           "payload": payload,
       }
       print(json.dumps(entry), flush=True)  # stdout for Railway/Render log drain
       # Also append to file if configured
   ```
3. Create `app/agent/validation.py` — input validation guardrails (charter §4):
   ```python
   GUARDRAILS = [
       ("weight_bounds", lambda c: 0 < c.get("weight_kg", 0) < 60000, "Reject container, log warning"),
       ("block_capacity", lambda ctx: ctx.get("containers_per_block", 0) <= ctx.get("block_max_capacity", 4500), "Trigger overflow routing"),
       ("truck_availability", lambda ctx: ctx.get("available_trucks", 0) >= 1, "Fall back to 100% sea ITT"),
       ("feeder_capacity", lambda ctx: ctx.get("sea_containers", 0) <= ctx.get("feeder_available_teu", 9999), "Reduce sea allocation"),
       ("vessel_margin", lambda ctx: ctx.get("itt_arrival") < ctx.get("vessel_departure") - timedelta(minutes=60), "Reject split — insufficient margin"),
       ("tidal_window", lambda ctx: ctx.get("feeder_departure") < ctx.get("tidal_deadline"), "Enforce hold limit in split"),
   ]
   def validate_all(state) -> list[dict]:
       failures = []
       for name, check, action in GUARDRAILS:
           if not check(state.get("context", {})):
               failures.append({"guard": name, "action": action})
               structured_log("guardrail_failed", run_id=state["run_id"], step=name, action=action)
       return failures
   ```
   Called at: webhook bootstrap + before each T4 computation + before each post-approval tool.
4. Trace stored in state, exportable as JSON; LangSmith integration: if `LANGSMITH_API_KEY` env var present, wrap graph with `langsmith` tracing
5. Deviation log: `state["deviation_log"]` appended in `monitor_node` (6.10), included in `export_trace` + SSE `deviation` events

**Verification:**
```bash
pytest app/tests/test_trace.py -v
```

### 6.9: Graph Assembly
**Duration:** ~3 hours
**What:** Assemble the full LangGraph StateGraph with correct `interrupt()` + `Command` + `MemorySaver` + `thread_id`.

**Steps:**
1. Create `app/agent/graph.py`:
   ```python
   from langgraph.graph import StateGraph, START, END
   from langgraph.checkpoint.memory import MemorySaver
   from langgraph.types import Command

   def build_graph():
       graph = StateGraph(AgentState)

       # Nodes — single hitl node (not 5), single monitor node
       graph.add_node("agent", agent_node)
       graph.add_node("tools", tool_node)
       graph.add_node("hitl", hitl_node)          # uses interrupt() internally
       graph.add_node("monitor", monitor_node)      # Phase 6.10 — re-queries feeder after dispatch

       # Edges
       graph.add_edge(START, "agent")
       graph.add_conditional_edges("agent", route_after_agent, {
           "tools": "tools",
           "hitl": "hitl",
           "monitor": "monitor",
           END: END,
       })
       graph.add_edge("tools", "agent")
       graph.add_edge("hitl", "agent")       # after Command(resume) the graph re-enters hitl_node, then routes back to agent
       graph.add_conditional_edges("monitor", route_after_monitor, {
           "hitl": "hitl",       # berth conflict → re-compute → HITL
           "agent": "agent",     # no conflict → continue
           END: END,
       })

       checkpointer = MemorySaver()
       return graph.compile(checkpointer=checkpointer)

   def route_after_agent(state: AgentState) -> str:
       if state.get("pending_tool_calls"):
           return "tools"
       if state.get("hitl_pending"):
           return "hitl"
       if state.get("escalation"):
           # Escalation sets hitl_pending to HITL-5 — route to hitl
           state["hitl_pending"] = HITL_GATES["HITL-5"]
           return "hitl"
       # After dispatch tools have run, check if monitoring is needed
       if state.get("context", {}).get("dispatched") and not state.get("context", {}).get("monitored"):
           return "monitor"
       return END

   def route_after_monitor(state: AgentState) -> str:
       if state.get("escalation") or state.get("hitl_pending"):
           return "hitl"
       if state.get("deviation_log"):
           return "agent"  # re-plan after deviation
       return END
   ```
2. Create `app/agent/run.py`:
   ```python
   from langgraph.types import Command
   import uuid

   async def run_agent(event: ITTCoordinationEvent) -> dict:
       graph = build_graph()
       run_id = f"run-{uuid.uuid4().hex[:8]}"
       initial_state = create_initial_state(event, run_id)  # charter bootstrap: 11 fields
       config = {"configurable": {"thread_id": run_id}}
       # Broadcaster is a singleton at app.agent.sse.broadcaster — nodes import it directly,
       # not via state (avoids checkpoint serialization of queue objects).
       # SSE replay buffer (Phase 7.1) ensures events before GET /stream/{run_id} are replayed.
       # If graph hit interrupt, result will contain __interrupt__ — caller must resume via:
       #   graph.ainvoke(Command(resume={"decision": "approve"}), config=config)
       return {"run_id": run_id, "state": result, "trace": export_trace(result)}

   async def resume_agent(run_id: str, decision: dict) -> dict:
       graph = build_graph()
       config = {"configurable": {"thread_id": run_id}}
       result = await graph.ainvoke(Command(resume=decision), config=config)
       return {"run_id": run_id, "state": result, "trace": export_trace(result)}

   def create_initial_state(event: ITTCoordinationEvent, run_id: str) -> AgentState:
       # Charter §3 T6 bootstrap — must include all 11 fields
       now = datetime.now(timezone.utc).isoformat()
       # Validate: container_count >= 50, tuas_vessel_departure > now + 2h
       assert event.container_count >= 50, "container_count must be >= 50"
       assert event.tuas_vessel_departure > now, "vessel departure must be in future"
       return {
           "messages": [{"role": "user", "content": f"ITT coordination request: {event.model_dump_json()}"}],
           "tool_results": {},
           "hitl_pending": None,
           "hitl_history": [],
           "confidence": 1.0,
           "escalation": None,
           "trace": [],
           "deviation_log": [],
           "problem_config": load_problem_config("pb-12-itt"),
           "run_id": run_id,
           "status": "running",
           "context": {
               "event": event.model_dump(),
               "origin_terminal": event.origin_terminal,
               "destination_terminal": event.destination_terminal,
               "vessel_id": event.vessel_id,
               "container_count": event.container_count,
               "tuas_vessel_departure": event.tuas_vessel_departure,
               "blocks_affected": event.blocks_affected,
               "dg_containers": event.dg_containers,
               "current_step": "ingest",
           },
       }
   ```
3. Wire webhook endpoint (`POST /webhook/itt-coordination` in `app/main.py`) to `run_agent`:
   ```python
   @app.post("/webhook/itt-coordination")
   async def webhook_itt(event: ITTCoordinationEvent):
       result = await run_agent(event, broadcaster=sse_broadcaster)
       if "__interrupt__" in result["state"]:
           return {"status": "waiting_hitl", "run_id": result["run_id"], "hitl_card": result["state"]["__interrupt__"]}
       return {"status": "completed", "run_id": result["run_id"], "result": result["state"]}
   ```
4. Wire HITL resume endpoint (`POST /agent/hitl/respond` in `app/main.py`):
   ```python
   @app.post("/agent/hitl/respond")
   async def hitl_respond(req: HITLResponse):
       result = await resume_agent(req.run_id, {"decision": req.decision, "reason": req.reason, "modifications": req.modifications})
       if "__interrupt__" in result["state"]:
           return {"status": "waiting_hitl", "hitl_card": result["state"]["__interrupt__"]}
       return {"status": "completed", "result": result["state"]}
   ```

**Verification:**
```bash
python -c "from app.agent.graph import build_graph; g = build_graph(); print('Graph compiled OK')"
```

### 6.10: Monitoring / Re-computation Loop (Steps 12–17)
**Duration:** ~3 hours
**What:** Implement the post-dispatch monitoring loop that detects feeder berth conflicts and triggers re-planning.

> **Charter to-be workflow steps 12–17:** After dispatch (step 9–11), agent monitors feeder via PORTNET at T+21 min, detects berth conflict, re-computes 80/40 → 100/20, presents emergency HITL card, dispatches delta trucks, updates Tuas sequence, logs deviation.

**Steps:**
1. Create `app/agent/monitor.py`:
   ```python
   async def monitor_node(state: AgentState) -> AgentState:
       # Called after dispatch — re-queries feeder status
       from app.tools.registry import registry

       # Mark monitoring started
       state["context"]["monitored"] = True
       state["trace"].append({"event": "monitor_start", "timestamp": now()})

       # Re-query T3 with current_time = now
       feeder_id = state["context"].get("feeder_id", "FEEDER ATLANTIC-03")
       result = await registry.call("check_sea_itt_capacity", feeder_id=feeder_id, current_time=now())

       # Check for deviation: berth_status changed, departure delayed, tidal risk
       previous = state["context"].get("sea_capacity", {})
       current = result.output

       deviation = None
       if current.get("berth_status") == "conflict" or current.get("departure_window", {}).get("latest") != previous.get("departure_window", {}).get("latest"):
           # Berth conflict detected — triggers escalation #2 (hold > 1.5h) + #1 (confidence drop)
           deviation = {
               "type": "feeder_berth_conflict",
               "previous_window": previous.get("departure_window"),
               "current_window": current.get("departure_window"),
               "impact": "feeder delayed to 1600, may miss downstream tidal window",
               "detected_at": now(),
           }
           state["deviation_log"].append(deviation)
           state["context"]["sea_capacity"] = current
           state["confidence"] = 0.78  # below 0.85 → triggers escalation #1
           state["context"]["feeder_hold_hours"] = 2.0  # above 1.5h → triggers escalation #2
           state["escalation"] = {"trigger": "feeder_berth_conflict", "deviation": deviation}
           # Re-compute split with updated sea capacity
           new_split = await registry.call("compute_itt_split",
               candidates=state["context"]["candidates"],
               road_capacity=state["context"]["road_capacity"],
               sea_capacity=current,
               tuas_vessel_departure=state["context"]["tuas_vessel_departure"],
               constraints=state["context"].get("constraints", {}))
           state["context"]["split_result"] = new_split.output["optimal_split"]
           state["context"]["split_alternatives"] = new_split.output["alternatives"]
           state["context"]["previous_split"] = previous.get("optimal_split")
           # Route to emergency HITL (HITL-5 or re-present HITL-1 with updated card)
           state["hitl_pending"] = HITL_GATES["HITL-5"]
           state["hitl_pending"]["approval_card"] = build_emergency_resplit_card(state, deviation)
           state["trace"].append({"event": "deviation_detected", "deviation": deviation, "new_split": new_split.output["optimal_split"]})
       else:
           state["trace"].append({"event": "monitor_no_deviation", "timestamp": now()})

       # Check data staleness (trigger #4) while monitoring
       stale = check_data_stale(state, threshold_minutes=30)
       if stale:
           state["escalation"] = {"trigger": "data_stale", "message": "Container data is stale (>30 min)"}
           state["hitl_pending"] = HITL_GATES["HITL-5"]

       return state

   def build_emergency_resplit_card(state, deviation) -> dict:
       return {
           "title": "EMERGENCY RE-SPLIT REQUIRED",
           "reason": deviation["impact"],
           "previous_split": state["context"].get("previous_split"),
           "new_split": state["context"]["split_result"],
           "cost_impact": "+$1,500 road cost but avoids $5,000 missed connection",
           "delta_trucks": "+4 trucks (10 additional trips)",
           "confidence": state["confidence"],
       }
   ```
2. After emergency HITL approval → dispatch delta trucks → update Tuas loading sequence (second T5 call)
3. Wire `monitor_node` into graph (see 6.9 `monitor` node + `route_after_monitor`)

**Verification:**
```bash
pytest app/tests/test_monitor.py -v
# Inject feeder conflict → monitor detects → re-compute → HITL-5 fires → approve → delta dispatch
```

### 6.11: End-to-End Integration Test
**Duration:** ~3 hours
**What:** Test the full pipeline including monitoring loop + deviation recovery.

**Steps:**
1. Create `app/tests/test_agent_e2e.py`:
   - Test with mocked LLM (deterministic responses)
   - Test with real LLM (if API key available)
   - **Happy path** (10 steps):
     1. Send ITT_COORDINATION_REQUEST event (120 containers, MV PACIFIC STAR)
     2. Agent reasons, calls T1/T2/T3 (T1 vessel_id, T2 terminal + time_window, T3 feeder_id + current_time)
     3. Agent calls T4 (compute_itt_split with tuas_vessel_departure + constraints) → 80/40 = $10,400
     4. HITL-1 Approve ITT Split fires → auto-approve (test mode via Command(resume))
     5. HITL-2 Approve Truck Dispatch fires → auto-approve
     6. HITL-3 Approve Feeder Hold fires → auto-approve
     7. Agent calls dispatch_road_itt (num_trucks + route) + request_feeder_hold (feeder_id + hold_hours)
     8. Agent calls T5 update_tuas_loading_sequence (vessel_id + ETAs + container_ids)
     9. HITL-4 Approve Loading Sequence fires → auto-approve
     10. Result returned with full trace + deviation_log (empty)
   - **Deviation path** (7 additional steps after step 10):
     11. Inject feeder berth conflict (mutate mock data)
     12. Monitor node re-queries T3 → detects conflict
     13. Agent re-computes T4 → 100/20 = $11,200
     14. HITL-5 Emergency Re-Split fires → auto-approve
     15. Agent dispatches delta trucks (+4 trucks / +10 trips)
     16. Agent calls T5 again with updated ETAs
     17. Result with deviation_log entry + re-split trace
   - Verify: all tools called, all HITL gates fired (with correct timeout_action per gate), escalation triggers #1+#2 fire on deviation, trace + deviation_log populated
   - Charter trace verification: wall time, token counts, confidence trajectory 0.95→0.78→0.90

**Verification:**
```bash
pytest app/tests/test_agent_e2e.py -v  # full pipeline completes
```

### 6.12: Resilience — Rate Limit, Stale Resume, Concurrency, Webhook Validation
**Duration:** ~2 hours
**What:** Harden the agent against real-world failure modes the competition will probe.

**Steps:**
1. Create `app/agent/resilience.py`:
   ```python
   # a. LLM rate limit (429) — wrap provider.chat with retry + fallback
   async def chat_with_rate_limit(provider, messages, tools, retries=2):
       for attempt in range(retries + 1):
           try:
               return await provider.chat(messages, tools=tools)
           except RateLimitError as e:
               if attempt < retries:
                   await asyncio.sleep(2 ** attempt)  # exponential backoff
                   continue
               # Fall back to fallback provider (ProblemConfig.llm.fallback_provider)
               fallback = create_provider(fallback_config)
               return await fallback.chat(messages, tools=tools)

   # b. Stale HITL resume guard — reject late approve after timeout already fired
   def is_hitl_stale(state: AgentState, gate_id: str) -> bool:
       return state.get("status") in ("halted", "cancelled", "holding") and state.get("hitl_pending") is None

   # In resume_agent (6.9), check before Command(resume=):
   #   if is_hitl_stale(snapshot_state, req.gate_id): return {"status": "stale", "error": f"HITL {gate_id} already timed out → {status}"}

   # c. SSE disconnect — Last-Event-ID replay
   #    Broadcaster buffer (Phase 7.1) already replays on reconnect; add Last-Event-ID header support:
   #    GET /agent/stream/{run_id} with Header Last-Event-ID → replay from that index
   ```
2. Webhook validation error path — `POST /webhook/itt-coordination` must return 422 (Pydantic), NOT 500:
   ```python
   @app.post("/webhook/itt-coordination")
   async def webhook_itt(event: ITTCoordinationEvent):  # FastAPI auto-validates → 422
       try:
           result = await run_agent(event)
       except ValidationError as e:
           raise HTTPException(422, detail=str(e))
       except Exception as e:
           structured_log("webhook_error", event_type="webhook_failed", error=str(e))
           raise HTTPException(500, detail="Agent failed")
       ...
   ```
3. Concurrency isolation — `inject_feeder_berth_conflict` currently mutates global `app/mocks/data.py`. Document: single demo at a time; `POST /agent/reset-mocks` restores clean state. For concurrent runs, Phase 5.8 stores per-`run_id` overrides in `app/mocks/data.py:_overrides: dict[run_id, dict]` so T3 lookup checks `overrides.get(run_id)` first.
4. Wire `chat_with_rate_limit` into `agent_node` (Phase 6.3) instead of raw `provider.chat`.
5. Add `app/tests/test_resilience.py`: 429→retry→fallback, stale resume→422, SSE reconnect→replay, concurrent inject→isolated, webhook invalid→422 (not 500), LangSmith export failure→no crash.

**Verification:**
```bash
pytest app/tests/test_resilience.py -v  # all resilience scenarios pass
```

## Verification Loop

After all sub-phases complete:
1. `pytest app/tests/ -v` — all tests pass (including test_monitor, test_hitl with Command resume, test_escalation charter thresholds, test_validation guardrails, test_resilience)
2. Graph compiles without errors — `python -c "from app.agent.graph import build_graph; g = build_graph(); print('OK')"`
3. Agent processes a test event end-to-end (happy path + deviation path via 6.11)
4. HITL gates fire with correct timeout/timeout_action per gate; `Command(resume=)` pattern works with `thread_id`; stale resume after timeout returns `stale` error
5. All 7 escalation triggers use charter thresholds (0.85, 1.5h, $10k, 30min, 60%, 15min, planner_conflict)
6. Confidence scores use LLM self-assessment with deterministic backup; threshold 0.85; risk_score in every TraceEntry
7. Execution trace + deviation_log + structured logging all populated; `export_trace` includes deviations + risk_score trajectory
8. Input validation guardrails checked at webhook (422, not 500) + T4 + post-approval
9. Monitoring loop: inject conflict → re-query T3 → detect → re-compute T4 → emergency HITL → delta dispatch
10. LangSmith trace export failure does not crash agent (try/except)
11. Resilience: 429→fallback, tool timeout vs 503 distinct, hallucinated tool→error ToolResult, partial batch→continue
12. Provider observability: `LLMResponse.latency_ms`, `usage.input_tokens/output_tokens`, `raw`, `finish_reason` logged to trace

## Commit
After verification: `git commit -m "Phase 6: Agent core — LangGraph graph, HITL gates, escalation triggers, confidence, trace"`
