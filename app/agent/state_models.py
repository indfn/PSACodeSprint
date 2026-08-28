"""State helper models — TraceEntry, HITLDecision, Escalation (Phase 6.1)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TraceEntry:
    timestamp: str
    run_id: str
    node: str  # 'agent', 'tool', 'hitl', 'escalation', 'monitor'
    action: str  # 'reason', 'call_tool', 'show_card', 'escalate', 'deviation', 'monitor_check', 'fallback', 'hallucinated_tool', 'rate_limited'
    result: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    confidence: float = 0.0
    risk_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "run_id": self.run_id,
            "node": self.node,
            "action": self.action,
            "result": self.result,
            "duration_ms": self.duration_ms,
            "confidence": self.confidence,
            "risk_score": self.risk_score,
        }


@dataclass
class HITLDecision:
    gate_id: str
    decision: str  # 'approve' | 'reject' | 'modify' | 'timeout'
    reason: Optional[str] = None
    modifications: Optional[dict[str, Any]] = None
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


@dataclass
class Escalation:
    trigger: str
    severity: str = "high"
    message: str = ""
    timestamp: str = ""
    action: str = "escalate_to_human"

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger": self.trigger,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp,
            "action": self.action,
        }
