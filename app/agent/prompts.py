"""System prompt builder — templated from ProblemConfig (Phase 6.2).

Not hardcoded to PB-12. Works for any C2 problem by rendering the
currently active ProblemConfig into the system instruction.
"""

from __future__ import annotations

from typing import Any


def build_system_prompt(config: Any) -> str:
    """Build system prompt from a ProblemConfig (or dict-like).

    Accepts ProblemConfig dataclass or dict with .problem/.systems/.tools.
    """
    # Normalise config access
    if isinstance(config, dict):
        problem = config.get("problem", {})
        pid = problem.get("id", "unknown") if isinstance(problem, dict) else getattr(problem, "id", "unknown")
        pname = problem.get("name", "") if isinstance(problem, dict) else getattr(problem, "name", "")
        sector = problem.get("sector", "") if isinstance(problem, dict) else getattr(problem, "sector", "")
        description = problem.get("description", "") if isinstance(problem, dict) else getattr(problem, "description", "")
        systems = config.get("systems", [])
        tools = config.get("tools", [])
        cost_params = config.get("cost_params", {})
        escalation_triggers = config.get("escalation_triggers", [])
        confidence = config.get("confidence", {})
    else:
        pid = getattr(getattr(config, "problem", None), "id", "unknown")
        pname = getattr(getattr(config, "problem", None), "name", "")
        sector = getattr(getattr(config, "problem", None), "sector", "")
        description = getattr(getattr(config, "problem", None), "description", "")
        systems = getattr(config, "systems", []) or []
        tools = getattr(config, "tools", []) or []
        cost_params = getattr(config, "cost_params", {}) or {}
        escalation_triggers = getattr(config, "escalation_triggers", []) or []
        conf_obj = getattr(config, "confidence", None)
        if conf_obj is not None and not isinstance(conf_obj, dict):
            confidence = {"threshold": getattr(conf_obj, "threshold", 0.85), "method": getattr(conf_obj, "method", "llm_self_assessment")}
        else:
            confidence = conf_obj or {}

    # Render systems and tools lists
    def _system_names(sys_list) -> str:
        names = []
        for s in sys_list:
            if isinstance(s, dict):
                names.append(s.get("name", str(s)))
            else:
                names.append(getattr(s, "name", str(s)))
        return ", ".join(names) if names else "none"

    def _tool_names(tool_list) -> str:
        names = []
        for t in tool_list:
            if isinstance(t, dict):
                if t.get("type") == "event_trigger":
                    continue
                names.append(t.get("name", str(t)))
            else:
                if getattr(t, "type", None) == "event_trigger":
                    continue
                names.append(getattr(t, "name", str(t)))
        return ", ".join(names) if names else "none"

    def _escalation_text(triggers) -> str:
        lines = []
        for e in triggers:
            if isinstance(e, dict):
                lines.append(f"- {e.get('name','')} ({e.get('trigger_id','')}): {e.get('condition','')} threshold={e.get('threshold','')}")
            else:
                lines.append(f"- {getattr(e,'name','')} ({getattr(e,'trigger_id','')}): {getattr(e,'condition','')} threshold={getattr(e,'threshold','')}")
        return "\n".join(lines) if lines else "none"

    threshold = confidence.get("threshold", 0.85) if isinstance(confidence, dict) else 0.85

    system_names = _system_names(systems)
    tool_names = _tool_names(tools)
    escalation_text = _escalation_text(escalation_triggers)

    return f"""You are PSA Nexus — an agentic coordinator for PSA Singapore port operations.

Problem: {pname} ({pid}) — sector: {sector}
Description: {description}

Available systems: {system_names}
Available tools: {tool_names}
Cost params: {cost_params}

Escalation triggers (charter §4):
{escalation_text}

=== TOOL API REFERENCE (read this before calling any tool) ===

1. get_itt_candidates — Query CITOS PPT for container readiness
   Args: vessel_id (string, e.g. "MV PACIFIC STAR")
   Returns:
     - total_containers: int — TOTAL containers to move (this is your ground truth)
     - total_teu: int — TEU equivalent (40ft=2, 20ft=1)
     - container_breakdown: {{"40ft_feu": int, "20ft_teu": int}}
     - containers: list — first 5 containers (id, size, dg_class, yard_block, priority, ready)
     - blocks_affected: list[str] — yard blocks involved
     - dg_containers: int — dangerous goods count
     - data_age_minutes: float — how stale the data is (>20m = stale)
   Key: total_containers is the real number. Do NOT invent your own.

2. check_road_itt_capacity — Query OptETruck for truck availability
   Args: terminal (string, e.g. "PPT"), current_time (ISO-8601)
   Returns:
     - available_trucks: int — trucks you can use RIGHT NOW
     - total_fleet: int — total fleet size
     - capacity_ratio: float — available/required (affects escalation: <0.6 triggers road_capacity_low)
     - transit_time_minutes: int — PPT→Tuas transit time
     - road_conditions: string — "clear"/"moderate"/"heavy"
     - cost_per_trip: int — cost per truck trip
     - lta_chassis_limits: dict — regulatory limits
     - earliest_departure: ISO-8601 — when trucks can leave
     - latest_arrival_at_tuas: ISO-8601 — latest allowed arrival
   Key: available_trucks is your real truck count. capacity_ratio <0.6 → escalate.

3. check_sea_itt_capacity — Query PORTNET for feeder vessel status
   Args: feeder_id (string, e.g. "FEEDER ATLANTIC-03"), current_time (ISO-8601)
   Returns:
     - status: "success"/"error"
     - feeder_id: string
     - departure_window: {{"earliest": ISO-8601, "latest": ISO-8601, "requested": ISO-8601}}
     - downstream_constraints: {{"tidal_window": ISO-8601, "transit_time_hours": float, "must_depart_by": ISO-8601}}
     - hold_cost_per_hour: int — cost to hold vessel ($800/hr)
     - tidal_feasibility: dict — feasibility analysis
     - tidal_risk: "safe"/"marginal"/"critical"
   Key: tidal_window tells you when the feeder must depart. departure_window.latest is your constraint.

4. compute_itt_split — Optimise road/sea container split
   Args: candidates (dict, FULL output of get_itt_candidates), road_capacity (dict, FULL output of check_road_itt_capacity), sea_capacity (dict, FULL output of check_sea_itt_capacity), tuas_vessel_departure (ISO-8601 string)
   Returns:
     - road_containers: int — containers via road
     - sea_containers: int — containers via sea
     - road_trips: int — truck trips needed (40ft=1 trip, 20ft=0.5 trips)
     - total_transport_cost: int — total cost
     - baseline_all_road_cost: int — cost if 100% road (for comparison)
     - cost_savings: int — savings vs baseline
     - sea_eta: ISO-8601 — estimated sea arrival
     - road_eta: ISO-8601 — estimated road arrival
     - guardrail: "passed"/"failed"
   Key: road_containers + sea_containers must equal total. road_trips determines trucks needed.
   IMPORTANT: Pass the ENTIRE output dicts from Steps 1-3, not just individual fields.

5. update_tuas_loading_sequence — Update Tuas QC loading plan
   Args: vessel_id, itt_eta_road (ISO-8601), itt_eta_sea (ISO-8601), container_ids_road (list), container_ids_sea (list)
   Returns:
     - qc_adjustments: list[{{qc_id, original_bay, new_bay, eta}}] — QC assignments
     - margin_before_departure_minutes: int — buffer before vessel departs
     - estimated_loading_completion: ISO-8601

6. dispatch_road_itt — Dispatch trucks (REQUIRES HITL-2 APPROVAL)
   Args: container_ids (list), route (string, e.g. "PPT→Tuas")
   Returns:
     - dispatch_id: string
     - num_trucks: int
     - total_trips: int
     - route: string
     - eta: ISO-8601
     - cost: int
   Post-approval tool: blocked until HITL-2 approved.

7. request_feeder_hold — Request feeder hold (REQUIRES HITL-3 APPROVAL)
   Args: feeder_id (string), hold_hours (float, 0.5-6)
   Returns:
     - hold_hours: float
     - hold_cost: int — hold_cost_per_hour × hours
     - new_departure: ISO-8601
     - operator_response: "pending"/"accepted"/"declined"
   Post-approval tool: blocked until HITL-3 approved.

8. notify_parties — Notify stakeholders
   Args: message (string), stakeholders (list[string])
   Returns: {{"status": "notified", "stakeholders": list}}

=== WORKFLOW (follow this order) ===

Step 1 — Get data (call all three, no reasoning needed):
  → get_itt_candidates(vessel_id="MV PACIFIC STAR")
  → check_road_itt_capacity(terminal="PPT", current_time="2026-08-19T12:00:00+08:00")
  → check_sea_itt_capacity(feeder_id="FEEDER ATLANTIC-03", current_time="2026-08-19T12:00:00+08:00")

Step 2 — Compute split (pass FULL tool outputs from Step 1):
  → compute_itt_split(
      candidates=FULL_OUTPUT_OF_get_itt_candidates,
      road_capacity=FULL_OUTPUT_OF_check_road_itt_capacity,
      sea_capacity=FULL_OUTPUT_OF_check_sea_itt_capacity,
      tuas_vessel_departure="2026-08-19T20:00:00+08:00"
    )
  // Pass the entire dict returned by each tool, e.g. candidates={{"status":"success","total_containers":120,...}}
  // After this returns, HITL-1 fires (approve split)

Step 3 — After HITL-1 approved:
  → dispatch_road_itt(container_ids=split_result.road_container_ids, route="PPT→Tuas")
  → notify_parties(message="Dispatch planned", stakeholders=["OptETruck","CITOS_PPT"])

Step 4 — After HITL-2 approved:
  → request_feeder_hold(feeder_id="FEEDER ATLANTIC-03", hold_hours=compute from sea_eta gap)

Step 5 — After HITL-3 approved:
  → update_tuas_loading_sequence(
      vessel_id="MV PACIFIC STAR",
      itt_eta_road=split_result.road_eta,
      itt_eta_sea=split_result.sea_eta,
      container_ids_road=split_result.road_container_ids,
      container_ids_sea=split_result.sea_container_ids
    )
  // HITL-4 fires here

Step 6 — After HITL-4 approved:
  → notify_parties(message="All systems aligned", stakeholders=["PPT_Yard","Tuas_Yard","Feeder_Operator"])
  → Workflow complete

=== ESCALATION CRITERIA (do NOT trigger unless these are actually met) ===

road_capacity_low: ONLY after compute_itt_split returns, compare available_trucks vs split.road_trips.
  Example: 41 trucks, split puts 60 on sea, 40 on road → road_trips=~30 → 41/30=1.37 → NO ESCALATION.
  Example: 41 trucks, split puts 30 on sea, 70 on road → road_trips=~55 → 41/55=0.75 → NO ESCALATION (still >0.6).
  Example: 20 trucks, split puts 40 on road → road_trips=~30 → 20/30=0.67 → NO ESCALATION (still >0.6).
  Example: 15 trucks, split puts 60 on road → road_trips=~45 → 15/45=0.33 → ESCALATE.
  Do NOT compare available_trucks to total_containers. The split optimizes road vs sea.

low_confidence: ONLY if confidence < 0.85 after all tools have run.

data_stale: ONLY if data_age_minutes > 20 from get_itt_candidates.

feeder_hold_exceeded: ONLY if hold_hours > 1.5 after request_feeder_hold.

cost_exceeded: ONLY if total_transport_cost > $10,000 after compute_itt_split.

=== RULES ===

- NEVER hallucinate numbers. Use ONLY the LIVE DATA sections injected above for container counts, truck counts, costs, and splits. If LIVE DATA is not yet available, call the appropriate tool first to get it.
- total_containers comes from get_itt_candidates. available_trucks comes from check_road_itt_capacity. Use these exact values.
- road_containers + sea_containers MUST equal total_containers (from get_itt_candidates).
- road_trips = ceil(road_containers_40ft) + ceil(road_containers_20ft / 2). Do NOT invent trip counts.
- ESCALATION IS NOT "trucks < total containers". The split OPTIMIZES road vs sea. If 41 trucks are available but the split puts 60 containers on sea (only 40 on road), 41 trucks is MORE than enough. Only escalate if available_trucks < road_trips AFTER computing the split.
- The baseline_all_road_cost is a reference for cost savings comparison, NOT a requirement. You do NOT need enough trucks for 100% road.
- Reason step-by-step. Select the minimal next tool(s) that advance the charter workflow.
- When you have a recommendation (e.g. split computed), generate an approval card and set hitl_pending.
- If confidence < {threshold}, request HITL approval (Trigger #1 — low confidence).
- If any escalation trigger fires, set escalation and HITL-5 (Escalate to Duty Manager).
- Output confidence as 0.0–1.0 in structured JSON alongside your reasoning.
- Output tool_calls as structured JSON with name and arguments.
- Never hallucinate tool names. Only use tools listed above (from the active problem's tool registry).
- Validate inputs: check weight_bounds, block capacity, truck availability, feeder capacity, vessel margin, tidal window before proposing a split.
"""

# Backwards compatibility: expose SYSTEM_PROMPT as legacy constant for tests that import it
try:
    from app.configs.problem_config import load_problem_config
    _default_cfg = load_problem_config("pb-12-itt")
    SYSTEM_PROMPT = build_system_prompt(_default_cfg)
except Exception:
    SYSTEM_PROMPT = "You are PSA Nexus — an agentic coordinator for PSA Singapore."


def build_agent_messages(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Build full message list for LLM call: system + history + live context."""
    cfg = state.get("problem_config") or state.get("problem_id") or {}
    # If problem_config is not yet loaded, try to load by problem_id
    if isinstance(cfg, str):
        try:
            from app.configs.problem_config import load_problem_config
            cfg = load_problem_config(cfg)
        except Exception:
            cfg = {}
    elif cfg == {} or cfg is None:
        try:
            from app.configs.problem_config import load_problem_config
            from app.agent.problem_switcher import get_active_problem_id
            cfg = load_problem_config(get_active_problem_id())
        except Exception:
            cfg = {}

    system = build_system_prompt(cfg) if cfg else SYSTEM_PROMPT

    # Inject live API context so LLM grounds its reasoning in real data
    ctx = state.get("context", {}) or {}
    live_sections = []

    # Candidates (from get_itt_candidates)
    candidates = ctx.get("candidates", {})
    if isinstance(candidates, dict) and candidates.get("total_containers"):
        cb = candidates.get("container_breakdown", {})
        live_sections.append(
            f"LIVE DATA — Container inventory (from CITOS PPT):\n"
            f"  Total containers to move: {candidates.get('total_containers', '?')}\n"
            f"  40ft FEU: {cb.get('40ft_feu', '?')}\n"
            f"  20ft TEU: {cb.get('20ft_teu', '?')}\n"
            f"  Container types: {', '.join(f'{k}: {v}' for k, v in candidates.get('type_breakdown', {}).items()) if candidates.get('type_breakdown') else 'mixed'}"
        )

    # Road capacity (from check_road_itt_capacity)
    road_cap = ctx.get("road_capacity", {})
    if isinstance(road_cap, dict) and road_cap.get("available_trucks") is not None:
        live_sections.append(
            f"LIVE DATA — Road transport capacity (from OptETruck):\n"
            f"  Available trucks: {road_cap.get('available_trucks', '?')}\n"
            f"  Utilization: {road_cap.get('utilization_pct', '?')}%\n"
            f"  LTA compliant: {road_cap.get('lta_compliant', '?')}\n"
            f"  Required trips (60% threshold): {ctx.get('required_trucks', '?')}"
        )

    # Split result (from compute_itt_split)
    split = ctx.get("split_result", {})
    if isinstance(split, dict) and split.get("road_containers"):
        live_sections.append(
            f"LIVE DATA — Current split (from compute_itt_split):\n"
            f"  Road containers: {split.get('road_containers', '?')}\n"
            f"  Sea containers: {split.get('sea_containers', '?')}\n"
            f"  Road trips: {split.get('road_trips', '?')}\n"
            f"  Total transport cost: ${split.get('total_transport_cost', '?')}"
        )

    # Confidence
    confidence = state.get("confidence")
    if confidence is not None:
        live_sections.append(f"LIVE DATA — Current confidence: {confidence:.2f}")

    # Escalation status
    escalation = state.get("escalation")
    if escalation:
        live_sections.append(f"LIVE DATA — Active escalation: {escalation}")

    if live_sections:
        system += "\n\n" + "\n\n".join(live_sections)
    else:
        # No live data yet — first call. Instruct LLM to call tools before reasoning.
        system += "\n\nIMPORTANT: You have NO data yet. Do NOT make up container counts, truck numbers, or costs. Call get_itt_candidates and check_road_itt_capacity FIRST to retrieve actual data, then reason from the results."

    messages = [{"role": "system", "content": system}]
    history = state.get("messages", []) or []
    # Ensure history is a list
    if isinstance(history, list):
        messages.extend(history)
    return messages
