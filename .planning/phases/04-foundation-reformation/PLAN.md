# Phase 4: Foundation Reformation + Platform Generalisation (PSA Nexus)

## Goal
Clean up the fragmented prototype into a unified foundation for PSA Nexus. Directory restructure, deduplication, provider validation, YAML wiring for ALL 7 C2 problems, and the platform switching mechanism that makes it a generalizable platform.

## Depends on
Phase 3 (complete)

## Requirements
F-01 through F-13

## Success Criteria
1. Unified FastAPI app starts on port 8000 with `/health`, `/agent/*`, `/mocks/*`, `/ui/*`, `/agent/switch-problem/{id}`
2. Directory restructured: `app/agent/`, `app/tools/`, `app/mocks/`, `app/hitl/`, `app/ui/`, `app/shared/`, `app/configs/`
3. provider.py + tool adapter tested end-to-end with real API key (tool_calls verified)
4. ALL 7 C2 YAML configs (pb-01..pb-12) load correctly into ProblemConfig dataclass with complete fields
5. Duplicate files consolidated (two webhooks → one, two schema sets → one at `app/shared/models.py`)
6. Problem switching works: `POST /agent/switch-problem/pb-01-berth` re-registers tools, prompt adapts
7. `pytest app/tests/` passes (config loading all 7, provider+adapter, platform generalisation, health)

## Current State
- `prototype/` has ~4,700 lines of Python across 45 files
- `provider.py` (735 lines) — dead code, never imported
- `orchestrator.py` (207 lines) — linear async, no LLM
- Two duplicate webhook handlers
- Three sets of Pydantic schemas (mocks/schemas.py, ppt_citos/models.py, sea_itt/models.py)
- `in_approval/` and `post_approval/` — empty
- YAML configs exist but never loaded by runtime

## Plan

### 4.1: Directory Restructure
**Duration:** ~2 hours
**What:** Create `app/` directory structure, move/salvage code from `prototype/`

**Steps:**
1. Create `app/` with subdirectories: `agent/`, `tools/`, `mocks/routers/`, `hitl/`, `ui/`, `shared/`, `configs/`, `tests/`
2. Copy `prototype/shared/utils/provider.py` → `app/shared/provider.py`
3. Copy `prototype/shared/utils/yaml_reader.py` → `app/shared/yaml_reader.py`
4. Copy `prototype/configs/*.yaml` → `app/configs/`
5. Copy `prototype/mocks/data.py` → `app/mocks/data.py`
6. Copy `prototype/mocks/edge_cases.py` → `app/mocks/edge_cases.py`
7. Create `app/main.py` — unified FastAPI app (placeholder with health endpoint)
8. Create `app/__init__.py`, `app/shared/__init__.py`, `app/mocks/__init__.py`, etc.

**Verification:**
```bash
ls -la app/  # shows all directories
python -c "from app.main import app; print('OK')"
```

### 4.2: Consolidate Mock Servers
**Duration:** ~3 hours
**What:** Merge the two parallel mock implementations into one canonical set.

> **Canonical schema location: `app/shared/models.py`** (aligns with charter Section 9 target `shared/` and Phase 6 `from app.shared.models import ITTCoordinationEvent`). `app/mocks/` must NOT have its own `schemas.py` — if needed, make it a re-export shim.

**Steps:**
1. Create `app/shared/models.py` — merged Pydantic schemas from:
   - `prototype/mocks/schemas.py` (182 lines) — central models
   - `prototype/pre_approval/ppt_citos/models.py` (79 lines) — PPT-specific
   - `prototype/pre_approval/sea_itt/models.py` (177 lines) — sea ITT-specific
   - Resolve duplicates: Container, ContainerBreakdown, WebhookEvent/ITTCoordinationEvent, WebhookResponse
   - Must define `ITTCoordinationEvent` with all 13 charter fields (event_type, timestamp, source, priority, origin_terminal, destination_terminal, vessel_id, tuas_vessel_departure, container_count, containers_ready, blocks_affected, dg_containers, priority_containers, requested_by, notes)
2. Create `app/mocks/routers/citos_ppt.py` — merge from:
   - `prototype/mocks/citos_ppt.py` (14 lines, simple)
   - `prototype/pre_approval/ppt_citos/router.py` (97 lines, richer)
   - Use the richer version, add missing endpoints
3. Create `app/mocks/routers/citos_tuas.py` — from `prototype/mocks/citos_tuas.py`
4. Create `app/mocks/routers/optetruck.py` — from `prototype/mocks/optetruck.py`
5. Create `app/mocks/routers/feeder.py` — from `prototype/mocks/feeder.py`
6. Create `app/mocks/routers/portnet.py` — from `prototype/mocks/portnet.py`
7. Create webhook handler — **NOT in `app/mocks/`** — webhook is the agent entry point (charter T6), not a mock system:
   - Option: implement directly in `app/main.py` as `POST /webhook/itt-coordination` that validates `ITTCoordinationEvent`, bootstraps charter 11-field `initial_state`, and calls `run_agent()` (Phase 6.9)
   - For now, scaffold the endpoint in `app/main.py` with validation + stub; full wiring completed in Phase 6.9
   - If a separate file is needed: `app/agent/webhook.py` (not `app/mocks/routers/webhook.py`)
8. Register mock routers (citos_ppt, citos_tuas, optetruck, feeder, portnet) in `app/mocks/__init__.py`
9. Mount mock routers + webhook in `app/main.py`
10. Delete: `prototype/pre_approval/ppt_citos/`, `prototype/pre_approval/sea_itt/app.py`, `prototype/pre_approval/sea_itt/router.py`, `prototype/pre_approval/sea_itt/models.py`, `prototype/pre_approval/container_readiness/webhook.py`
11. Verify canonical import works before proceeding to 4.5:
   ```bash
   python -c "from app.shared.models import ITTCoordinationEvent, ITTSplitResponse, SeaITTCapacityResponse; print('OK')"
   ```

**Verification:**
```bash
curl localhost:8000/api/citos/ppt/containers  # returns container data
curl localhost:8000/api/optetruck/capacity     # returns truck data
curl localhost:8000/api/feeder/F001            # returns feeder data
curl localhost:8000/api/portnet/feeder/F001    # returns portnet data
curl localhost:8000/webhook/runs               # returns run status
```

### 4.3: Validate provider.py + Tool-Calling Adapter
**Duration:** ~1.5 hours
**What:** Test provider.py end-to-end with a real API key. Build adapter so any provider can call tools.

**Steps:**
1. Copy `prototype/shared/utils/provider.py` → `app/shared/provider.py`
2. Create `app/shared/tool_adapter.py` — translates tool schemas between provider formats:
   ```python
   def adapt_tools_for_provider(schemas: list[dict], provider: str) -> list[dict]:
       """Convert OpenAI-format tool schemas to provider-specific format."""
       if provider == "anthropic":
           # OpenAI: {name, description, parameters: {type, properties}} → Anthropic: {name, description, input_schema}
           return [{"name": s["name"], "description": s["description"], "input_schema": s["parameters"]} for s in schemas]
       elif provider == "gemini":
           # Gemini uses different function declaration format
           return convert_to_gemini(schemas)
       else:  # openai, deepseek, ollama, vllm, custom
           return schemas
   ```
3. Create `app/tests/test_provider.py`:
   - Test `create_provider()` with mock config
   - Test `create_provider_with_fallback()`
   - Test `chat()` with mocked HTTP response
   - Test `chat()` with tool schemas (mocked tool_calls in response)
   - Test `health_check()` with mocked response
   - Test tool adapter for anthropic/gemini/openai
4. Manual test with real API key (if available):
   ```python
   from app.shared.provider import create_provider
   config = {'provider': 'anthropic', 'model': 'claude-sonnet-4-20250514', 'api_key': 'sk-...'}
   p = create_provider(config)
   response = p.chat('Say hello in one word')
   print(response.content)
   # Tool calling test
   tools = [{"name": "get_itt_candidates", "description": "...", "parameters": {...}}]
   response = p.chat([{"role": "user", "content": "Get containers for MV SOPHIA"}], tools=adapt_tools_for_provider(tools, "anthropic"))
   print(response.tool_calls)
   ```
5. Document which providers work and any issues found

**Verification:**
```bash
pytest app/tests/test_provider.py -v  # all tests pass
```

### 4.4: Validate YAML Config System
**Duration:** ~2 hours
**What:** Load pb-12-itt.yaml, verify all fields parse correctly.

**Steps:**
1. Copy `prototype/configs/pb-12-itt.yaml` → `app/configs/pb-12-itt.yaml`
2. Copy other pb-*.yaml files → `app/configs/`
3. Create `app/configs/problem_config.py`:
   - `ProblemConfig` dataclass with all fields from YAML
   - `load_problem_config(problem_id: str) -> ProblemConfig` function
   - Validates required fields, applies defaults
4. Create `app/tests/test_config.py`:
   - Test loading pb-12-itt.yaml
   - Verify: 5 systems, 6 tools, 5 HITL gates, 7 escalation triggers, cost params, LLM settings
   - Test loading other pb-*.yaml files
   - Test missing config raises error

**Verification:**
```bash
python -c "
from app.configs.problem_config import load_problem_config
c = load_problem_config('pb-12-itt')
print(f'Systems: {len(c.systems)}')
print(f'Tools: {len(c.tools)}')
print(f'HITL gates: {len(c.hitl_gates)}')
print(f'Escalation triggers: {len(c.escalation_triggers)}')
"
pytest app/tests/test_config.py -v
```

### 4.5: Consolidate Schemas (Second Pass — Extend & Verify)
**Duration:** ~1 hour
**What:** Second pass on `app/shared/models.py` — extend with Phase 6 placeholder models. Depends on 4.2.

**Steps:**
1. Review `app/shared/models.py` (created in 4.2) — verify no `app/mocks/schemas.py` exists separately
2. Ensure all models from all 3 original sources are included, no duplicate fields
3. Add placeholder models for Phase 6 (forward-declare so imports don't break):
   - `AgentState` (TypedDict placeholder — real definition in `app/agent/state.py` Phase 6.1)
   - `HITLGate`, `HITLDecision` (placeholder — real in `app/hitl/models.py` Phase 6.5)
   - `TraceEntry` (placeholder — real in `app/agent/trace.py` Phase 6.8)
   - Note: placeholders are `Optional` or `TYPE_CHECKING` guarded to avoid circular imports
4. Verify all imports work across the codebase (mocks, tools, agent all import from `app.shared.models`)

**Verification:**
```bash
python -c "
from app.shared.models import (
    ITTCoordinationEvent, ITTSplitResponse, SeaITTCapacityResponse,
    RoadITTCapacityResponse, LoadingSequenceResponse, Container,
    ContainerBreakdown, TruckTripRequirement
)
print('All models imported OK')
"
```

### 4.6: Base Tests
**Duration:** ~2 hours
**What:** Write foundational tests.

**Steps:**
1. Create `app/tests/__init__.py`
2. Create `app/tests/test_health.py`:
   - Test GET /health returns 200
3. Create `app/tests/test_config.py` (from 4.4 — all 7 configs)
4. Create `app/tests/test_provider.py` (from 4.3 — with adapter)
5. Create `app/tests/test_schemas.py`:
   - Test schema serialization/deserialization
6. Create `conftest.py` with shared fixtures

**Verification:**
```bash
pytest app/tests/ -v  # all tests pass
```

### 4.7: Complete Sibling YAML Configs
**Duration:** ~2 hours
**What:** Fill in the 6 incomplete sibling configs so all 7 C2 problems are fully specified.

**Steps:**
1. For each of `pb-01-berth`, `pb-02-dtqc`, `pb-04-feeder`, `pb-09-expressway`, `pb-10-sea-air`, `pb-11-customs`:
   - Add 7 `escalation_triggers` (same thresholds as PB-12, adapted to problem context)
   - Add `confidence: {enabled: true, threshold: 0.85, method: llm_self_assessment}`
   - Add `cost_params` — problem-specific (e.g. PB-01: vessel_demurrage $2500/hr, berth_idle $500/hr, QC repositioning $2000, pilot standby $300/hr, tidal miss $5000)
   - Add `constraints` — problem-specific (e.g. PB-01: max_berths 56, min/max QC per berth, tidal windows)
   - Add `edge_cases` — at least 2 per problem (e.g. PB-01: berth conflict, tidal window miss)
   - Ensure ≥2 `hitl_gates` (most siblings currently have only 1)
2. Validate each: `for id in pb-01 pb-02 pb-04 pb-09 pb-10 pb-11; do load_problem_config($id) && echo "$id OK"; done`

**Verification:**
```bash
for id in pb-01-berth pb-02-dtqc pb-04-feeder pb-09-expressway pb-10-sea-air pb-11-customs pb-12-itt; do
  python -c "from app.configs.problem_config import load_problem_config; c=load_problem_config('$id'); print(f'$id: {len(c.systems)} systems, {len(c.tools)} tools, {len(c.hitl_gates)} gates, {len(c.escalation_triggers)} triggers')"
done
```

### 4.8: Problem Switching Mechanism (PSA Nexus Platform Core)
**Duration:** ~2 hours
**What:** Build the runtime switch that makes Nexus a platform, not a single-problem agent.

**Steps:**
1. Create `app/agent/problem_switcher.py`:
   ```python
   def switch_problem(problem_id: str) -> ProblemConfig:
       config = load_problem_config(problem_id)
       # Validate required fields
       assert config.systems and config.tools and config.hitl_gates
       return config
   ```
2. Create `app/main.py` endpoint:
   ```python
   @app.post("/agent/switch-problem/{problem_id}")
   async def switch_problem_endpoint(problem_id: str):
       config = switch_problem(problem_id)
       # Re-register tools for this problem
       from app.tools.registry import registry
       registry.clear()
       registry.register_many(load_tools_for_problem(problem_id))
       return {"problem_id": problem_id, "systems": config.systems, "tools": registry.get_tool_names(), "hitl_gates": config.hitl_gates}
   ```
3. Enhance `app/tools/registry.py`: add `clear()`, `register_many(tools)`, `get_tool_names()`
4. Enhance `app/agent/prompts.py`: system prompt templated from `ProblemConfig`:
   ```python
   def build_system_prompt(config: ProblemConfig) -> str:
       return f"You are PSA Nexus, coordinating {config.problem.name} ({config.problem.sector}). Systems: {config.systems}. Tools: {config.tools}. ..."
   ```
   Not hardcoded to "ITT planner"

**Verification:**
```bash
curl -X POST localhost:8000/agent/switch-problem/pb-01-berth  # → PB-01 systems/tools
curl -X POST localhost:8000/agent/switch-problem/pb-12-itt    # → back to PB-12
```

### 4.9: Cross-Check + Cost Params + Platform Test
**Duration:** ~1 hour
**What:** Verify all 10 cost param rows + platform generalisability wiring.

**Steps:**
1. Verify `app/configs/problem_config.py` — `CostParams` includes all 10 charter §5 rows; validates on load
2. Create `app/tests/test_platform.py`:
   - Load all 7 configs, verify system/tool/gate counts
   - Switch PB-12 → PB-01 → PB-12, verify tool set changes
   - Verify prompt contains correct problem name after switch
   - Verify cost params parsed for each problem

**Verification:**
```bash
pytest app/tests/test_platform.py -v
```

## Verification Loop

After all sub-phases complete:
1. `pytest app/tests/ -v` — all tests pass (including test_platform, test_config for all 7)
2. `python -m uvicorn app.main:app --port 8000` — app starts
3. `curl localhost:8000/health` — returns OK
4. `curl localhost:8000/api/citos/ppt/containers` — returns data
5. All mock endpoints respond
6. All 7 configs load: `for id in pb-01 pb-02 pb-04 pb-09 pb-10 pb-11 pb-12; do load...; done` → all OK
7. Problem switching: `POST /agent/switch-problem/pb-01-berth` → PB-01 tools; switch back → PB-12
8. Provider + adapter: tool_calls work with any provider
9. Cost params: all 10 rows validated

## Commit
After verification: `git commit -m "Phase 4: Nexus foundation — unified app, 7 configs, problem switching, platform proof"`
