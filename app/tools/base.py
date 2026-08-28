from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ToolResult:
    output: dict
    confidence: float
    metadata: dict = field(default_factory=dict)


class BaseTool(ABC):
    name: str
    description: str
    parameters_schema: dict
    post_approval: bool = False
    fallback_tool: str | None = None
    timeout_seconds: int = 10

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        ...

    async def call(self, **kwargs) -> ToolResult:
        t0 = time.monotonic()
        run_id = kwargs.get("_run_id", "") or kwargs.get("run_id", "")
        hitl_approved = kwargs.get("_hitl_approved", None)
        _run_id_val = kwargs.pop("_run_id", run_id)
        _hitl_val = kwargs.pop("_hitl_approved", hitl_approved)

        required = self.parameters_schema.get("required", []) if isinstance(self.parameters_schema, dict) else []
        properties = self.parameters_schema.get("properties", {}) if isinstance(self.parameters_schema, dict) else {}

        for req in required:
            if req not in kwargs:
                duration_ms = int((time.monotonic() - t0) * 1000)
                return ToolResult(
                    output={"error": f"Missing required parameter: {req}"},
                    confidence=0.0,
                    metadata={
                        "tool_name": self.name,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": duration_ms,
                        "run_id": run_id,
                        "error": f"missing_required:{req}",
                    },
                )

        for key in list(kwargs.keys()):
            if key.startswith("_"):
                continue
            if properties and key not in properties:
                duration_ms = int((time.monotonic() - t0) * 1000)
                return ToolResult(
                    output={"error": f"Unknown parameter: {key}. Hallucinated argument."},
                    confidence=0.0,
                    metadata={
                        "tool_name": self.name,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": duration_ms,
                        "run_id": run_id,
                        "error": f"hallucinated_arg:{key}",
                    },
                )

        for key, val in list(kwargs.items()):
            if key.startswith("_"):
                continue
            prop = properties.get(key, {}) if isinstance(properties, dict) else {}
            expected = prop.get("type") if isinstance(prop, dict) else None
            if expected == "integer" and isinstance(val, str):
                try:
                    kwargs[key] = int(val)
                except Exception:
                    duration_ms = int((time.monotonic() - t0) * 1000)
                    return ToolResult(
                        output={"error": f"Parameter {key} must be integer, got {val!r}"},
                        confidence=0.0,
                        metadata={"tool_name": self.name, "timestamp": datetime.now(timezone.utc).isoformat(), "duration_ms": duration_ms, "run_id": run_id, "error": f"type_mismatch:{key}"},
                    )
            elif expected == "number" and isinstance(val, str):
                try:
                    kwargs[key] = float(val)
                except Exception:
                    duration_ms = int((time.monotonic() - t0) * 1000)
                    return ToolResult(
                        output={"error": f"Parameter {key} must be number, got {val!r}"},
                        confidence=0.0,
                        metadata={"tool_name": self.name, "timestamp": datetime.now(timezone.utc).isoformat(), "duration_ms": duration_ms, "run_id": run_id, "error": f"type_mismatch:{key}"},
                    )

        # forward per-run context to execute for isolation
        kwargs["_run_id"] = _run_id_val
        if _hitl_val is not None:
            kwargs["_hitl_approved"] = _hitl_val
        try:
            result: ToolResult = await asyncio.wait_for(
                self.execute(**kwargs), timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - t0) * 1000)
            return ToolResult(
                output={"error": f"Tool {self.name} timed out after {self.timeout_seconds}s"},
                confidence=0.0,
                metadata={
                    "tool_name": self.name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": duration_ms,
                    "run_id": run_id,
                    "error": "timeout",
                },
            )
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            return ToolResult(
                output={"error": str(exc)},
                confidence=0.0,
                metadata={
                    "tool_name": self.name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": duration_ms,
                    "run_id": run_id,
                    "error": "execution_error",
                },
            )

        duration_ms = int((time.monotonic() - t0) * 1000)
        if not isinstance(result, ToolResult):
            return ToolResult(
                output={"error": "Tool did not return ToolResult"},
                confidence=0.0,
                metadata={
                    "tool_name": self.name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": duration_ms,
                    "run_id": run_id,
                    "error": "invalid_return",
                },
            )

        meta = dict(result.metadata) if result.metadata else {}
        meta.setdefault("tool_name", self.name)
        meta.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        meta.setdefault("duration_ms", duration_ms)
        meta.setdefault("run_id", run_id)
        result.metadata = meta
        return result

    def get_schema(self) -> dict:
        return {"name": self.name, "description": self.description, "parameters": self.parameters_schema}
