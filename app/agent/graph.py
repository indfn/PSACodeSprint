"""Graph assembly — 4 nodes: agent, tools, hitl (interrupt), monitor (Phase 6.9).

Optional LangSmith tracing: set LANGCHAIN_TRACING_V2=true + LANGCHAIN_API_KEY
in .env to enable trace capture at https://smith.langchain.com.
"""
from __future__ import annotations

import os
from typing import Any

# Optional LangSmith tracing — must be set before graph compilation
if os.environ.get("LANGCHAIN_TRACING_V2") == "true" and os.environ.get("LANGCHAIN_API_KEY"):
    os.environ.setdefault("LANGCHAIN_PROJECT", "psa-nexus")

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.agent.state import AgentState
from app.agent.nodes import agent_node, tool_node
from app.hitl.gates import hitl_node
from app.agent.monitor import monitor_node


def route_after_agent(state: dict[str, Any]) -> str:
    # Pure routing — no mutation. HITL gates are set in agent_node; router just reads.
    if state.get("pending_tool_calls"):
        return "tools"
    if state.get("hitl_pending"):
        return "hitl"
    if state.get("escalation"):
        return "hitl"
    # After all HITL-1..4 approved and dispatch+Tuas done, check if monitoring is needed.
    # Monitor should only fire AFTER HITL-4 approved (charter: steps 12-17 after step 10 complete).
    ctx = state.get("context", {}) or {}
    # Check HITL-4 history — only monitor after approval
    has_hitl4 = any(
        (h.get("gate_id") if isinstance(h, dict) else getattr(h, "gate_id", "")) and str(h.get("gate_id") if isinstance(h, dict) else getattr(h, "gate_id", "")).lower().replace("-", "_") == "hitl_4"
        for h in (state.get("hitl_history", []) or [])
        if (h.get("decision") if isinstance(h, dict) else getattr(h, "decision", "")) and str(h.get("decision") if isinstance(h, dict) else getattr(h, "decision", "")).lower() == "approve"
    )
    # Also guard: need dispatched and tuas_sequence exists
    if has_hitl4 and ctx.get("dispatched") and not ctx.get("monitored"):
        return "monitor"
    # Fallback: if not yet hitl4 but dispatched+hold+tuas pending, don't monitor yet — wait for HITL
    return END


def _has_hitl_history(state: dict[str, Any], gate_id: str) -> bool:
    history = state.get("hitl_history", []) or []
    for h in history:
        gid = h.get("gate_id") if isinstance(h, dict) else getattr(h, "gate_id", None)
        if gid == gate_id or gid == gate_id.lower() or gid == gate_id.replace("-", "_").lower() or gid == gate_id.replace("_", "-").upper():
            # also handle hitl_1 vs HITL-1
            if str(gid).lower().replace("-", "_") == gate_id.lower().replace("-", "_"):
                return True
    return False


def route_after_monitor(state: dict[str, Any]) -> str:
    if state.get("escalation") or state.get("hitl_pending"):
        return "hitl"
    if state.get("deviation_log"):
        return "agent"  # re-plan after deviation (will re-compute already done, but agent will handle delta dispatch)
    return END


# Singleton checkpointer — reused across run_agent / resume_agent so thread_id checkpoint persists
_checkpointer = MemorySaver()
_compiled_graph = None


def build_graph():
    global _compiled_graph, _checkpointer
    # Reuse compiled graph if already built (keeps same checkpointer)
    if _compiled_graph is not None:
        return _compiled_graph

    graph = StateGraph(AgentState)

    # Nodes — single hitl node (not 5), single monitor node
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("hitl", hitl_node)
    graph.add_node("monitor", monitor_node)

    # Edges
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", route_after_agent, {
        "tools": "tools",
        "hitl": "hitl",
        "monitor": "monitor",
        END: END,
    })
    graph.add_edge("tools", "agent")
    graph.add_edge("hitl", "agent")       # after Command(resume) the graph re-enters hitl_node, then routes back to agent
    graph.add_conditional_edges("monitor", route_after_monitor, {
        "hitl": "hitl",       # berth conflict → re-compute → HITL
        "agent": "agent",     # deviation -> re-plan after HITL? Actually deviation already set hitl_pending, so hitl first. If no deviation, agent maybe to handle completion.
        END: END,
    })

    _compiled_graph = graph.compile(checkpointer=_checkpointer)
    return _compiled_graph


def reset_graph():
    """For tests — clear compiled graph and checkpointer."""
    global _compiled_graph, _checkpointer
    _compiled_graph = None
    _checkpointer = MemorySaver()
