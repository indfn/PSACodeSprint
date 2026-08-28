"""HITL timeout scheduler — background asyncio tasks per gate (Phase 6.5).

Each gate that enters hitl_pending gets a background task. After timeout_seconds,
the task auto-fires the configured timeout_action via handler. Manual decisions
cancel the pending task.

Usage:
    from app.hitl.timeout_scheduler import schedule_timeout, cancel_timeout, cancel_all_timeouts

    # In hitl_node, after interrupt() returns with decision=None (waiting):
    schedule_timeout(run_id, gate_id, timeout_seconds, state, gate)

    # On manual decision:
    cancel_timeout(run_id, gate_id)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger("psa-nexus.hitl.timeout")

# Pending timeout tasks: (run_id, gate_id) -> asyncio.Task
_pending: dict[tuple[str, str], asyncio.Task] = {}


def schedule_timeout(
    run_id: str,
    gate_id: str,
    timeout_seconds: int,
    state: dict[str, Any],
    gate: dict[str, Any],
) -> None:
    """Schedule a background task that fires timeout_action after timeout_seconds.

    Args:
        run_id: Current run ID.
        gate_id: HITL gate identifier (e.g. "hitl_1").
        timeout_seconds: Seconds to wait before firing.
        state: Current AgentState dict (will be read, not mutated here).
        gate: HITL gate config dict (must have timeout_action).
    """
    key = (run_id, gate_id)

    # Cancel any existing task for this gate (idempotent)
    cancel_timeout(run_id, gate_id)

    if timeout_seconds <= 0:
        return

    async def _timeout_handler() -> None:
        try:
            await asyncio.sleep(timeout_seconds)

            # Check if state still has this gate pending (guards against race)
            if state.get("hitl_pending") is None:
                return
            current_gate = state.get("hitl_pending")
            current_gid = ""
            if isinstance(current_gate, dict):
                current_gid = current_gate.get("gate_id", "")
            elif hasattr(current_gate, "gate_id"):
                current_gid = current_gate.gate_id
            if current_gid and current_gid != gate_id:
                return

            logger.warning("HITL timeout fired: run=%s gate=%s after %ds", run_id, gate_id, timeout_seconds)

            # Build timeout decision
            decision = {"decision": "timeout", "reason": f"Auto-timeout after {timeout_seconds}s"}

            # Handle via handler
            try:
                from app.hitl.handler import handle_hitl_response
                await handle_hitl_response(state, gate, decision)
            except Exception as exc:
                logger.error("HITL timeout handler failed: %s", exc)
                state["status"] = "halted"
                state["hitl_pending"] = None

            # Publish SSE notification
            try:
                from app.agent.sse import broadcaster
                await broadcaster.publish(run_id, "hitl_timeout", {
                    "gate_id": gate_id,
                    "timeout_seconds": timeout_seconds,
                    "status": state.get("status", "halted"),
                })
            except Exception:
                pass

        except asyncio.CancelledError:
            # Task was cancelled (manual decision arrived) — normal path
            pass
        except Exception as exc:
            logger.error("HITL timeout task error: %s", exc)
        finally:
            _pending.pop(key, None)

    task = asyncio.create_task(_timeout_handler())
    _pending[key] = task
    logger.info("HITL timeout scheduled: run=%s gate=%s in %ds", run_id, gate_id, timeout_seconds)


def cancel_timeout(run_id: str, gate_id: str) -> bool:
    """Cancel a pending timeout task. Returns True if a task was cancelled."""
    key = (run_id, gate_id)
    task = _pending.pop(key, None)
    if task and not task.done():
        task.cancel()
        return True
    return False


def cancel_all_timeouts() -> int:
    """Cancel all pending timeout tasks. Returns count cancelled."""
    count = 0
    for key, task in list(_pending.items()):
        if not task.done():
            task.cancel()
            count += 1
    _pending.clear()
    return count


def pending_count() -> int:
    """Number of active pending timeout tasks."""
    return sum(1 for t in _pending.values() if not t.done())
