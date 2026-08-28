"""Structured JSON logging — charter G-23 (Phase 6.8).

Each line is a JSON object with timestamp, run_id, step, event_type, payload.
Goes to stdout (for Railway/Render log drain) and optionally to a file.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def structured_log(
    event_type: str,
    run_id: str = "",
    step: str = "",
    **payload: Any,
) -> dict[str, Any]:
    """Emit a structured log line.

    Args:
        event_type: Logical event name (e.g. trace, guardrail_failed, hitl_card).
        run_id: Correlation id for the current run.
        step: Logical step / node name.
        **payload: Arbitrary payload fields.

    Returns:
        The entry dict that was emitted.
    """
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "step": step,
        "event_type": event_type,
        "payload": payload,
    }
    try:
        # Use ensure_ascii=True to avoid Windows cp1252 encoding issues with '→' etc.
        # Also handle broken pipe / encoding errors gracefully.
        line = json.dumps(entry, default=str, ensure_ascii=True)
        # Write bytes to stdout buffer if possible to avoid charmap errors
        try:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
        except UnicodeEncodeError:
            # Fallback: write escaped
            sys.stdout.write(line.encode("ascii", "backslashreplace").decode("ascii") + "\n")
            sys.stdout.flush()
        except Exception:
            # Last resort: use print with errors
            print(line, flush=True, file=sys.stdout)
    except Exception:
        pass

    # Optionally append to file if LOG_FILE env var is set
    import os
    log_file = os.environ.get("LOG_FILE", "")
    if log_file:
        try:
            p = Path(log_file)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception:
            pass

    return entry
