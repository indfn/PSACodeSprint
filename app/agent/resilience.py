"""Resilience — rate limit, stale resume, concurrency, webhook validation (Phase 6.12)."""
from __future__ import annotations

import asyncio
from typing import Any


class RateLimitError(Exception):
    pass


async def chat_with_rate_limit(
    provider: Any,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    retries: int = 2,
) -> Any:
    """Wrap provider.chat with retry on 429 + fallback provider.

    - On RateLimitError / 429, retries with exponential backoff (1s, 2s).
    - After retries exhausted, tries fallback provider from ProblemConfig.llm.fallback_provider.
    """
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            # provider.chat may be sync — run it appropriately
            try:
                loop = asyncio.get_running_loop()
                # If we're in async loop, run sync provider.chat in executor
                import inspect
                if inspect.iscoroutinefunction(getattr(provider, "chat", None)):
                    return await provider.chat(messages, tools=tools)
                else:
                    return await loop.run_in_executor(None, lambda: provider.chat(messages, tools=tools))
            except RuntimeError:
                # No loop — direct call
                import inspect
                if inspect.iscoroutinefunction(getattr(provider, "chat", None)):
                    return await provider.chat(messages, tools=tools)  # type: ignore
                else:
                    return provider.chat(messages, tools=tools)  # type: ignore
        except Exception as exc:
            last_exc = exc
            msg = str(exc).lower()
            is_rate_limit = "429" in str(exc) or "rate limit" in msg or "too many requests" in msg or isinstance(exc, RateLimitError)
            if is_rate_limit and attempt < retries:
                wait = 2 ** attempt  # 1, 2, 4
                try:
                    await asyncio.sleep(wait)
                except Exception:
                    import time
                    time.sleep(wait)
                continue
            if is_rate_limit:
                # Try fallback provider
                fallback = _try_fallback_provider()
                if fallback is not None:
                    try:
                        # Structured log fallback
                        try:
                            from app.shared.logging import structured_log
                            structured_log("llm_rate_limit_fallback", step="agent", provider=getattr(provider, "name", "unknown"), fallback=getattr(fallback, "name", "fallback"))
                        except Exception:
                            pass
                        if hasattr(fallback, "chat"):
                            import inspect
                            if inspect.iscoroutinefunction(fallback.chat):
                                return await fallback.chat(messages, tools=tools)
                            else:
                                try:
                                    loop = asyncio.get_running_loop()
                                    return await loop.run_in_executor(None, lambda: fallback.chat(messages, tools=tools))
                                except RuntimeError:
                                    return fallback.chat(messages, tools=tools)
                    except Exception as fb_exc:
                        last_exc = fb_exc
                        break
            # Not rate limit or fallback failed
            break
    if last_exc:
        raise last_exc
    # Should not reach here
    raise RuntimeError("chat_with_rate_limit: no provider response")


def _try_fallback_provider() -> Any | None:
    try:
        from app.configs.problem_config import load_problem_config
        from app.agent.problem_switcher import get_active_problem_id
        from app.shared.provider import create_provider
        cfg = load_problem_config(get_active_problem_id())
        llm = cfg.llm or {}
        fb_name = llm.get("fallback_provider")
        if not fb_name:
            return None
        fb_config = {
            "provider": fb_name,
            "model": llm.get("fallback_model", ""),
            "api_key_env": llm.get("fallback_api_key_env", ""),
            "api_key": llm.get("fallback_api_key", ""),
            "base_url": llm.get("fallback_base_url", ""),
        }
        return create_provider(fb_config)
    except Exception:
        return None


def _norm_gate(g: str | None) -> str:
    return str(g).lower().replace("-", "_") if g else ""


def is_hitl_stale(state: dict[str, Any], gate_id: str | None = None) -> bool:
    """Check if HITL resume is stale (already timed out -> terminal).

    Normalizes gate_id (HITL-1 == hitl_1) and adds TTL check per gate timeout.
    """
    status = state.get("status", "")
    hitl_pending = state.get("hitl_pending")
    pending_id_raw = None
    if isinstance(hitl_pending, dict):
        pending_id_raw = hitl_pending.get("gate_id")
    elif hitl_pending and hasattr(hitl_pending, "gate_id"):
        pending_id_raw = hitl_pending.gate_id  # type: ignore
    pid = _norm_gate(pending_id_raw)
    gid = _norm_gate(gate_id)

    # If no pending HITL and status is terminal, any resume is stale
    if hitl_pending is None and status in ("halted", "cancelled", "holding", "completed", "failed"):
        return True

    # If status terminal, check gate affinity
    if status in ("halted", "cancelled", "holding") and gid:
        # If pending is a different gate (e.g., HITL-5 now pending), then stale check for old HITL-1 should NOT block
        if pid and pid != gid:
            return False
        if pid is None:
            return True
        # Same gate but TTL expired?
        entered = state.get("hitl_gate_entered_at")
        if entered:
            try:
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(str(entered).replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - dt).total_seconds()
                gate_timeout = 1800
                if isinstance(hitl_pending, dict):
                    gate_timeout = int(hitl_pending.get("timeout_seconds", 1800))
                if age > gate_timeout:
                    return True
            except Exception:
                pass

    # Also TTL check even when not strictly terminal but gate timed out
    # (timeout handler should have set terminal, but stale detection is the only guard)
    entered = state.get("hitl_gate_entered_at")
    if entered and pid and gid and pid == gid:
        try:
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(str(entered).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - dt).total_seconds()
            gate_timeout = 1800
            if isinstance(hitl_pending, dict):
                gate_timeout = int(hitl_pending.get("timeout_seconds", 1800))
            if age > gate_timeout:
                return True
        except Exception:
            pass

    return False


def validate_webhook_event(data: dict[str, Any]) -> tuple[bool, str]:
    """Validate ITT event shape — for resilience tests expecting 422 not 500."""
    # Minimal validation: container_count >=50, tuas_vessel_departure future, etc.
    # Real validation is done by Pydantic ITTCoordinationEvent; this is a helper for manual checks.
    if not isinstance(data, dict):
        return False, "event must be a dict"
    if "container_count" in data and isinstance(data["container_count"], int) and data["container_count"] < 50:
        return False, "container_count must be >=50"
    if "vessel_id" not in data or not data.get("vessel_id"):
        return False, "vessel_id required"
    if "tuas_vessel_departure" not in data or not data.get("tuas_vessel_departure"):
        return False, "tuas_vessel_departure required"
    # Future check per A-21
    v = data.get("tuas_vessel_departure")
    if v:
        try:
            from datetime import datetime, timedelta, timezone
            dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt <= datetime.now(timezone.utc) + timedelta(minutes=30):
                return False, "tuas_vessel_departure must be > now + 30min"
        except Exception:
            return False, "invalid tuas_vessel_departure"
    # containers_ready vs container_count (422)
    if "containers_ready" in data and "container_count" in data:
        try:
            if int(data["containers_ready"]) > int(data["container_count"]):
                return False, "containers_ready cannot exceed container_count"
        except Exception:
            pass
    return True, ""
