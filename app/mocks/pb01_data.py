from __future__ import annotations

from datetime import datetime, timezone

notification_log: list[dict] = []


def get_vessel_data(vessel_id: str = "MV EVER GIVEN") -> dict:
    return {
        "vessel_id": vessel_id,
        "eta": "2026-08-19T18:00:00+08:00",
        "pilot_available": True,
        "tug_available": True,
        "status": "approaching",
        "delay": 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_berth_data(vessel_id: str = "MV EVER GIVEN", berth_id: str = "B-03") -> dict:
    return {
        "vessel_id": vessel_id,
        "berth_id": berth_id,
        "available": True,
        "window": {
            "earliest": "2026-08-19T18:00:00+08:00",
            "latest": "2026-08-19T22:00:00+08:00",
        },
        "draft_limit": 16.0,
        "tidal_window": "2026-08-19T23:00:00+08:00",
        "occupancy": 0.7,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_qc_data(berth_id: str = "B-03") -> dict:
    qc_status = [
        {"qc_id": "QC-07", "status": "available"},
        {"qc_id": "QC-08", "status": "available"},
        {"qc_id": "QC-09", "status": "maintenance"},
    ]
    return {
        "berth_id": berth_id,
        "qc_count": 3,
        "qc_status": qc_status,
        "crane_status": {q["qc_id"]: q["status"] for q in qc_status},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def compute_berth_reassignment_data(vessel_id: str = "MV EVER GIVEN", constraints: dict | None = None) -> dict:
    return {
        "vessel_id": vessel_id,
        "original_berth": "B-03",
        "new_berth": "B-07",
        "qc_allocation": ["QC-07", "QC-08"],
        "estimated_cost": 2400,
        "timeline": {
            "reassignment_computed": datetime.now(timezone.utc).isoformat(),
            "original_eta": "2026-08-19T18:00:00+08:00",
            "new_berth_available_from": "2026-08-19T18:30:00+08:00",
            "estimated_berthing": "2026-08-19T19:00:00+08:00",
        },
        "constraints_applied": constraints or {},
        "status": "computed",
    }


def log_vessel_notification(vessel_id: str, message: str) -> dict:
    entry = {
        "vessel_id": vessel_id,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    notification_log.append(entry)
    try:
        import app.mocks.data as _data

        if hasattr(_data, "notification_log"):
            _data.notification_log.append({"vessel_id": vessel_id, "message": message, "timestamp": entry["timestamp"], "channel": "vtis"})
    except Exception:
        pass
    return entry
