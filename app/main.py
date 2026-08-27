"""PSA Nexus — Unified FastAPI app (Phase 4).

Mounts: health, mocks, webhook (agent entry point), agent switch-problem.
Canonical schema import: from app.shared.models import ITTCoordinationEvent
"""

import uuid
from collections import OrderedDict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(
    title="PSA Nexus — Agentic Multi-Party Coordination Platform",
    description="Unified platform for Cluster C2 (7 problems) — flagship PB-12 ITT Coordination",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# ---------------------------------------------------------------------------
# Webhook — agent entry point (charter T6), NOT a mock system
# ---------------------------------------------------------------------------

MAX_RUNS = 100
runs: OrderedDict[str, dict] = OrderedDict()


@app.post("/webhook/itt-coordination", response_model=WebhookResponse, tags=["Webhook"])
async def receive_webhook(event: ITTCoordinationEvent):
    """Webhook endpoint for ITT_COORDINATION_REQUEST events (T6 trigger).

    Validates ITTCoordinationEvent (15 fields), bootstraps charter 11-field
    initial_state, and triggers the agent (Phase 6.9 wires run_agent()).
    For now: validates + stores run, returns accepted.
    """
    if event.containers_ready > event.container_count:
        raise HTTPException(
            status_code=400,
            detail=f"containers_ready ({event.containers_ready}) cannot exceed container_count ({event.container_count})",
        )

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    # Charter 11-field initial_state (scaffold — full wiring in Phase 6.9)
    initial_state = {
        "run_id": run_id,
        "event": event.model_dump(),
        "origin_terminal": event.origin_terminal,
        "destination_terminal": event.destination_terminal,
        "vessel_id": event.vessel_id,
        "container_count": event.container_count,
        "tuas_vessel_departure": event.tuas_vessel_departure,
        "blocks_affected": event.blocks_affected,
        "dg_containers": event.dg_containers,
        "priority_containers": event.priority_containers,
        "requested_by": event.requested_by,
        "current_step": "ingest",
        "hitl_pending": [],
        "escalations": [],
        "confidence_scores": [],
        "deviation_log": [],
    }
    runs[run_id] = {
        "run_id": run_id,
        "event": event.model_dump(),
        "status": "accepted",
        "current_step": "ingest",
        "origin_terminal": event.origin_terminal,
        "destination_terminal": event.destination_terminal,
        "vessel_id": event.vessel_id,
        "container_count": event.container_count,
        "tuas_vessel_departure": event.tuas_vessel_departure,
        "blocks_affected": event.blocks_affected,
        "dg_containers": event.dg_containers,
        "hitl_pending": [],
        "escalations": [],
        "confidence_scores": [],
        "deviation_log": [],
        "initial_state": initial_state,
    }
    if len(runs) > MAX_RUNS:
        runs.popitem(last=False)

    # Phase 6.9 will call: await run_agent(initial_state)
    return WebhookResponse(status="accepted", run_id=run_id)


@app.get("/webhook/runs", tags=["Webhook"])
async def list_runs():
    """List all webhook runs (for verification)."""
    return {"runs": list(runs.values()), "count": len(runs)}


@app.get("/webhook/runs/{run_id}", tags=["Webhook"])
async def get_run_status(run_id: str):
    """Get status of a specific run."""
    if run_id not in runs:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return runs[run_id]


# ---------------------------------------------------------------------------
# Problem switching — PSA Nexus platform core (4.8)
# Consumer of app/tools/registry.py owned by Phase 5.1 — imported lazily
# Single source of truth is app.agent.problem_switcher._active_problem_id;
# this module re-exports it for backwards compatibility with Phase 6.9's
# `from app.main import _active_problem_id` import.
# ---------------------------------------------------------------------------

# Re-export for compatibility — do NOT maintain a separate copy (fixes drift bug
# where app/main.py and app/agent/problem_switcher.py held divergent state).
import app.agent.problem_switcher as _ps  # noqa: E402

_active_problem_id: str = _ps._active_problem_id  # type: ignore[attr-defined]  # re-export, not authoritative


def _sync_active_problem_id() -> str:
    """Sync local alias from authoritative store and return it."""
    global _active_problem_id
    _active_problem_id = _ps.get_active_problem_id()
    return _active_problem_id


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

    active = _sync_active_problem_id()

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
# UI placeholder (Phase 7) and Mocks alias (for success criteria /mocks/*)
# ---------------------------------------------------------------------------

@app.get("/ui/", tags=["UI"])
@app.get("/ui/{path:path}", tags=["UI"])
async def ui_placeholder(path: str = ""):
    """UI placeholder — Phase 7 will replace with full dashboard."""
    return {
        "service": "PSA Nexus UI",
        "path": f"/ui/{path}" if path else "/ui/",
        "status": "placeholder - Phase 7",
        "note": "Dashboard will be implemented in Phase 7 (Nexus Dashboard).",
    }


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


@app.get("/")
async def root():
    return {
        "service": "PSA Nexus — Agentic Multi-Party Coordination Platform",
        "version": "0.1.0",
        "health": "/health",
        "docs": "/docs",
    }
