"""PB-01 Berth Delay mock data — supports scenario-based randomization."""

from __future__ import annotations

from datetime import datetime, timezone

notification_log: list[dict] = []


def _get_scenario_rng():
    """Get active scenario RNG, or None."""
    try:
        from app.mocks.scenarios import _active_scenario_id, _rng, PB01_SCENARIOS
        if _active_scenario_id in PB01_SCENARIOS:
            return _active_scenario_id, _rng, PB01_SCENARIOS[_active_scenario_id]
    except ImportError:
        pass
    return None, None, None


VESSEL_NAMES = [
    "MV EVER GIVEN", "MV MAERSK ALABAMA", "MV COSCO SHIPPING UNIVERSE",
    "MV MSC GULSUN", "MV CMA CGM JACQUES SAADE", "MV ONE AQUILA",
    "MV HAPAG-LLOYD BERLIN", "MV YANG MING INTEGRITY",
]


def get_vessel_data(vessel_id: str = "MV EVER GIVEN") -> dict:
    """VTIS vessel arrival data — randomized when scenario active."""
    scenario_id, rng, sc = _get_scenario_rng()

    if rng is not None and sc is not None:
        delay = sc.vessel_delay_hours.sample(rng)
        draft = sc.vessel_draft_m.sample(rng)
        status = "delayed" if delay > 2 else "approaching"
    else:
        delay = 0
        draft = 14.5
        status = "approaching"

    return {
        "vessel_id": vessel_id,
        "eta": "2026-08-19T18:00:00+08:00",
        "pilot_available": True,
        "tug_available": True,
        "status": status,
        "delay_hours": round(delay, 1),
        "draft_m": round(draft, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_berth_data(vessel_id: str = "MV EVER GIVEN", berth_id: str = "B-03") -> dict:
    """OptEVoyage berth availability — randomized when scenario active."""
    scenario_id, rng, sc = _get_scenario_rng()

    if rng is not None and sc is not None:
        occupancy = sc.berth_occupancy.sample(rng)
        available_count = sc.berth_count_available.sample_int(rng)
        available = available_count > 0
    else:
        occupancy = 0.7
        available = True
        available_count = 2

    return {
        "vessel_id": vessel_id,
        "berth_id": berth_id,
        "available": available,
        "available_count": available_count,
        "window": {
            "earliest": "2026-08-19T18:00:00+08:00",
            "latest": "2026-08-19T22:00:00+08:00",
        },
        "draft_limit": 16.0,
        "tidal_window": "2026-08-19T23:00:00+08:00",
        "occupancy": round(occupancy, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_qc_data(berth_id: str = "B-03") -> dict:
    """Berth QC availability — randomized when scenario active."""
    try:
        from app.agent.problem_switcher import get_active_problem_id
        pid = get_active_problem_id()
        if pid == "pb-12-itt":
            try:
                from app.mocks.data import get_loading_sequence_data
                from app.mocks.scenarios import _active_scenario_id, PB12_SCENARIOS, _rng
                seq = get_loading_sequence_data()
                qcs = seq.get("qc_adjustments", []) or seq.get("qc_assignments", [])
                # Dynamic QC count from loading sequence (scaled by container volume)
                total = len(qcs) if qcs else 4
                qc_status = []
                for idx, q in enumerate(qcs[:total]):
                    qc_id = q.get("qc_id", f"QC-{idx+7:02d}")
                    qc_status.append({"qc_id": qc_id, "status": "available"})
                # pad to total if needed
                while len(qc_status) < total:
                    qc_status.append({"qc_id": f"QC-{len(qc_status)+7:02d}", "status": "available"})
                return {"berth_id": berth_id, "qc_count": total, "qc_status": qc_status, "crane_status": {q["qc_id"]: q["status"] for q in qc_status}, "timestamp": datetime.now(timezone.utc).isoformat()}
            except Exception:
                pass
    except Exception:
        pass
    scenario_id, rng, sc = _get_scenario_rng()

    if rng is not None and sc is not None:
        qc_available = sc.qc_available.sample_int(rng)
    else:
        qc_available = 26

    total = 40
    qc_status = []
    for i in range(1, total + 1):
        qc_id = f"QC-{i:02d}"
        if i <= qc_available:
            qc_status.append({"qc_id": qc_id, "status": "available"})
        else:
            qc_status.append({"qc_id": qc_id, "status": "maintenance"})

    return {
        "berth_id": berth_id,
        "qc_count": total,
        "qc_status": qc_status,
        "crane_status": {q["qc_id"]: q["status"] for q in qc_status},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def compute_berth_reassignment_data(vessel_id: str = "MV EVER GIVEN", constraints: dict | None = None) -> dict:
    """Compute berth reassignment — uses scenario data when active."""
    scenario_id, rng, sc = _get_scenario_rng()

    if rng is not None and sc is not None:
        berths_available = sc.berth_count_available.sample_int(rng)
        assigned_berth = "B-07" if berths_available >= 2 else "B-03"
        cost = 2400 + (500 if berths_available < 2 else 0)
    else:
        assigned_berth = "B-07"
        cost = 2400

    return {
        "vessel_id": vessel_id,
        "original_berth": "B-03",
        "new_berth": assigned_berth,
        "qc_allocation": ["QC-07", "QC-08"],
        "estimated_cost": cost,
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
