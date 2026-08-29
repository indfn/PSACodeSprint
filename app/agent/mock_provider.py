"""Deterministic mock provider for demo/tests without real API keys (extracted from nodes.py).

Synthesises tool_calls based on current state progress, mimicking the
charter's 17-step workflow so the graph can complete without an LLM.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


class _MockProvider:
    """Deterministic mock provider for demo/tests without real API keys.

    It synthesises tool_calls based on current state progress, mimicking the
    charter's 17-step workflow so the graph can complete without an LLM.
    """

    def __init__(self, state: dict[str, Any]):
        self.state = state
        self.name = "mock"

    def chat(self, messages, tools=None, temperature=0.0, max_tokens=4096):
        # Delegate to deterministic planner
        from app.tools.registry import registry
        available = set(registry.list()) if registry.list() else {"get_itt_candidates", "check_road_itt_capacity", "check_sea_itt_capacity", "compute_itt_split", "dispatch_road_itt", "request_feeder_hold", "update_tuas_loading_sequence", "notify_parties"}
        ctx = self.state.get("context", {}) or {}
        tool_results = self.state.get("tool_results", {}) or {}
        hitl_history = self.state.get("hitl_history", []) or []

        # Determine which tools have already succeeded
        succeeded_tools = set()
        for rid, res in tool_results.items():
            meta = res.get("metadata", {}) if isinstance(res, dict) else getattr(res, "metadata", {})
            name = meta.get("tool_name") if isinstance(meta, dict) else ""
            if not name:
                # try to infer from output keys
                out = res.get("output", {}) if isinstance(res, dict) else {}
                if "total_containers" in out:
                    name = "get_itt_candidates"
                elif "available_trucks" in out:
                    name = "check_road_itt_capacity"
                elif "feeder_id" in out and "capacity_teu" in out:
                    name = "check_sea_itt_capacity"
            if name:
                # Only count if not error
                out = res.get("output", {}) if isinstance(res, dict) else {}
                if "error" not in out:
                    succeeded_tools.add(name)

        # Check hitl approvals
        approved = {h.get("gate_id") for h in hitl_history if isinstance(h, dict) and h.get("decision") == "approve"}

        # Build tool_calls deterministically following charter to-be workflow
        tool_calls = []

        # Phase: ingest -> T1/T2/T3 batch
        if "get_itt_candidates" not in succeeded_tools and "get_itt_candidates" in available:
            vessel = ctx.get("vessel_id", "MV PACIFIC STAR")
            tool_calls.append({"id": "call_T1", "type": "function", "function": {"name": "get_itt_candidates", "arguments": json.dumps({"vessel_id": vessel})}})
        if "check_road_itt_capacity" not in succeeded_tools and "check_road_itt_capacity" in available:
            # Only after T1? Actually charter has T1→T2→T3 parallel; we batch T2+T3 after T1
            if "get_itt_candidates" in succeeded_tools:
                tool_calls.append({"id": "call_T2", "type": "function", "function": {"name": "check_road_itt_capacity", "arguments": json.dumps({"terminal": "PPT", "time_window_start": "2026-08-19T11:00:00+08:00", "time_window_end": "2026-08-19T18:00:00+08:00"})}})
        if "check_sea_itt_capacity" not in succeeded_tools and "check_sea_itt_capacity" in available:
            if "get_itt_candidates" in succeeded_tools:
                tool_calls.append({"id": "call_T3", "type": "function", "function": {"name": "check_sea_itt_capacity", "arguments": json.dumps({"feeder_id": "FEEDER ATLANTIC-03", "current_time": "2026-08-19T10:35:00+08:00"})}})

        # After T2+T3 have succeeded, call T4
        if "compute_itt_split" not in succeeded_tools and "compute_itt_split" in available:
            if "check_road_itt_capacity" in succeeded_tools and "check_sea_itt_capacity" in succeeded_tools:
                # Build candidates/road/sea from context for T4
                candidates = ctx.get("candidates", {"total_containers": 120})
                road_cap = ctx.get("road_capacity", {"available_trucks": 20})
                sea_cap = ctx.get("sea_capacity", {"feeder_id": "FEEDER ATLANTIC-03"})
                # If deviation exists and we already had a split, this is re-compute with updated sea
                # Still call compute_itt_split
                tool_calls.append({"id": "call_T4", "type": "function", "function": {"name": "compute_itt_split", "arguments": json.dumps({"candidates": candidates, "road_capacity": road_cap, "sea_capacity": sea_cap, "tuas_vessel_departure": ctx.get("tuas_vessel_departure", "2026-08-19T20:00:00+08:00"), "constraints": ctx.get("constraints", {})})}})

        # If we've already approved HITL-1..3, then dispatch and Tuas
        if "HITL-1" in approved or "hitl_1" in approved:
            if "dispatch_road_itt" not in succeeded_tools and "dispatch_road_itt" in available:
                if "HITL-2" in approved or "hitl_2" in approved:
                    # Build container_ids from candidates for dispatch
                    candidates = ctx.get("candidates", {}) or {}
                    all_containers = candidates.get("containers", []) if isinstance(candidates, dict) else []
                    def _ids(n, offset=0):
                        if all_containers and isinstance(all_containers, list):
                            result = []
                            for idx, c in enumerate(all_containers[offset:offset+n]):
                                cid = c.get("container_id")
                                if cid:
                                    result.append(cid)
                                else:
                                    result.append(f"C{idx+offset:06d}")
                            return result
                        return [f"C{i+offset:06d}" for i in range(n)]
                    if ctx.get("deviation_log"):
                        ids = _ids(20, 80)
                        if len(ids) < 20:
                            try:
                                from app.mocks.data import generate_containers
                                gen = generate_containers()
                                ids = [c["container_id"] for c in gen[80:100]]
                            except Exception:
                                ids = [f"DELTA{i:03d}" for i in range(20)]
                        tool_calls.append({"id": "call_dispatch_delta", "type": "function", "function": {"name": "dispatch_road_itt", "arguments": json.dumps({"num_trucks": 4, "route": "PPT→West Coast Hwy→AYE→Tuas", "container_ids": ids or [f"DELTA{i:03d}" for i in range(4)]})}})
                    else:
                        ids = _ids(80, 0)
                        if len(ids) < 80:
                            try:
                                from app.mocks.data import generate_containers
                                gen = generate_containers()
                                ids = [c["container_id"] for c in gen[:80]]
                            except Exception:
                                ids = [f"C{i:06d}" for i in range(80)]
                        tool_calls.append({"id": "call_dispatch", "type": "function", "function": {"name": "dispatch_road_itt", "arguments": json.dumps({"num_trucks": 20, "route": "PPT→West Coast Hwy→AYE→Tuas", "container_ids": ids})}})
            if "request_feeder_hold" not in succeeded_tools and "request_feeder_hold" in available:
                if "HITL-3" in approved or "hitl_3" in approved:
                    tool_calls.append({"id": "call_hold", "type": "function", "function": {"name": "request_feeder_hold", "arguments": json.dumps({"feeder_id": "FEEDER ATLANTIC-03", "hold_hours": 1.0})}})

        # Delta dispatch after deviation + HITL-5 approved
        if ctx.get("deviation_log") and ("HITL-5" in approved or "hitl_5" in approved) and "dispatch_road_itt" in succeeded_tools and not ctx.get("delta_dispatched"):
            if "dispatch_road_itt" in available:
                candidates = ctx.get("candidates", {}) or {}
                all_containers = candidates.get("containers", []) if isinstance(candidates, dict) else []
                def _delta_ids(n, offset=80):
                    if all_containers and isinstance(all_containers, list) and len(all_containers) >= offset + n:
                        return [c.get("container_id") or f"C{idx+offset:06d}" for idx, c in enumerate(all_containers[offset:offset+n])]
                    try:
                        from app.mocks.data import generate_containers
                        gen = generate_containers()
                        return [c["container_id"] for c in gen[offset:offset+n]]
                    except Exception:
                        return [f"DELTA{i:03d}" for i in range(n)]
                ids = _delta_ids(20, 80)
                tool_calls.append({"id": "call_dispatch_delta", "type": "function", "function": {"name": "dispatch_road_itt", "arguments": json.dumps({"num_trucks": 4, "route": "PPT→West Coast Hwy→AYE→Tuas", "container_ids": ids or [f"DELTA{i:03d}" for i in range(4)]})}})

        # Tuas loading sequence — call after all 3 HITL gates approved (don't wait for dispatch+hold)
        if "update_tuas_loading_sequence" not in succeeded_tools and "update_tuas_loading_sequence" in available:
            all_3_approved = "HITL-1" in approved and "HITL-2" in approved and "HITL-3" in approved
            if all_3_approved and "HITL-4" not in approved and "hitl_4" not in approved:
                def _split_ids():
                    candidates = ctx.get("candidates", {}) or {}
                    all_containers = candidates.get("containers", []) if isinstance(candidates, dict) else []
                    if all_containers and isinstance(all_containers, list) and len(all_containers) >= 120:
                        road_ids = [c["container_id"] for c in all_containers[:80]]
                        sea_ids = [c["container_id"] for c in all_containers[80:]]
                        return road_ids, sea_ids
                    try:
                        from app.mocks.data import generate_containers
                        gen = generate_containers()
                        road_ids = [c["container_id"] for c in gen[:80]]
                        sea_ids = [c["container_id"] for c in gen[80:]]
                        return road_ids, sea_ids
                    except Exception:
                        return [f"R{i:03d}" for i in range(80)], [f"S{i:03d}" for i in range(40)]
                road_ids, sea_ids = _split_ids()
                tool_calls.append({"id": "call_T5", "type": "function", "function": {"name": "update_tuas_loading_sequence", "arguments": json.dumps({"vessel_id": ctx.get("vessel_id", "MV PACIFIC STAR"), "itt_eta_road": "2026-08-19T14:30:00+08:00", "itt_eta_sea": "2026-08-19T16:30:00+08:00", "container_ids_road": road_ids, "container_ids_sea": sea_ids})}})

        # Second T5 after deviation (delta)
        if ctx.get("deviation_log") and "HITL-5" in approved:
            if not ctx.get("tuas_second_done") and "update_tuas_loading_sequence" in succeeded_tools:
                try:
                    from app.mocks.data import generate_containers
                    gen2 = generate_containers()
                    road_ids2 = [c["container_id"] for c in gen2[:100]]
                    sea_ids2 = [c["container_id"] for c in gen2[100:120]]
                except Exception:
                    candidates = ctx.get("candidates", {}) or {}
                    all_containers = candidates.get("containers", []) if isinstance(candidates, dict) else []
                    if all_containers and isinstance(all_containers, list) and len(all_containers) >= 120:
                        road_ids2 = [c["container_id"] for c in all_containers[:100]]
                        sea_ids2 = [c["container_id"] for c in all_containers[100:120]]
                    else:
                        road_ids2 = [f"R{i:03d}" for i in range(100)]
                        sea_ids2 = [f"S{i:03d}" for i in range(20)]
                if "dispatch_road_itt" in succeeded_tools and ctx.get("delta_dispatched"):
                    tool_calls.append({"id": "call_T5_2", "type": "function", "function": {"name": "update_tuas_loading_sequence", "arguments": json.dumps({"vessel_id": ctx.get("vessel_id", "MV PACIFIC STAR"), "itt_eta_road": "2026-08-19T16:00:00+08:00", "itt_eta_sea": "2026-08-19T18:00:00+08:00", "container_ids_road": road_ids2, "container_ids_sea": sea_ids2})}})

        # Limit to max 3 parallel tools per batch
        if len(tool_calls) > 3:
            tool_calls = tool_calls[:3]

        content = json.dumps({"confidence": 0.92, "reason": "deterministic mock planner"}) if tool_calls else json.dumps({"confidence": 0.95, "status": "awaiting HITL or complete"})

        @dataclass
        class _Resp:
            content: str
            tool_calls: list
            finish_reason: str = "stop"
            usage: dict = None
            model: str = "mock"
            provider: str = "mock"
            latency_ms: float = 5.0
            raw: dict = None
            def __post_init__(self):
                if self.usage is None:
                    self.usage = {}
                if self.raw is None:
                    self.raw = {}

        return _Resp(content=content, tool_calls=tool_calls)


def mock_provider_for_state(state: dict[str, Any]):
    """Create a _MockProvider for the given state."""
    return _MockProvider(state)


def fallback_llm_response(state: dict[str, Any], schemas: list[dict[str, Any]]):
    """Use mock provider as fallback when no real LLM is available."""
    mock = _MockProvider(state)
    return mock.chat(state.get("messages", []), tools=schemas)
