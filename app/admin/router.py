"""Admin API router — config management + API key injection.

GET  /api/admin/config          — read-only global LLM + active problem summary (auth required)
POST /api/admin/config          — write provider/model/base_url to llm.yaml, confidence to problem YAML (auth required)
GET  /api/admin/config/problem  — read active problem's cost_params, constraints, escalation_triggers, confidence (auth required)
POST /api/admin/config/problem  — write active problem's cost_params, constraints, escalation_triggers, confidence (auth required)
POST /api/admin/api-key         — inject API key into .env + os.environ (auth required, write-only)
POST /api/admin/login           — authenticate, get session cookie
GET  /api/admin/config/status   — API key status (no auth — for startup check)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.admin.auth import (
    check_auth,
    create_session_cookie,
    verify_credentials,
)
from app.configs.problem_config import LLM_CONFIG_PATH, CONFIG_DIR

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.post("/login")
async def admin_login(payload: dict):
    """Authenticate admin. Returns session cookie."""
    username = payload.get("username", "")
    password = payload.get("password", "")
    if not verify_credentials(username, password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_session_cookie(username)
    response = JSONResponse({"status": "ok", "user": username, "expires_in": 3600})
    response.set_cookie(
        "psa_admin_session",
        token,
        httponly=True,
        samesite="lax",
        max_age=3600,
    )
    return response


# ---------------------------------------------------------------------------
# Read config
# ---------------------------------------------------------------------------

@router.get("/config")
async def get_config(request: Request):
    """Read-only view of global LLM config + active problem settings."""
    check_auth(request)

    # Global LLM config
    llm_data: dict[str, Any] = {}
    if LLM_CONFIG_PATH.exists():
        with open(LLM_CONFIG_PATH) as f:
            llm_data = yaml.safe_load(f) or {}

    # Active problem config
    from app.agent.problem_switcher import get_active_problem_id
    from app.configs.problem_config import load_problem_config
    active_id = get_active_problem_id()
    cfg = load_problem_config(active_id)

    # API key status (never expose values)
    api_key_status = {}
    for key_name in [
        llm_data.get("api_key_env", ""),
        llm_data.get("fallback_api_key_env", ""),
    ]:
        if key_name:
            api_key_status[key_name] = "set" if os.environ.get(key_name) else "not set"

    return {
        "llm": {
            "provider": llm_data.get("provider", ""),
            "model": llm_data.get("model", ""),
            "base_url": llm_data.get("base_url", ""),
            "api_key_env": llm_data.get("api_key_env", ""),
            "fallback_provider": llm_data.get("fallback_provider", ""),
            "fallback_model": llm_data.get("fallback_model", ""),
            "fallback_api_key_env": llm_data.get("fallback_api_key_env", ""),
            "fallback_base_url": llm_data.get("fallback_base_url", ""),
        },
        "api_key_status": api_key_status,
        "active_problem": {
            "id": active_id,
            "confidence_threshold": cfg.confidence.threshold,
            "cost_params": cfg.cost_params,
        },
    }


# ---------------------------------------------------------------------------
# Write config
# ---------------------------------------------------------------------------

@router.post("/config")
async def update_config(payload: dict, request: Request):
    """Update provider settings in llm.yaml + confidence threshold in problem YAML."""
    check_auth(request)

    updates = payload.get("llm", {})
    confidence_update = payload.get("confidence_threshold")

    # Update llm.yaml
    if updates:
        llm_data: dict[str, Any] = {}
        if LLM_CONFIG_PATH.exists():
            with open(LLM_CONFIG_PATH) as f:
                llm_data = yaml.safe_load(f) or {}

        # Allowed fields
        allowed = {"provider", "model", "base_url", "api_key_env",
                    "fallback_provider", "fallback_model", "fallback_api_key_env", "fallback_base_url"}
        for k, v in updates.items():
            if k in allowed:
                llm_data[k] = v

        with open(LLM_CONFIG_PATH, "w") as f:
            yaml.dump(llm_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Update confidence threshold in active problem YAML
    if confidence_update is not None:
        from app.agent.problem_switcher import get_active_problem_id
        active_id = get_active_problem_id()
        yaml_path = CONFIG_DIR / f"{active_id}.yaml"
        if not yaml_path.exists():
            # Try glob match
            for p in CONFIG_DIR.glob("pb-*.yaml"):
                if p.stem.lower() == active_id.lower():
                    yaml_path = p
                    break

        if yaml_path.exists():
            with open(yaml_path) as f:
                prob_data = yaml.safe_load(f) or {}
            prob_data.setdefault("confidence", {})["threshold"] = float(confidence_update)
            with open(yaml_path, "w") as f:
                yaml.dump(prob_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return {"status": "ok", "message": "Config updated. Provider changes take effect on next agent run."}


# ---------------------------------------------------------------------------
# API key injection (write-only)
# ---------------------------------------------------------------------------

@router.post("/api-key")
async def inject_api_key(payload: dict, request: Request):
    """Inject API key into .env file + os.environ. Never echoes the key back."""
    check_auth(request)

    provider = payload.get("provider", "")
    key = payload.get("key", "")
    key_env = payload.get("key_env", "")

    if not key:
        raise HTTPException(status_code=422, detail="key is required")
    if not provider and not key_env:
        raise HTTPException(status_code=422, detail="provider or key_env is required")

    # Resolve env var name
    if not key_env:
        _PROVIDER_KEY_MAP = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "custom": "CUSTOM_API_KEY",
        }
        key_env = _PROVIDER_KEY_MAP.get(provider, "")
        if not key_env:
            raise HTTPException(status_code=422, detail=f"Unknown provider '{provider}'. Use key_env explicitly.")

    # 1. Set in os.environ (immediate effect)
    os.environ[key_env] = key

    # 2. Write to .env file (persists across restarts)
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    _update_env_file(env_path, key_env, key)

    # 3. Return status only — never the key
    return {"status": "ok", "key_env": key_env, "provider": provider, "message": "API key set. Takes effect immediately."}


def _update_env_file(env_path: Path, key: str, value: str) -> None:
    """Update or append a key in .env file."""
    lines: list[str] = []
    found = False
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"{key}={value}\n")
    with open(env_path, "w") as f:
        f.writelines(lines)


# ---------------------------------------------------------------------------
# API key status (no auth — lightweight check)
# ---------------------------------------------------------------------------

@router.get("/config/status")
async def config_status():
    """Quick API key status check (no auth required)."""
    from app.configs.problem_config import _load_global_llm_config
    llm = _load_global_llm_config()
    status = {}
    for field in ("api_key_env", "fallback_api_key_env"):
        env_name = llm.get(field, "")
        if env_name:
            status[env_name] = "set" if os.environ.get(env_name) else "not set"
    return {"status": "ok", "api_key_status": status}


# ---------------------------------------------------------------------------
# Per-problem config (cost_params, constraints, escalation_triggers, confidence)
# ---------------------------------------------------------------------------

def _find_problem_yaml(problem_id: str) -> Path | None:
    """Locate YAML for a problem_id (same logic as problem_config._find_yaml)."""
    pid = problem_id.lower().strip()
    candidate = CONFIG_DIR / f"{pid}.yaml"
    if candidate.exists():
        return candidate
    for p in CONFIG_DIR.glob("pb-*.yaml"):
        stem = p.stem.lower()
        if stem == pid:
            return p
        parts_pid = pid.split("-")
        parts_stem = stem.split("-")
        if len(parts_pid) >= 2 and len(parts_stem) >= 2 and parts_pid[0] == parts_stem[0] and parts_pid[1] == parts_stem[1]:
            return p
    return None


@router.get("/config/problem")
async def get_problem_config(request: Request):
    """Read active problem's editable config fields."""
    check_auth(request)

    from app.agent.problem_switcher import get_active_problem_id
    from app.configs.problem_config import load_problem_config

    active_id = get_active_problem_id()
    cfg = load_problem_config(active_id)

    # Read raw YAML for fields that ProblemConfig dataclass may not fully expose
    yaml_path = _find_problem_yaml(active_id)
    raw: dict[str, Any] = {}
    if yaml_path:
        with open(yaml_path) as f:
            raw = yaml.safe_load(f) or {}

    return {
        "problem_id": active_id,
        "confidence": raw.get("confidence", {}),
        "cost_params": raw.get("cost_params", {}),
        "constraints": raw.get("constraints", {}),
        "escalation_triggers": raw.get("escalation_triggers", []),
        "edge_cases": raw.get("edge_cases", []),
    }


@router.post("/config/problem")
async def update_problem_config(payload: dict, request: Request):
    """Write active problem's config fields back to YAML.

    Accepts any subset of: confidence, cost_params, constraints, escalation_triggers, edge_cases.
    Only provided fields are updated; omitted fields are preserved.
    """
    check_auth(request)

    from app.agent.problem_switcher import get_active_problem_id

    active_id = get_active_problem_id()
    yaml_path = _find_problem_yaml(active_id)
    if not yaml_path or not yaml_path.exists():
        raise HTTPException(status_code=404, detail=f"No YAML config found for problem '{active_id}'")

    with open(yaml_path) as f:
        prob_data = yaml.safe_load(f) or {}

    # Allowed top-level fields for per-problem editing
    allowed = {"confidence", "cost_params", "constraints", "escalation_triggers", "edge_cases"}
    updated_fields = []
    for key in allowed:
        if key in payload:
            prob_data[key] = payload[key]
            updated_fields.append(key)

    if not updated_fields:
        raise HTTPException(status_code=422, detail=f"No valid fields provided. Allowed: {sorted(allowed)}")

    with open(yaml_path, "w") as f:
        yaml.dump(prob_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return {"status": "ok", "problem_id": active_id, "updated": updated_fields}
