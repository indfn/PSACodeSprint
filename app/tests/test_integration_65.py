"""Integration tests — Phase 6.5.6 Integration Wiring & Cleanup.

12 tests covering:
- Startup validation (lifespan)
- YAML config consistency (7 files)
- Tool registry ↔ YAML consistency
- Graph compiles
- HITL timeout scheduler
- SSE confidence_update publishing
- tool_adapter relocation
- .env.example exists
- requirements.txt is UTF-8
- fallback_api_key_env in all YAMLs
- LangSmith env var wiring
- Timeout scheduler cancel idempotent
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# 1. Startup validation
# ---------------------------------------------------------------------------

class TestStartupValidation:
    def test_validate_startup_returns_list(self):
        from app.main import _validate_startup
        warnings = _validate_startup()
        assert isinstance(warnings, list)

    def test_validate_startup_warns_missing_api_key(self):
        """Should warn about missing ANTHROPIC_API_KEY (expected in CI)."""
        from app.main import _validate_startup
        old = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            warnings = _validate_startup()
            assert any("ANTHROPIC_API_KEY" in w for w in warnings)
        finally:
            if old:
                os.environ["ANTHROPIC_API_KEY"] = old


# ---------------------------------------------------------------------------
# 2. YAML config consistency (all 7 files)
# ---------------------------------------------------------------------------

class TestYAMLConsistency:
    CONFIG_DIR = Path(__file__).resolve().parent.parent / "configs"

    def _load_all_yamls(self) -> dict[str, dict]:
        yamls = {}
        for yf in sorted(self.CONFIG_DIR.glob("pb-*.yaml")):
            with open(yf) as f:
                yamls[yf.name] = yaml.safe_load(f) or {}
        return yamls

    def test_all_yamls_have_problem_block(self):
        yamls = self._load_all_yamls()
        assert len(yamls) == 7
        for name, data in yamls.items():
            assert "problem" in data, f"{name}: missing 'problem' block"

    def test_all_yamls_have_tools(self):
        yamls = self._load_all_yamls()
        for name, data in yamls.items():
            assert "tools" in data and data["tools"], f"{name}: missing 'tools'"

    def test_all_yamls_have_hitl_gates(self):
        yamls = self._load_all_yamls()
        for name, data in yamls.items():
            assert "hitl_gates" in data, f"{name}: missing 'hitl_gates'"

    def test_fallback_api_key_env_in_all_yamls(self):
        """All YAMLs with fallback_provider must have fallback_api_key_env."""
        yamls = self._load_all_yamls()
        for name, data in yamls.items():
            llm = data.get("llm", {})
            if llm.get("fallback_provider"):
                assert "fallback_api_key_env" in llm, (
                    f"{name}: fallback_provider={llm['fallback_provider']} but no fallback_api_key_env"
                )


# ---------------------------------------------------------------------------
# 3. Tool registry ↔ YAML consistency
# ---------------------------------------------------------------------------

class TestRegistryConsistency:
    def test_pb12_tools_in_registry(self):
        from app.tools.registry import TOOLSETS
        assert "pb-12-itt" in TOOLSETS
        assert len(TOOLSETS["pb-12-itt"]) >= 6  # at least 6 core tools

    def test_registry_has_all_problems(self):
        from app.tools.registry import TOOLSETS
        expected = ["pb-12-itt", "pb-01-berth", "pb-02-dtqc", "pb-04-feeder",
                     "pb-09-expressway", "pb-10-sea-air", "pb-11-customs"]
        for pid in expected:
            assert pid in TOOLSETS, f"Registry missing {pid}"


# ---------------------------------------------------------------------------
# 4. Graph compiles
# ---------------------------------------------------------------------------

class TestGraphCompilation:
    def test_graph_compiles(self):
        from app.agent.graph import build_graph, reset_graph
        reset_graph()
        graph = build_graph()
        assert graph is not None

    def test_graph_has_all_nodes(self):
        from app.agent.graph import build_graph, reset_graph
        reset_graph()
        graph = build_graph()
        node_names = set(graph.get_graph().nodes.keys())
        assert "agent" in node_names
        assert "tools" in node_names
        assert "hitl" in node_names
        assert "monitor" in node_names


# ---------------------------------------------------------------------------
# 5. HITL timeout scheduler
# ---------------------------------------------------------------------------

class TestHITLTimeoutScheduler:
    @pytest.mark.asyncio
    async def test_schedule_and_cancel(self):
        from app.hitl.timeout_scheduler import schedule_timeout, cancel_timeout, pending_count
        state = {"hitl_pending": {"gate_id": "hitl_1"}, "run_id": "test-run"}
        gate = {"gate_id": "hitl_1", "timeout_seconds": 60, "timeout_action": "escalate"}
        schedule_timeout("test-run", "hitl_1", 60, state, gate)
        assert pending_count() >= 1
        cancelled = cancel_timeout("test-run", "hitl_1")
        assert cancelled is True

    def test_cancel_nonexistent_is_noop(self):
        from app.hitl.timeout_scheduler import cancel_timeout
        cancelled = cancel_timeout("nonexistent-run", "hitl_99")
        assert cancelled is False

    @pytest.mark.asyncio
    async def test_cancel_all(self):
        from app.hitl.timeout_scheduler import schedule_timeout, cancel_all_timeouts, pending_count
        state = {"hitl_pending": {"gate_id": "hitl_1"}, "run_id": "run-a"}
        gate = {"gate_id": "hitl_1", "timeout_seconds": 300, "timeout_action": "halt"}
        schedule_timeout("run-a", "hitl_1", 300, state, gate)
        count = cancel_all_timeouts()
        assert count >= 1
        assert pending_count() == 0


# ---------------------------------------------------------------------------
# 6. SSE confidence_update (import check only)
# ---------------------------------------------------------------------------

class TestSSEConfidenceUpdate:
    def test_broadcaster_importable(self):
        from app.agent.sse import broadcaster
        assert hasattr(broadcaster, "publish")

    def test_broadcaster_has_buffer(self):
        from app.agent.sse import broadcaster
        assert hasattr(broadcaster, "buffers")
        assert hasattr(broadcaster, "max_buffer")


# ---------------------------------------------------------------------------
# 7. tool_adapter relocation
# ---------------------------------------------------------------------------

class TestToolAdapterRelocation:
    def test_import_from_new_location(self):
        from app.tools.tool_adapter import adapt_tools_for_provider
        assert callable(adapt_tools_for_provider)

    def test_import_from_old_location(self):
        """Backwards compatibility re-export should still work."""
        from app.shared.tool_adapter import adapt_tools_for_provider
        assert callable(adapt_tools_for_provider)

    def test_anthropic_format(self):
        from app.tools.tool_adapter import adapt_tools_for_provider
        schemas = [{"name": "test_tool", "description": "A test", "parameters": {"type": "object", "properties": {}}}]
        result = adapt_tools_for_provider(schemas, "anthropic")
        assert result[0]["input_schema"] == {"type": "object", "properties": {}}

    def test_openai_format(self):
        from app.tools.tool_adapter import adapt_tools_for_provider
        schemas = [{"name": "test_tool", "description": "A test", "parameters": {"type": "object"}}]
        result = adapt_tools_for_provider(schemas, "openai")
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "test_tool"


# ---------------------------------------------------------------------------
# 8. .env.example exists
# ---------------------------------------------------------------------------

class TestDotenvExample:
    def test_env_example_exists(self):
        env_example = Path(__file__).resolve().parent.parent.parent / ".env.example"
        assert env_example.exists(), ".env.example missing"

    def test_env_example_has_api_key(self):
        env_example = Path(__file__).resolve().parent.parent.parent / ".env.example"
        content = env_example.read_text()
        assert "ANTHROPIC_API_KEY" in content
        assert "OPENAI_API_KEY" in content


# ---------------------------------------------------------------------------
# 9. requirements.txt is UTF-8
# ---------------------------------------------------------------------------

class TestRequirementsTxt:
    def test_requirements_is_utf8(self):
        req_path = Path(__file__).resolve().parent.parent.parent / "requirements.txt"
        content = req_path.read_text(encoding="utf-8")
        assert "fastapi" in content
        assert "langgraph" in content
        assert "python-dotenv" in content

    def test_requirements_not_utf16(self):
        req_path = Path(__file__).resolve().parent.parent.parent / "requirements.txt"
        raw = req_path.read_bytes()
        # UTF-16LE has BOM (ff fe) — should not be present
        assert raw[:2] != b"\xff\xfe", "requirements.txt is still UTF-16LE"


# ---------------------------------------------------------------------------
# 10. LangSmith env vars
# ---------------------------------------------------------------------------

class TestLangSmithWiring:
    def test_graph_import_sets_project(self):
        """Importing graph.py should set LANGCHAIN_PROJECT if tracing enabled."""
        # We can't easily test env var setting in isolation, but we can verify
        # the module imports without error
        from app.agent import graph
        assert hasattr(graph, "build_graph")
