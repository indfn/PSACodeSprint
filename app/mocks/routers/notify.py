from datetime import datetime, timezone

from fastapi import APIRouter

from app.mocks.data import notification_log

router = APIRouter(prefix="/api", tags=["Notify"])


@router.post("/notify")
async def post_notify(body: dict):
    message = body.get("message", "")
    parties = body.get("parties", [])
    run_id = body.get("run_id", "")
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {"message": message, "parties": list(parties), "timestamp": timestamp, "run_id": run_id}
    notification_log.append(entry)
    try:
        broadcaster = None
        try:
            from app.agent.sse import broadcaster as _bc

            broadcaster = _bc
        except ImportError:
            try:
                from app.main import broadcaster as _bc2  # type: ignore

                broadcaster = _bc2
            except ImportError:
                broadcaster = None
        if broadcaster is not None and hasattr(broadcaster, "publish"):
            import asyncio

            payload = {"message": message, "parties": list(parties), "timestamp": timestamp, "run_id": run_id}
            result = broadcaster.publish(run_id, "notification", payload)
            if asyncio.iscoroutine(result):
                await result
    except Exception:
        pass
    return {"status": "sent", "notified": list(parties), "message": message, "timestamp": timestamp, "run_id": run_id}


@router.get("/notify")
async def get_notify():
    return {"notifications": list(notification_log), "count": len(notification_log)}


@router.delete("/notify")
async def clear_notify():
    notification_log.clear()
    return {"status": "cleared", "count": 0}
