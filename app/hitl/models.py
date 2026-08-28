"""HITL gate models — 5 charter gates with timeouts and timeout_actions (Phase 6.5)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HITLGate:
    gate_id: str  # "HITL-1" .. "HITL-5" (or hitl_1 legacy)
    gate_name: str  # "Approve ITT Split" etc.
    trigger: str  # charter trigger condition
    description: str = ""
    approval_card: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 1800  # default 30 min
    timeout_action: str = "escalate"  # escalate / cancel_dispatch / hold_sequence / halt
    options: list[str] = field(default_factory=lambda: ["approve", "reject", "modify"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "trigger": self.trigger,
            "description": self.description,
            "approval_card": self.approval_card,
            "timeout_seconds": self.timeout_seconds,
            "timeout_action": self.timeout_action,
            "options": self.options,
        }


@dataclass
class HITLDecision:
    gate_id: str
    decision: str  # approve | reject | modify | timeout
    reason: str | None = None
    modifications: dict[str, Any] | None = None
    timestamp: str = ""
    decided_by: str = "operator"

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "decision": self.decision,
            "reason": self.reason,
            "modifications": self.modifications,
            "timestamp": self.timestamp,
            "decided_by": self.decided_by,
        }


# Canonical 5 gates — charter Section 4, also mirrored from YAML hitl_gates
# We normalise both HITL-1 and hitl_1 forms to support both graph and YAML lookups.
HITL_GATES: dict[str, HITLGate] = {
    "HITL-1": HITLGate(
        gate_id="HITL-1",
        gate_name="Approve ITT Split",
        trigger="split computed",
        description="Operator approves the optimal road/sea split and cost.",
        timeout_seconds=1800,  # 30 min
        timeout_action="escalate",
    ),
    "HITL-2": HITLGate(
        gate_id="HITL-2",
        gate_name="Approve Truck Dispatch",
        trigger="truck dispatch ready",
        description="Operator approves dispatch of prime movers.",
        timeout_seconds=900,  # 15 min
        timeout_action="cancel_dispatch",
    ),
    "HITL-3": HITLGate(
        gate_id="HITL-3",
        gate_name="Approve Feeder Hold",
        trigger="feeder hold request ready",
        description="Operator approves holding feeder at berth.",
        timeout_seconds=900,  # 15 min
        timeout_action="escalate",
    ),
    "HITL-4": HITLGate(
        gate_id="HITL-4",
        gate_name="Approve Loading Sequence Update",
        trigger="Tuas QC sequence update ready",
        description="Operator approves QC reassignment at Tuas.",
        timeout_seconds=600,  # 10 min
        timeout_action="hold_sequence",
    ),
    "HITL-5": HITLGate(
        gate_id="HITL-5",
        gate_name="Escalate to Duty Manager",
        trigger="escalation fired",
        description="Duty Manager review after escalation or if agent cannot resolve.",
        timeout_seconds=1800,  # 30 min
        timeout_action="halt",
    ),
    # Legacy aliases (YAML uses hitl_1)
    "hitl_1": HITLGate(
        gate_id="HITL-1",
        gate_name="Approve ITT Split",
        trigger="split computed",
        timeout_seconds=1800,
        timeout_action="escalate",
    ),
    "hitl_2": HITLGate(
        gate_id="HITL-2",
        gate_name="Approve Truck Dispatch",
        trigger="truck dispatch ready",
        timeout_seconds=900,
        timeout_action="cancel_dispatch",
    ),
    "hitl_3": HITLGate(
        gate_id="HITL-3",
        gate_name="Approve Feeder Hold",
        trigger="feeder hold request ready",
        timeout_seconds=900,
        timeout_action="escalate",
    ),
    "hitl_4": HITLGate(
        gate_id="HITL-4",
        gate_name="Approve Loading Sequence Update",
        trigger="Tuas QC sequence update ready",
        timeout_seconds=600,
        timeout_action="hold_sequence",
    ),
    "hitl_5": HITLGate(
        gate_id="HITL-5",
        gate_name="Escalate to Duty Manager",
        trigger="escalation fired",
        timeout_seconds=1800,
        timeout_action="halt",
    ),
}

# Also expose lower-case hyphen forms
for k, v in list(HITL_GATES.items()):
    HITL_GATES[k.lower()] = v


# Canonical HITL-5 fallback dict — used across nodes.py, monitor.py, handler.py
HITL5_FALLBACK: dict[str, Any] = {
    "gate_id": "HITL-5",
    "gate_name": "Escalate to Duty Manager",
    "trigger": "escalation fired",
    "timeout_seconds": 1800,
    "timeout_action": "halt",
}
