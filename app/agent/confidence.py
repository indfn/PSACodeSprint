"""Confidence scoring — LLM self-assessment + deterministic fallback (Phase 6.7)."""
from __future__ import annotations

import json
import re
from typing import Any


def extract_confidence(text: str | None) -> float | None:
    """Parse confidence float from LLM text (expects JSON with confidence field)."""
    if not text:
        return None
    # Try to find JSON with confidence
    try:
        # Look for { ... "confidence": 0.92 ... }
        m = re.search(r'"confidence"\s*:\s*([0-9]*\.?[0-9]+)', text)
        if m:
            v = float(m.group(1))
            if 0.0 <= v <= 1.0:
                return v
            if 0.0 <= v <= 100.0 and v > 1.0:
                # LLM sometimes returns percent
                return v / 100.0
        # Try direct JSON
        data = json.loads(text)
        if isinstance(data, dict) and "confidence" in data:
            v = float(data["confidence"])
            return max(0.0, min(1.0, v))
    except Exception:
        pass
    return None


def deterministic_score(state: dict[str, Any]) -> float:
    """Compute deterministic confidence from state quality metrics."""
    # Start high, penalise for issues
    score = 1.0
    context = state.get("context", {}) or {}

    # Penalise if any guardrail failed (from optimiser metadata)
    tool_results = state.get("tool_results", {}) or {}
    for res in tool_results.values():
        meta = {}
        if isinstance(res, dict):
            meta = res.get("metadata", {}) or {}
        else:
            meta = getattr(res, "metadata", {}) or {}
        if meta.get("error") or meta.get("guardrail_failed"):
            score -= 0.2
        if meta.get("fallback_used"):
            score -= 0.15

    # Data age penalty — if any tool result is stale >30m
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        for res in tool_results.values():
            ts = None
            if isinstance(res, dict):
                ts = (res.get("metadata") or {}).get("timestamp") or res.get("timestamp")
            else:
                ts = (getattr(res, "metadata", {}) or {}).get("timestamp")
            # also check output data_age_minutes
            out = {}
            if isinstance(res, dict):
                out = res.get("output", {}) or {}
            else:
                out = getattr(res, "output", {}) or {}
            age = out.get("data_age_minutes")
            if isinstance(age, (int, float)) and age > 30:
                score -= 0.2
            if ts:
                try:
                    # try to parse timestamp — if older than 30m, penalise
                    dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                    age_min = (now - dt).total_seconds() / 60
                    if age_min > 30:
                        score -= 0.1
                except Exception:
                    pass
    except Exception:
        pass

    # Deviation history penalty
    if state.get("deviation_log"):
        score -= 0.15 * len(state["deviation_log"])

    # Escalation penalty
    if state.get("escalation"):
        score -= 0.15

    # Clamp
    return max(0.0, min(1.0, round(score, 3)))


async def compute_confidence(state: dict[str, Any], provider: Any | None = None) -> float:
    """Primary: LLM self-assessment via provider.chat; fallback: deterministic."""
    # If state already has a confidence from LLM tool call result, prefer it?
    # Instead, ask LLM if provider available
    det = deterministic_score(state)

    if provider is None:
        # Try to get provider from config
        try:
            from app.shared.provider import create_provider
            from app.configs.problem_config import load_problem_config
            from app.agent.problem_switcher import get_active_problem_id
            cfg = load_problem_config(get_active_problem_id())
            if cfg.llm:
                provider = create_provider(cfg.llm)
        except Exception:
            provider = None

    if provider is None:
        return det

    # Build minimal prompt — keep cheap
    prompt = (
        "Rate your confidence in the current ITT coordination plan from 0.0 to 1.0. "
        "Consider data freshness, constraint satisfaction, and margin before vessel departure. "
        'Respond ONLY as JSON {"confidence": float}. '
        f"Context: {json.dumps(state.get('context', {}), default=str)[:2000]}"
    )
    try:
        # provider.chat is synchronous in current implementation — run directly
        resp = provider.chat([{"role": "user", "content": prompt}], max_tokens=50)
        conf = extract_confidence(getattr(resp, "content", None))
        if conf is not None:
            return max(0.0, min(1.0, float(conf)))
    except Exception:
        pass
    return det


def compute_risk_score(state: dict[str, Any]) -> float:
    """CodeSprint Phase 4.3 requires risk_score in every TraceEntry.

    risk_score = 1 - confidence, boosted by escalation count (+0.15 per active trigger)
    and deviation_log (+0.1). This ensures risk badges show meaningful spread during
    problematic scenarios (e.g., 78% confidence + escalation → Medium/High risk).
    """
    base = 1.0 - float(state.get("confidence", 1.0))
    esc = state.get("escalation")
    count = 0
    if isinstance(esc, list):
        count = len(esc)
    elif isinstance(esc, dict) and esc:
        count = 1
    elif esc:
        count = 1
    boosted = base + count * 0.15
    if state.get("deviation_log"):
        boosted += 0.1
    return min(1.0, max(0.0, round(boosted, 3)))
