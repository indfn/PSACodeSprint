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
        run_id = kwargs.pop("_run_id", "")
        hitl_approved = kwargs.pop("_hitl_approved", None)

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
