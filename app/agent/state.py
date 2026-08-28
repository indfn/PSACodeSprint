"""AgentState — LangGraph state schema for PSA Nexus (Phase 6.1).

Covers all charter bootstrap fields (Section 3 T6 — 11 fields) plus execution fields.
"""
from __future__ import annotations

from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    # Conversation — plain list (in-place mutation) to avoid Annotated reducer duplication
    # Nodes mutate messages via append and return full state; checkpoint stores snapshot directly.
    # Alternative reducer pattern (Annotated + delta) is valid but we use in-place for consistency.
    messages: list[dict[str, Any]]

    # Tool results
    tool_results: dict[str, Any]  # {tool_call_id: ToolResult serialized or dict}
    pending_tool_calls: list[dict[str, Any]]  # tool calls awaiting execution

    # HITL
    hitl_pending: Optional[dict[str, Any]]  # current HITLGate awaiting interrupt
    hitl_history: list[dict[str, Any]]  # past HITLDecision entries

    # Confidence & escalation
    confidence: float  # current confidence score (0.0–1.0)
    escalation: Optional[dict[str, Any]]  # active escalation (single) or list

    # Observability
    trace: list[dict[str, Any]]  # list[TraceEntry dict]
    deviation_log: list[dict[str, Any]]  # list[deviation dicts]

    # Config & identity
    problem_config: dict[str, Any]  # serialized ProblemConfig (or ProblemConfig object)
    problem_id: str  # shorthand for problem_config id
    run_id: str  # unique run identifier — also LangGraph thread_id
    status: str  # running | waiting_hitl | escalated | completed | failed | cancelled | holding | halted

    # Charter bootstrap context (Section 3 T6 — 11+ fields)
    # Holds event + derived context that persists across graph steps.
    context: dict[str, Any]

    # Resilience / HITL stale tracking (internal)
    hitl_gate_entered_at: Optional[str]  # ISO timestamp when current hitl gate was entered

    # Internal convenience: fallback flag
    fallback_used: bool
