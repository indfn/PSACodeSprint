from __future__ import annotations

import asyncio
import warnings
from datetime import datetime, timezone

from app.tools.base import BaseTool, ToolResult

KNOWN_STAKEHOLDERS: set[str] = {
    "PPT_Yard",
    "Tuas_Yard",
    "Feeder_Operator",
    "OptETruck",
    "PORTNET",
    "CITOS_PPT",
    "CITOS_Tuas",
    "Yard_Planner",
    "Duty_Manager",
    "Shipping_Line",
    "Harbour_Pilot",
    "Gate_Operator",
    "citos_ppt",
    "citos_tuas",
    "optetruck",
    "feeder",
    "portnet",
    "PPT",
    "TUAS",
}


def get_notifications() -> list[dict]:
    try:
        from app.mocks.data import notification_log
        return list(notification_log)
    except ImportError:
        return []


_broadcaster_cache = None


def _get_broadcaster():
    global _broadcaster_cache
    if _broadcaster_cache is not None:
        return _broadcaster_cache
    try:
        from app.agent.sse import broadcaster as _bc

        _broadcaster_cache = _bc
        return _broadcaster_cache
    except ImportError:
        pass
    try:
        from app.main import broadcaster as _bc2  # type: ignore

        _broadcaster_cache = _bc2
        return _broadcaster_cache
    except ImportError:
        pass
    return None


class NotifyPartiesTool(BaseTool):
    name = "notify_parties"
    description = "Send alerts to affected stakeholders (PPT yard, Tuas yard, feeder operator, etc.)"
    parameters_schema = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Notification message"},
            "parties": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Stakeholder parties e.g. PPT_Yard, Tuas_Yard, Feeder_Operator",
            },
        },
        "required": ["message", "parties"],
    }
    timeout_seconds = 10

    async def execute(self, message: str, parties: list[str], **kwargs) -> ToolResult:
        unknown = [p for p in parties if p not in KNOWN_STAKEHOLDERS]
        if unknown:
            warnings.warn(f"Unknown stakeholders: {unknown}. Known: {sorted(KNOWN_STAKEHOLDERS)}", UserWarning)

        now_iso = datetime.now(timezone.utc).isoformat()
        run_id = kwargs.get("run_id") or kwargs.get("_run_id") or ""

        entry: dict = {
            "message": message,
            "parties": list(parties),
            "timestamp": now_iso,
            "run_id": run_id,
        }

        try:
            import app.mocks.data as _data

            if not hasattr(_data, "notification_log"):
                _data.notification_log = []
            _data.notification_log.append(entry)
        except Exception:
            pass

        try:
            broadcaster = _get_broadcaster()
            if broadcaster is not None and hasattr(broadcaster, "publish"):
                payload = {"message": message, "parties": list(parties), "timestamp": now_iso, "run_id": run_id}
                result = broadcaster.publish(run_id, "notification", payload)
                if asyncio.iscoroutine(result):
                    await result
        except Exception as e:
            warnings.warn(f"SSE publish failed: {e}", UserWarning)

        trace_hint = {"event": "notification", "parties": list(parties), "message": message}
        output = {
            "notified": list(parties),
            "message": message,
            "timestamp": now_iso,
            "status": "sent",
            "trace_hint": trace_hint,
        }
        confidence = 0.7 if unknown else 1.0
        meta: dict = {"notification": trace_hint}
        if unknown:
            meta["unknown_parties"] = unknown
        return ToolResult(output=output, confidence=confidence, metadata=meta)

    async def call(self, **kwargs) -> ToolResult:
        run_id = kwargs.get("_run_id", "") or kwargs.get("run_id", "")
        result = await super().call(**kwargs)
        if run_id:
            try:
                import app.mocks.data as _data

                log = getattr(_data, "notification_log", [])
                if log:
                    last = log[-1]
                    if last.get("message") == result.output.get("message") and not last.get("run_id"):
                        last["run_id"] = run_id
            except Exception:
                pass
        return result
