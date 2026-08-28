# Phase 6.5: Integration Wiring & Cleanup

## Goal
Fix all missing connections between components — requirements, startup validation, HITL timeouts, SSE events, config consistency, dead code cleanup — so the system actually runs end-to-end without silent failures.

## Depends on
Phase 6

## Requirements
T-18 (notification SSE), A-17 (HITL resume), D-08 (Docker prep), plus new: startup validation, timeout scheduler, config consistency

## Success Criteria
1. `pip install -r requirements.txt` installs all dependencies (including `langgraph`) without encoding errors
2. `.env.example` documents all env vars; `load_dotenv()` wires them at startup
3. App fails fast with clear error if required env vars missing (no silent 401 at first LLM call)
4. `lifespan` handler validates env vars, YAML configs, registry, graph compilation at startup
5. HITL timeout scheduler auto-fires `timeout_action` after `timeout_seconds` per gate
6. SSE events `confidence_update` and `notification` published by relevant nodes
7. All 7 YAML configs have consistent `fallback_api_key_env` field
8. `prototype/` deleted, `__init__.py` modules re-export, `tool_adapter.py` relocated
9. LangSmith tracing wired (optional, activates if `LANGSMITH_API_KEY` set)
10. All existing tests still pass + new tests for startup, timeout, SSE coverage

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Startup Lifespan                           │
│                                                              │
│  1. load_dotenv() → read .env                                │
│  2. Validate ANTHROPIC_API_KEY (or configured provider key)  │
│  3. Load all 7 YAML configs → verify parse                   │
│  4. Init registry → verify TOOLSETS resolve                  │
│  5. Compile graph → verify MemorySaver wired                 │
│  6. (Optional) Init LangSmith if LANGSMITH_API_KEY set       │
│  7. Log "PSA Nexus ready" with provider + model info         │
│                                                              │
│  On failure: clear error message, exit(1), not silent 401   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    HITL Timeout Scheduler                     │
│                                                              │
│  On HITL gate fire:                                          │
│    → asyncio.create_task(_timeout_monitor(gate, run_id))     │
│    → waits timeout_seconds                                    │
│    → if not cancelled (manual decision arrived):              │
│       - timeout_action == "halt" → auto-reject + log         │
│       - timeout_action == "escalate" → auto-escalate         │
│       - timeout_action == "timeout" → fire timeout decision  │
│    → cancels task on manual approve/reject/modify             │
│                                                              │
│  Background task lives in app/hitl/timeout_scheduler.py      │
└─────────────────────────────────────────────────────────────┘
```

## Plan

### 6.5.1: Fix Dependencies & Environment
**Duration:** ~30 minutes
**What:** Fix the broken requirements file, create `.env` template, wire dotenv loading.

**Steps:**
1. **Fix `requirements.txt` encoding:**
   - Read current file (UTF-16LE with BOM)
   - Rewrite as UTF-8 with CRLF→LF
   - Add missing packages: `langgraph>=0.2.0`, `langsmith>=0.1.0`, `langchain-core>=0.3.0`, `python-dotenv>=1.0.0`
   - Keep all existing pinned versions

2. **Create `.env.example`:**
   ```
   # PSA Nexus — Environment Configuration
   # Copy to .env and fill in your values

   # === Provider API Keys (at least one required) ===
   ANTHROPIC_API_KEY=your-key-here
   OPENAI_API_KEY=your-key-here
   GOOGLE_API_KEY=your-key-here
   DEEPSEEK_API_KEY=your-key-here
   OPENROUTER_API_KEY=your-key-here
   CUSTOM_API_KEY=your-key-here

   # === LLM Config (overridden by YAML llm section) ===
   # LLM_PROVIDER=anthropic
   # LLM_MODEL=claude-sonnet-4-20250514
   # LLM_BASE_URL=

   # === LangSmith (optional — enables trace export) ===
   # LANGSMITH_API_KEY=your-key-here
   # LANGCHAIN_PROJECT=psa-nexus

   # === Logging ===
   # LOG_FILE=
   ```

3. **Wire `load_dotenv()` in `app/main.py`:**
   - Add `from dotenv import load_dotenv` at top
   - Call `load_dotenv()` before FastAPI app init
   - This ensures `.env` is loaded before any `os.environ.get()` calls

**Deliverables:**
- `requirements.txt` — UTF-8, all deps including langgraph/langsmith/python-dotenv
- `.env.example` — documented template
- `app/main.py` — `load_dotenv()` called at module level

**Verification:**
```bash
file requirements.txt  # should say "ASCII text" or "UTF-8", not "UTF-16"
pip install -r requirements.txt  # installs without errors
python -c "from dotenv import load_dotenv; print('dotenv OK')"
```

**Depends on:** Phase 6
**Gaps fixed:** C1, C2, C4, M4

---

### 6.5.2: Startup Lifespan & Validation
**Duration:** ~1 hour
**What:** Add FastAPI `lifespan` that validates everything at startup — fail fast with clear errors, not silent 401s.

**Steps:**
1. **Add `lifespan` async context manager to `app/main.py`:**
   ```python
   from contextlib import asynccontextmanager
   import logging, os, sys

   logger = logging.getLogger("psa.nexus.startup")

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # === STARTUP VALIDATION ===
       errors = []

       # 1. Check at least one provider API key is set
       provider_keys = {
           "anthropic": "ANTHROPIC_API_KEY",
           "openai": "OPENAI_API_KEY",
           "gemini": "GOOGLE_API_KEY",
           "deepseek": "DEEPSEEK_API_KEY",
       }
       active_key = os.environ.get("ANTHROPIC_API_KEY", "")
       if not active_key:
           # Check if any fallback key is set
           for name, env_var in provider_keys.items():
               if os.environ.get(env_var, ""):
                   logger.info(f"Using {name} provider (from {env_var})")
                   break
           else:
               errors.append("No provider API key set. Set ANTHROPIC_API_KEY (or any of: OPENAI_API_KEY, GOOGLE_API_KEY, DEEPSEEK_API_KEY)")

       # 2. Validate YAML configs load
       try:
           from app.configs.problem_config import load_problem_config
           for problem_id in ["pb-12-itt", "pb-01-berth", "pb-02-dtqc", "pb-04-feeder", "pb-09-expressway", "pb-10-sea-air", "pb-11-customs"]:
               try:
                   cfg = load_problem_config(problem_id)
                   logger.info(f"  ✓ {problem_id}: {len(cfg.systems)} systems, {len(cfg.tools)} tools")
               except Exception as e:
                   errors.append(f"YAML config {problem_id}: {e}")
       except Exception as e:
           errors.append(f"Config loader failed: {e}")

       # 3. Verify registry initializes
       try:
           from app.tools.registry import registry, TOOLSETS
           logger.info(f"  ✓ Registry: {len(TOOLSETS)} problem sets registered")
       except Exception as e:
           errors.append(f"Registry init failed: {e}")

       # 4. Verify graph compiles
       try:
           from app.agent.graph import build_graph
           graph = build_graph()
           logger.info(f"  ✓ Graph compiled: {len(graph.get_graph().nodes)} nodes")
       except Exception as e:
           errors.append(f"Graph compilation failed: {e}")

       # 5. LangSmith (optional)
       if os.environ.get("LANGSMITH_API_KEY"):
           logger.info("  ✓ LangSmith tracing enabled")
       else:
           logger.info("  ○ LangSmith tracing disabled (set LANGSMITH_API_KEY to enable)")

       # === FAIL FAST ===
       if errors:
           for err in errors:
               logger.error(f"  ✗ {err}")
           logger.critical("PSA Nexus startup FAILED — fix errors above")
           sys.exit(1)

       provider_name = os.environ.get("LLM_PROVIDER", "anthropic")
       logger.info(f"PSA Nexus ready — provider: {provider_name}")
       logger.info(f"  Dashboard: http://localhost:8000/ui/")
       logger.info(f"  Health: http://localhost:8000/health")

       yield

       # === SHUTDOWN ===
       logger.info("PSA Nexus shutting down")
   ```

2. **Wire lifespan into FastAPI app:**
   - Change `app = FastAPI(title=...)` to `app = FastAPI(title=..., lifespan=lifespan)`

3. **Verify existing tests still pass** — lifespan should not break test setup (tests use `TestClient` which triggers lifespan; need to ensure test env has mock keys or tests bypass validation)

**Deliverables:**
- `app/main.py` — `lifespan` context manager with 5-point validation
- Startup logs: clear ✓/✗ per check, fail fast with actionable messages

**Verification:**
```bash
# Without API key → clear error, exits
unset ANTHROPIC_API_KEY; python -m uvicorn app.main:app
# → "No provider API key set. Set ANTHROPIC_API_KEY..."

# With API key → validates all configs, logs OK
ANTHROPIC_API_KEY=test python -m uvicorn app.main:app
# → "PSA Nexus ready — provider: anthropic"
```

**Depends on:** 6.5.1
**Gaps fixed:** C3

---

### 6.5.3: HITL Timeout Scheduler
**Duration:** ~1.5 hours
**What:** Build background task that auto-fires timeout decisions when HITL gates exceed their timeout.

**Steps:**
1. **Create `app/hitl/timeout_scheduler.py`:**
   ```python
   import asyncio
   import logging
   from typing import Optional

   logger = logging.getLogger("psa.nexus.hitl.timeout")

   # Active timeout tasks per (run_id, gate_name) → asyncio.Task
   _active_timeouts: dict[tuple[str, str], asyncio.Task] = {}

   async def schedule_timeout(
       run_id: str,
       gate_name: str,
       timeout_seconds: float,
       timeout_action: str,
       on_timeout,  # async callable
   ):
       """Schedule a timeout for a HITL gate. Cancels any existing timeout for this gate."""
       key = (run_id, gate_name)

       # Cancel existing timeout if any
       cancel_timeout(run_id, gate_name)

       async def _wait_and_fire():
           try:
               await asyncio.sleep(timeout_seconds)
               logger.warning(f"TIMEOUT: {gate_name} on run {run_id} after {timeout_seconds}s — firing {timeout_action}")
               await on_timeout(run_id, gate_name, timeout_action)
           except asyncio.CancelledError:
               logger.info(f"Timeout cancelled for {gate_name} on run {run_id} (manual decision arrived)")
           finally:
               _active_timeouts.pop(key, None)

       task = asyncio.create_task(_wait_and_fire())
       _active_timeouts[key] = task
       logger.info(f"Scheduled timeout for {gate_name}: {timeout_seconds}s → {timeout_action}")

   def cancel_timeout(run_id: str, gate_name: str):
       """Cancel a pending timeout (called when manual decision arrives)."""
       key = (run_id, gate_name)
       task = _active_timeouts.pop(key, None)
       if task and not task.done():
           task.cancel()
           logger.info(f"Cancelled timeout for {gate_name} on run {run_id}")

   def cancel_all_timeouts(run_id: str):
       """Cancel all timeouts for a run (e.g., on run completion)."""
       keys_to_cancel = [k for k in _active_timeouts if k[0] == run_id]
       for key in keys_to_cancel:
           task = _active_timeouts.pop(key, None)
           if task and not task.done():
               task.cancel()
   ```

2. **Wire into HITL gate firing** — when `hitl_node` fires an interrupt:
   - Read `timeout_seconds` and `timeout_action` from gate config
   - Call `schedule_timeout(run_id, gate_name, timeout_seconds, timeout_action, on_timeout_callback)`
   - The callback calls `resume_agent(run_id, {"decision": "timeout", "gate": gate_name})`

3. **Wire cancellation** — when `POST /agent/hitl/respond` receives a manual decision:
   - Call `cancel_timeout(run_id, gate_name)` before processing the decision

4. **Wire cleanup** — when run completes or resets:
   - Call `cancel_all_timeouts(run_id)`

5. **Test:** verify timeout fires after N seconds, verify cancellation on manual approve

**Deliverables:**
- `app/hitl/timeout_scheduler.py` — `schedule_timeout()`, `cancel_timeout()`, `cancel_all_timeouts()`
- `app/hitl/gates.py` — calls `schedule_timeout()` when firing interrupt
- `app/agent/run.py` — calls `cancel_timeout()` on manual decision, `cancel_all_timeouts()` on run end
- `app/tests/test_timeout_scheduler.py` — unit tests (mock asyncio.sleep)

**Verification:**
```bash
# Start agent → HITL gate fires → wait timeout_seconds → auto-timeout decision
# Manual approve before timeout → timeout cancelled, no double-fire
pytest app/tests/test_timeout_scheduler.py -v
```

**Depends on:** 6.5.1
**Gaps fixed:** H1

---

### 6.5.4: SSE Events & Config Consistency
**Duration:** ~1 hour
**What:** Publish missing SSE events, fix YAML config inconsistency, fix code bug.

**Steps:**
1. **Publish `confidence_update` events** — in `app/agent/nodes.py`:
   - After confidence score is computed/updated, call `broadcaster.publish(run_id, "confidence_update", {"confidence": state["confidence"], "risk_score": state.get("risk_score", 0.0)})`
   - Location: in `agent_node` after line ~200 (confidence computation) and in `monitor_node` after deviation detection

2. **Publish `notification` events** — in `app/tools/notify.py`:
   - The `notify_parties()` tool already logs to trace. Add: `await broadcaster.publish(run_id, "notification", {"message": message, "parties": parties, "timestamp": ...})`
   - Need to pass `run_id` into the tool context (check how other tools get it — likely from `ToolResult.metadata`)

3. **Add `fallback_api_key_env` to 6 YAML configs:**
   - `pb-01-berth.yaml`: add `fallback_api_key_env: OPENAI_API_KEY`
   - `pb-02-dtqc.yaml`: add same
   - `pb-04-feeder.yaml`: add same
   - `pb-09-expressway.yaml`: add same
   - `pb-10-sea-air.yaml`: add same
   - `pb-11-customs.yaml`: add same
   - (pb-12-itt.yaml already has it)

4. **Fix unreachable exception handler** in `app/main.py`:
   - Lines 218-227: second `except HTTPException: raise` is unreachable
   - Remove the dead `except` blocks, keep only the correct error handling

**Deliverables:**
- `app/agent/nodes.py` — `confidence_update` SSE events published
- `app/tools/notify.py` — `notification` SSE events published
- 6 YAML configs — `fallback_api_key_env` added
- `app/main.py` — dead exception handler removed

**Verification:**
```bash
# SSE stream shows confidence_update events during agent reasoning
curl -N localhost:8000/agent/stream/{run_id} | grep "confidence_update"
# Notification events appear when notify_parties() is called
# All 7 YAML configs have fallback_api_key_env
python -c "from app.configs.problem_config import load_problem_config; [print(f'{p}: {load_problem_config(p).llm}') for p in ['pb-01-berth','pb-12-itt']]"
```

**Depends on:** 6.5.1
**Gaps fixed:** H3, H5, M5

---

### 6.5.5: Cleanup & Relocation
**Duration:** ~1.5 hours
**What:** Delete dead code, re-export modules, relocate mispathed files, wire optional LangSmith.

**Steps:**
1. **Delete `prototype/` directory:**
   - `rm -rf prototype/`
   - Verify no imports from `app/` reference `prototype/` (already confirmed: zero matches)

2. **Re-export from `app/agent/__init__.py`:**
   ```python
   """PSA Nexus Agent — LangGraph-based multi-party coordination."""

   from app.agent.graph import build_graph
   from app.agent.state import AgentState
   from app.agent.run import run_agent, resume_agent
   from app.agent.problem_switcher import switch_problem, get_active_problem_id

   __all__ = ["build_graph", "AgentState", "run_agent", "resume_agent", "switch_problem", "get_active_problem_id"]
   ```

3. **Re-export from `app/hitl/__init__.py`:**
   ```python
   """PSA Nexus HITL — Human-in-the-loop gates with interrupt/resume."""

   from app.hitl.gates import hitl_node
   from app.hitl.handler import handle_hitl_response
   from app.hitl.models import HITL_GATES
   from app.hitl.timeout_scheduler import schedule_timeout, cancel_timeout

   __all__ = ["hitl_node", "handle_hitl_response", "HITL_GATES", "schedule_timeout", "cancel_timeout"]
   ```

4. **Relocate `app/shared/tool_adapter.py` → `app/tools/tool_adapter.py`:**
   - `mv app/shared/tool_adapter.py app/tools/tool_adapter.py`
   - Update all imports: `from app.shared.tool_adapter import adapt_tools_for_provider` → `from app.tools.tool_adapter import adapt_tools_for_provider`
   - Search codebase for all references and update

5. **Wire LangSmith tracing (optional):**
   - In `app/agent/graph.py`, after graph compilation:
     ```python
     import os
     if os.environ.get("LANGSMITH_API_KEY"):
         os.environ["LANGCHAIN_TRACING_V2"] = "true"
         os.environ["LANGCHAIN_PROJECT"] = os.environ.get("LANGCHAIN_PROJECT", "psa-nexus")
     ```
   - This enables LangSmith trace export if the API key is present; no-op otherwise

6. **Verify all tests still pass** after relocation

**Deliverables:**
- `prototype/` — deleted
- `app/agent/__init__.py` — convenience re-exports
- `app/hitl/__init__.py` — convenience re-exports
- `app/tools/tool_adapter.py` — relocated from `app/shared/`
- All imports updated across codebase
- LangSmith wiring in `app/agent/graph.py`

**Verification:**
```bash
ls prototype/  # should not exist
python -c "from app.agent import build_graph, AgentState; print('agent re-exports OK')"
python -c "from app.hitl import hitl_node, HITL_GATES; print('hitl re-exports OK')"
python -c "from app.tools.tool_adapter import adapt_tools_for_provider; print('tool_adapter relocated OK')"
pytest app/tests/ -v  # all pass
```

**Depends on:** 6.5.1
**Gaps fixed:** M1, M2, M3, M5

---

### 6.5.6: Integration Tests
**Duration:** ~30 minutes
**What:** Add tests that verify all wiring works together.

**Steps:**
1. **`app/tests/test_startup.py`:**
   - Test lifespan validation catches missing API key
   - Test lifespan validates all 7 YAML configs
   - Test lifespan verifies registry initializes
   - Test lifespan verifies graph compiles
   - (Use `unittest.mock.patch.dict` to control env vars)

2. **`app/tests/test_timeout.py`:**
   - Test `schedule_timeout()` fires after N seconds
   - Test `cancel_timeout()` prevents firing
   - Test `cancel_all_timeouts()` clears all for a run
   - (Use `asyncio` test with short timeouts)

3. **`app/tests/test_sse_events.py`:**
   - Test `confidence_update` event is published during agent reasoning
   - Test `notification` event is published when `notify_parties()` is called
   - (Mock broadcaster, verify `publish()` called with correct event types)

4. **`app/tests/test_configs.py`:**
   - Test all 7 YAML configs have `fallback_api_key_env`
   - Test all configs load without error
   - Test `llm` section has required fields

**Deliverables:**
- `app/tests/test_startup.py` — 4 tests
- `app/tests/test_timeout.py` — 3 tests
- `app/tests/test_sse_events.py` — 2 tests
- `app/tests/test_configs.py` — 3 tests

**Verification:**
```bash
pytest app/tests/test_startup.py app/tests/test_timeout.py app/tests/test_sse_events.py app/tests/test_configs.py -v
# All 12 new tests pass
pytest app/tests/ -v  # full suite still passes
```

**Depends on:** 6.5.2, 6.5.3, 6.5.4, 6.5.5
**Gaps fixed:** verification for all

---

## Verification Loop

After all sub-phases complete:
1. `pip install -r requirements.txt` — installs cleanly (UTF-8, langgraph present)
2. `cp .env.example .env` + fill key → app starts, lifespan logs all ✓
3. `unset ANTHROPIC_API_KEY && python -m uvicorn app.main:app` — fails fast with clear error
4. HITL timeout fires after `timeout_seconds` automatically
5. SSE stream includes `confidence_update` and `notification` events
6. All 7 YAML configs consistent
7. `prototype/` deleted, imports clean
8. `pytest app/tests/ -v` — all pass (existing + 12 new)
9. No regressions in existing 127 tests
