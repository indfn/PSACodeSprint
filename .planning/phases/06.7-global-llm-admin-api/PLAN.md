# Phase 6.7: Global LLM Config + Admin API

## Goal
Centralise LLM provider config into a single `llm.yaml` (remove duplication from 7 problem YAMLs), build an admin API with auth for runtime config editing and API key injection, and prepare the backend for the admin UI in Phase 7.

## Depends on
Phase 6.5

## Requirements
F-03 (provider validation), F-08 (provider adapter), A-17 (confidence scoring)

## Success Criteria
1. All 7 problem YAMLs load without `llm:` section — fallback to `app/configs/llm.yaml`
2. `POST /api/admin/login` returns session cookie (admin/admin123)
3. `GET /api/admin/config` shows provider, model, base_url, api_key_env, fallback, confidence threshold, cost_params (auth required)
4. `POST /api/admin/config` writes to `llm.yaml` + problem YAML (auth required)
5. `POST /api/admin/api-key` writes to `.env` + `os.environ`, never echoes key back (auth required)
6. Session expires after 1 hour, HMAC-signed cookie
7. All existing tests pass (172+)

## Status
✅ COMPLETE (2026-08-28) — commit 0d794c3

### What was done

**6.7.1: Global llm.yaml** — `app/configs/llm.yaml`
- Single source of truth: provider, model, api_key_env, base_url, fallback_*
- All 7 problem YAMLs had identical `llm:` sections — removed from all

**6.7.2: Config Loader Fallback** — `app/configs/problem_config.py`
- Added `_load_global_llm_config()` — reads `llm.yaml`
- `load_problem_config()` merges global + per-problem override (opt-in)

**6.7.3: Admin Auth** — `app/admin/auth.py`
- Hardcoded demo credentials: admin / admin123
- HMAC-signed session cookie, 1-hour TTL
- Auth check via cookie or Authorization Bearer header

**6.7.4: Admin API Endpoints** — `app/admin/router.py`
- `POST /api/admin/login` — authenticate, get session cookie
- `GET /api/admin/config` — read-only config display (auth required)
- `POST /api/admin/config` — write provider/model/base_url to llm.yaml, confidence to problem YAML
- `POST /api/admin/api-key` — inject key into .env + os.environ (write-only, never echoed)
- `GET /api/admin/config/status` — quick key status check (no auth)

**6.7.5: Router Mount** — `app/main.py`
- `app.include_router(admin_router)` mounted at `/api/admin/*`
