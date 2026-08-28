"""PSA Nexus — Unified FastAPI app (Phase 6).

Mounts: health, mocks, webhook (agent entry point), agent switch-problem,
HITL endpoints, SSE streaming, edge injection.
Canonical schema import: from app.shared.models import ITTCoordinationEvent
"""

import logging
import os
import uuid
from collections import OrderedDict
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.mocks.routers.citos_ppt import router as citos_ppt_router
from app.mocks.routers.citos_tuas import router as citos_tuas_router
from app.mocks.routers.optetruck import router as optetruck_router
from app.mocks.routers.feeder import router as feeder_router
from app.mocks.routers.portnet import router as portnet_router
from app.mocks.routers.notify import router as notify_router
try:
    from app.mocks.routers.vtis import router as vtis_router
except ImportError:
    vtis_router = None  # type: ignore
try:
    from app.mocks.routers.optevoyage import router as optevoyage_router
except ImportError:
    optevoyage_router = None  # type: ignore
try:
    from app.mocks.routers.berth import router as berth_router
except ImportError:
    berth_router = None  # type: ignore
from app.agent.problem_switcher import get_active_problem_id, switch_problem
from app.shared.models import ITTCoordinationEvent, WebhookResponse

# Admin router (config management + API key injection)
from app.admin import admin_router

logger = logging.getLogger("psa-nexus.startup")

# Local provider → API key env var mapping (for startup validation)
_PROVIDER_KEY_MAP: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    # Local providers — no API key required
    "ollama": "",
    "vllm": "",
    "lmstudio": "",
}


def _validate_startup() -> list[str]:
    """Validate env, YAML configs, registry, graph. Returns warnings (never raises)."""
    warnings: list[str] = []

    # 1. Validate API key for active provider
    try:
        from app.configs.problem_config import load_problem_config
        cfg = load_problem_config(get_active_problem_id())
        provider = cfg.llm.get("provider", "anthropic")
        api_key_env = _PROVIDER_KEY_MAP.get(provider, "")
        if api_key_env and not os.environ.get(api_key_env):
            warnings.append(f"Missing env var {api_key_env} for provider '{provider}' — LLM calls will fail")
    except Exception as exc:
        warnings.append(f"Failed to load active config: {exc}")

    # 2. Parse all 7 YAML configs
    import glob as _glob
    from pathlib import Path
    config_dir = Path(__file__).resolve().parent / "configs"
    yaml_count = 0
    for yf in sorted(config_dir.glob("pb-*.yaml")):
        try:
            import yaml
            with open(yf) as f:
                data = yaml.safe_load(f) or {}
            if "problem" not in data:
                warnings.append(f"{yf.name}: missing 'problem' block")
            if "tools" not in data or not data["tools"]:
                warnings.append(f"{yf.name}: missing 'tools'")
            yaml_count += 1
        except Exception as exc:
            warnings.append(f"{yf.name}: YAML parse error: {exc}")
    if yaml_count == 0:
        warnings.append("No YAML configs found in app/configs/")

    # 3. Verify tool registry consistency (pb-12 tools exist)
    try:
        from app.tools.registry import TOOLSETS, _PB12_MODULE_MAP
        for tool_name in TOOLSETS.get("pb-12-itt", []):
            if tool_name not in _PB12_MODULE_MAP:
                warnings.append(f"Registry: pb-12 tool '{tool_name}' not in _PB12_MODULE_MAP")
    except Exception as exc:
        warnings.append(f"Registry check failed: {exc}")

    # 4. Verify graph compiles
    try:
        from app.agent.graph import build_graph
        build_graph()
    except Exception as exc:
        warnings.append(f"Graph compilation failed: {exc}")

    return warnings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifespan — validate configs, register cleanup."""
    # --- startup ---
    warnings = _validate_startup()
    if warnings:
        for w in warnings:
            logger.warning("STARTUP: %s", w)
        print(f"[PSA Nexus] Startup completed with {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  ⚠ {w}")
    else:
        print("[PSA Nexus] Startup validation passed")

    yield  # app is running

    # --- shutdown ---
    try:
        from app.hitl.timeout_scheduler import cancel_all_timeouts
        cancel_all_timeouts()
    except (ImportError, Exception):
        pass
    print("[PSA Nexus] Shutdown complete")

app = FastAPI(
    title="PSA Nexus — Agentic Multi-Party Coordination Platform",
    description="Unified platform for Cluster C2 (7 problems) — flagship PB-12 ITT Coordination",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:8000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount mock routers
app.include_router(citos_ppt_router)
app.include_router(citos_tuas_router)
app.include_router(optetruck_router)
app.include_router(feeder_router)
app.include_router(portnet_router)
app.include_router(notify_router)
if vtis_router is not None:
    app.include_router(vtis_router)
if optevoyage_router is not None:
    app.include_router(optevoyage_router)
if berth_router is not None:
    app.include_router(berth_router)

# Admin router (config management, auth, API key injection)
app.include_router(admin_router)

# ---------------------------------------------------------------------------
# Webhook — agent entry point (charter T6), NOT a mock system
# ---------------------------------------------------------------------------

MAX_RUNS = 100
runs: OrderedDict[str, dict] = OrderedDict()


@app.post("/webhook/itt-coordination", tags=["Webhook"])
async def receive_webhook(event: ITTCoordinationEvent):
    """Webhook endpoint for ITT_COORDINATION_REQUEST events (T6 trigger).

    Validates ITTCoordinationEvent (15 fields), bootstraps charter 11-field
    initial_state, and triggers the agent (Phase 6.9 run_agent).
    Returns 422 on Pydantic validation failure (FastAPI auto), 400 for
    semantic errors like containers_ready > container_count.
    """
    # Resilience helper validation (422, not 500) — container_count, vessel_id, future departure
    try:
        from app.agent.resilience import validate_webhook_event
        ok, err = validate_webhook_event(event.model_dump())
        if not ok:
            raise HTTPException(status_code=422, detail=err)
    except HTTPException:
        raise
    except Exception:
        pass

    # Semantic guard — containers_ready cannot exceed container_count (422, not 400 per A-21)
    if event.containers_ready > event.container_count:
        raise HTTPException(
            status_code=422,
            detail=f"containers_ready ({event.containers_ready}) cannot exceed container_count ({event.container_count})",
        )

    # Wire to Phase 6 agent — use run_agent which creates its own run_id and checkpoint
    try:
        from app.agent.run import run_agent
        result = await run_agent(event)
        run_id = result.get("run_id", f"run-{uuid.uuid4().hex[:8]}")
        state = result.get("state", {})
        trace = result.get("trace", {})
        status = result.get("status", "accepted")
        # Preserve for legacy /webhook/runs endpoint
        # Update global runs dict with full trace and status
        entry = {
            "run_id": run_id,
            "event": event.model_dump(),
            "status": status,
            "hitl_card": result.get("hitl_card"),
            "hitl_pending": result.get("hitl_pending") or state.get("hitl_pending") if isinstance(state, dict) else None,
            "state": state,
            "trace": trace,
            "current_step": (state.get("context", {}) or {}).get("current_step", "ingest") if isinstance(state, dict) else "ingest",
            "origin_terminal": event.origin_terminal,
            "destination_terminal": event.destination_terminal,
            "vessel_id": event.vessel_id,
            "container_count": event.container_count,
            "tuas_vessel_departure": event.tuas_vessel_departure,
            "blocks_affected": event.blocks_affected,
            "dg_containers": event.dg_containers,
            "hitl_history": state.get("hitl_history", []) if isinstance(state, dict) else [],
            "deviation_log": state.get("deviation_log", []) if isinstance(state, dict) else [],
            "confidence": state.get("confidence", 1.0) if isinstance(state, dict) else 1.0,
        }
        runs[run_id] = entry
        if len(runs) > MAX_RUNS:
            runs.popitem(last=False)

        # Return shape compatible with both legacy WebhookResponse and Phase 6 HITL flow
        # If waiting HITL, include hitl_card so client can render
        if status == "waiting_hitl":
            return {"status": status, "run_id": run_id, "hitl_card": result.get("hitl_card"), "hitl_pending": result.get("hitl_pending")}
        return {"status": status, "run_id": run_id, "hitl_card": result.get("hitl_card"), "message": "ITT coordination request received. Agent started."}
    except HTTPException:
        raise
    except ValueError as exc:
        # Validation errors from create_initial_state (e.g., container_count <50)
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        # Structured log but return 500 (or 422 if validation-like)
        try:
            from app.shared.logging import structured_log
            structured_log("webhook_error", run_id="unknown", step="webhook", error=str(exc))
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Agent failed: {exc}")


@app.get("/webhook/runs", tags=["Webhook"])
async def list_runs():
    """List all webhook runs (for verification)."""
    return {"runs": list(runs.values()), "count": len(runs)}


@app.get("/webhook/runs/{run_id}", tags=["Webhook"])
async def get_run_status(run_id: str):
    """Get status of a specific run."""
    if run_id not in runs:
        # Also try to fetch from graph checkpointer if not in memory
        try:
            from app.agent.graph import build_graph
            graph = build_graph()
            snapshot = graph.get_state({"configurable": {"thread_id": run_id}})
            vals = getattr(snapshot, "values", None) or {}
            if vals:
                return {"run_id": run_id, "state": vals, "status": vals.get("status", "unknown")}
        except Exception:
            pass
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return runs[run_id]


# ---------------------------------------------------------------------------
# Agent HITL + SSE + edge injection (Phase 6.9 + 7.1)
# ---------------------------------------------------------------------------

@app.post("/agent/hitl/respond", tags=["Agent"])
async def hitl_respond(payload: dict):
    """Resume agent after HITL decision.

    Expected payload: {"run_id": "...", "decision": "approve|reject|modify|timeout",
                        "reason": "...", "modifications": {...}, "gate_id": "HITL-1"}
    - decision is required
    - run_id is required
    Returns: updated state or waiting_hitl if another gate fires
    Returns 422 if hitl already timed out (stale)
    """
    run_id = payload.get("run_id") or payload.get("runId")
    if not run_id:
        raise HTTPException(status_code=422, detail="run_id required")
    decision = payload.get("decision")
    if not decision:
        raise HTTPException(status_code=422, detail="decision required (approve|reject|modify|timeout)")

    # Stale resume — single source of truth is checkpoint (MemorySaver), not in-memory runs dict
    # runs dict may diverge from checkpoint, so checkpoint is authoritative.
    try:
        from app.agent.graph import build_graph
        from app.agent.resilience import is_hitl_stale
        graph = build_graph()
        snapshot = graph.get_state({"configurable": {"thread_id": run_id}})
        vals = getattr(snapshot, "values", {}) or {}
        if vals and is_hitl_stale(vals, payload.get("gate_id")):
            # Update runs store to terminal for consistency
            if run_id in runs:
                runs[run_id]["status"] = vals.get("status", "halted")
            raise HTTPException(status_code=422, detail=f"HITL {payload.get('gate_id','')} already timed out -> {vals.get('status')}")
        # Fallback: if checkpoint missing but runs shows terminal, treat as stale (with normalized gate check)
        if not vals:
            cur = runs.get(run_id)
            if cur and cur.get("status") in ("halted", "cancelled", "holding", "completed", "failed") and not cur.get("hitl_pending"):
                raise HTTPException(status_code=422, detail=f"HITL {payload.get('gate_id','')} already timed out -> {cur.get('status')}")
    except HTTPException:
        raise
    except Exception:
        # Fallback to runs check if graph unavailable
        cur = runs.get(run_id)
        if cur and cur.get("status") in ("halted", "cancelled", "holding", "completed", "failed") and not cur.get("hitl_pending"):
            raise HTTPException(status_code=422, detail=f"HITL {payload.get('gate_id','')} already timed out -> {cur.get('status')}")

    try:
        from app.agent.run import resume_agent
        result = await resume_agent(run_id, payload)
        # Update runs store
        if run_id in runs:
            # Merge new state
            runs[run_id]["state"] = result.get("state", runs[run_id].get("state"))
            runs[run_id]["trace"] = result.get("trace", runs[run_id].get("trace"))
            runs[run_id]["status"] = result.get("status", runs[run_id].get("status"))
            runs[run_id]["hitl_card"] = result.get("hitl_card")
            runs[run_id]["hitl_pending"] = result.get("hitl_pending")
            runs[run_id]["hitl_history"] = result.get("state", {}).get("hitl_history", []) if isinstance(result.get("state"), dict) else []
            runs[run_id]["deviation_log"] = result.get("state", {}).get("deviation_log", []) if isinstance(result.get("state"), dict) else []
        else:
            runs[run_id] = {
                "run_id": run_id,
                "status": result.get("status", "unknown"),
                "state": result.get("state", {}),
                "trace": result.get("trace", {}),
                "hitl_card": result.get("hitl_card"),
                "hitl_pending": result.get("hitl_pending"),
            }
            if len(runs) > MAX_RUNS:
                runs.popitem(last=False)

        if result.get("status") == "stale":
            raise HTTPException(status_code=422, detail=result.get("error", "stale HITL resume"))
        if result.get("status") == "waiting_hitl":
            return {"status": "waiting_hitl", "run_id": run_id, "hitl_card": result.get("hitl_card"), "hitl_pending": result.get("hitl_pending"), "state": result.get("state")}
        return {"status": result.get("status", "completed"), "run_id": run_id, "result": result.get("state"), "trace": result.get("trace"), "hitl_card": result.get("hitl_card")}
    except HTTPException:
        raise
    except Exception as exc:
        try:
            from app.shared.logging import structured_log
            structured_log("hitl_resume_error", run_id=run_id, step="hitl", error=str(exc))
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"HITL resume failed: {exc}")


@app.get("/agent/stream/{run_id}", tags=["Agent"])
async def stream_agent(run_id: str, request: Request, last_event_id: str | None = Header(default=None)):
    """SSE endpoint with replay buffer — Phase 7.1."""
    try:
        from app.agent.sse import broadcaster
    except ImportError:
        raise HTTPException(status_code=500, detail="SSE broadcaster not available")

    # Support Last-Event-ID via header or query param
    query_id = request.query_params.get("lastEventId") or request.query_params.get("Last-Event-ID")
    effective_last = last_event_id or query_id

    async def event_gen():
        async for chunk in broadcaster.stream(run_id, last_event_id=effective_last):
            yield chunk

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    })


@app.get("/agent/trace/{run_id}", tags=["Agent"])
async def get_trace(run_id: str):
    """Return execution trace for a run."""
    if run_id in runs:
        state = runs[run_id].get("state", {})
        if isinstance(state, dict):
            from app.agent.trace import export_trace
            return export_trace(state)
    try:
        from app.agent.graph import build_graph
        graph = build_graph()
        snapshot = graph.get_state({"configurable": {"thread_id": run_id}})
        vals = getattr(snapshot, "values", {}) or {}
        if vals:
            from app.agent.trace import export_trace
            return export_trace(vals)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    raise HTTPException(status_code=404, detail=f"Run {run_id} not found")


@app.post("/agent/inject-edge-case", tags=["Agent"])
async def inject_edge_case(payload: dict):
    """Inject edge case by mutating mock data layer (NOT AgentState)."""
    case = payload.get("case") or payload.get("edge_case") or payload.get("type")
    feeder_id = payload.get("feeder_id", "FEEDER ATLANTIC-03")
    run_id = payload.get("run_id", "")

    # Per-run overrides support (for concurrency isolation)
    # If run_id provided, we could store per-run override, but for now mutate global
    # so next monitor_node T3 re-query sees conflict
    try:
        from app.tools.edge_cases import inject_feeder_berth_conflict, inject_stale_data
        if case in ("feeder_berth_conflict", "berth_conflict", "feeder_conflict", "ec_1"):
            data = inject_feeder_berth_conflict(feeder_id=feeder_id, new_departure=payload.get("new_departure", "2026-08-19T16:00:00+08:00"), run_id=run_id)
            # Also mark in runs context if run_id provided
            if run_id and run_id in runs:
                ctx = runs[run_id].setdefault("state", {}).setdefault("context", {})
                ctx["injected_edge"] = "feeder_berth_conflict"
            return {"status": "injected", "case": "feeder_berth_conflict", "data": data, "run_id": run_id, "hint": "Inject AFTER dispatch, BEFORE monitor check"}
        elif case in ("stale_data", "data_staleness", "stale", "ec_2", "data_stale"):
            minutes = int(payload.get("minutes", payload.get("stale_minutes", 25)))
            data = inject_stale_data(time_offset_minutes=minutes, run_id=run_id)
            if run_id and run_id in runs:
                ctx = runs[run_id].setdefault("state", {}).setdefault("context", {})
                ctx["stale_minutes"] = minutes
                ctx["data_stale"] = True
            return {"status": "injected", "case": "stale_data", "data": data, "run_id": run_id}
        else:
            raise HTTPException(status_code=422, detail=f"Unknown edge case '{case}'. Use feeder_berth_conflict or stale_data")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/agent/reset-mocks", tags=["Agent"])
async def reset_mocks():
    """Restore clean mock data after edge injection."""
    try:
        from app.tools.edge_cases import reset_edge_cases
        reset_edge_cases()
        # Also clear notification log for clean test isolation if requested
        # Keep it — tests that check notification_log already clear manually
        return {"status": "reset", "message": "Mocks restored to clean state"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/agent/reset/{run_id}", tags=["Agent"])
async def reset_run(run_id: str):
    """Clear a single run's SSE buffer and runs entry."""
    try:
        from app.agent.sse import broadcaster
        broadcaster.clear(run_id)
    except Exception:
        pass
    runs.pop(run_id, None)
    # Also try to clear graph checkpoint (MemorySaver doesn't have delete, but we can reset via pop)
    return {"status": "reset", "run_id": run_id}


@app.post("/agent/run-demo", tags=["Agent"])
async def run_demo(payload: dict | None = None):
    """Trigger demo run (SSE-first): connects SSE before starting agent.

    This endpoint is a convenience wrapper around /webhook/itt-coordination that
    returns run_id immediately so the caller can connect SSE before agent emits.
    """
    # Build default PB-12 event if none provided
    if payload and "event" in payload:
        event_data = payload["event"]
    elif payload and "event_type" in payload:
        event_data = payload
    else:
        # Default PB-12 demo event (120 containers PPT→Tuas) — departure is future per A-21
        from datetime import datetime, timedelta, timezone
        _now = datetime.now(timezone.utc)
        event_data = {
            "event_type": "ITT_COORDINATION_REQUEST",
            "timestamp": (_now - timedelta(minutes=5)).isoformat(),
            "source": "CITOS_PPT",
            "priority": "high",
            "origin_terminal": "PPT",
            "destination_terminal": "TUAS",
            "vessel_id": "MV PACIFIC STAR",
            "tuas_vessel_departure": (_now + timedelta(hours=12)).isoformat(),
            "container_count": 120,
            "containers_ready": 120,
            "blocks_affected": ["B-07", "B-08", "B-12", "B-14"],
            "dg_containers": 3,
            "priority_containers": 45,
            "requested_by": "PPT_Yard_Planner_Lim",
            "notes": "Demo run — 120 containers PPT→Tuas",
        }

    try:
        event = ITTCoordinationEvent(**event_data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid event: {exc}")

    try:
        from app.agent.run import run_agent
        result = await run_agent(event)
        run_id = result.get("run_id")
        runs[run_id] = {
            "run_id": run_id,
            "event": event.model_dump(),
            "status": result.get("status", "waiting_hitl"),
            "hitl_card": result.get("hitl_card"),
            "hitl_pending": result.get("hitl_pending"),
            "state": result.get("state", {}),
            "trace": result.get("trace", {}),
        }
        if len(runs) > MAX_RUNS:
            runs.popitem(last=False)
        return {"run_id": run_id, "status": result.get("status"), "hitl_card": result.get("hitl_card")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Problem switching — PSA Nexus platform core (4.8)
# Consumer of app/tools/registry.py owned by Phase 5.1 — imported lazily
# Single source of truth is app.agent.problem_switcher.get_active_problem_id()
# ---------------------------------------------------------------------------

import app.agent.problem_switcher as _ps  # noqa: E402


@app.post("/agent/switch-problem/{problem_id}", tags=["Agent"])
async def switch_problem_endpoint(problem_id: str):
    """Switch active problem config at runtime.

    Loads new ProblemConfig, delegates tool re-registration to Phase 5.1
    registry if available (lazy import — does NOT require registry file).
    Same LangGraph core, different tools/costs/gates per problem.
    """
    try:
        config = switch_problem(problem_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Delegate to tool registry if it exists (Phase 5.1 ownership)
    tools_via_registry = None
    try:
        from app.tools.registry import registry  # type: ignore

        registry.register_for_problem(problem_id)  # type: ignore[attr-defined]
        try:
            reg_tools = registry.list()  # type: ignore[attr-defined]
            cfg_tools = [t.name for t in config.tools if getattr(t, "type", None) != "event_trigger"]
            merged = list(dict.fromkeys(reg_tools + cfg_tools))
            tools_via_registry = merged
        except Exception:
            tools_via_registry = [t.name for t in config.tools if getattr(t, "type", None) != "event_trigger"]
    except ImportError:
        tools_via_registry = [t.name for t in config.tools]
    except Exception:
        tools_via_registry = [t.name for t in config.tools]

    active = get_active_problem_id()

    return {
        "problem_id": problem_id,
        "active_problem_id": active,
        "systems": [s.name for s in config.systems],
        "tools": tools_via_registry,
        "hitl_gates": [g.label for g in config.hitl_gates],
    }


@app.get("/agent/active-problem", tags=["Agent"])
async def get_active_problem():
    """Return currently active problem id and summary."""
    from app.configs.problem_config import load_problem_config

    cfg = load_problem_config(get_active_problem_id())
    return {
        "active_problem_id": get_active_problem_id(),
        "problem": cfg.problem.__dict__,
        "systems": [s.name for s in cfg.systems],
        "tools": [t.name for t in cfg.tools if getattr(t, "type", None) != "event_trigger"],
        "hitl_gates": [g.label for g in cfg.hitl_gates],
    }


# ---------------------------------------------------------------------------
# UI static mount (Phase 7) — serves app/ui/index.html, style.css, app.js, admin.html
# ---------------------------------------------------------------------------

@app.get("/admin", tags=["UI"], include_in_schema=False)
async def admin_page():
    """Serve admin config page (auth handled by /api/admin/* endpoints)."""
    import pathlib
    p = pathlib.Path(__file__).resolve().parent / "ui" / "admin.html"
    if p.exists():
        return FileResponse(str(p), media_type="text/html")
    raise HTTPException(status_code=404, detail="admin.html not found")


@app.get("/mocks/", tags=["Mocks"])
@app.get("/mocks/{path:path}", tags=["Mocks"])
async def mocks_alias(path: str = ""):
    """Mocks alias — canonical mocks live under /api/*, this provides /mocks/* per Phase 4 criteria."""
    return {
        "service": "mocks alias",
        "path": f"/mocks/{path}" if path else "/mocks/",
        "canonical_prefix": "/api",
        "available": [
            "/api/citos/ppt/containers",
            "/api/citos/tuas/loading-sequence",
            "/api/optetruck/capacity",
            "/api/feeder/{feeder_id}",
            "/api/portnet/feeder/{feeder_id}",
        ],
    }


# ---------------------------------------------------------------------------
# Health & root
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "psa-nexus"}


app.mount("/ui", StaticFiles(directory="app/ui", html=True), name="ui")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/ui/", status_code=307)
