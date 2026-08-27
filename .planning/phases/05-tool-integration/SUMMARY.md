# Phase 5.1 Summary — ToolResult Interface & Registry (Wave 1)

Owner: canonical ToolRegistry — single source for problem switching.

Implemented:
- app/tools/base.py — ToolResult (output/confidence/metadata), BaseTool ABC with async call wrapper (validation, timeout, metadata population)
- app/tools/registry.py — TOOLSETS x7, ToolRegistry (register/register_many/clear/list/get_schemas/get_tool/register_for_problem/call), singleton registry, FALLBACKS, load_tools_for_problem factory with lazy import + GenericStubTool
- app/tools/fallbacks.py — CachedRoadCapacityTool / CachedSeaCapacityTool (fallback_used, confidence 0.6)
- app/tests/test_registry.py — 15 tests covering register/call/list/clear/register_many/register_for_problem/hallucinated/fallback/singleton/timeout
- app/main.py — switch-problem endpoint merges registry + YAML tools for backward compat; single-source registry import

Verification:
- python -c "from app.tools.registry import ToolRegistry; r=ToolRegistry(); print(r.list())" -> []
- pytest app/tests/test_registry.py -v -> 15 passed
- pytest app/tests -v -> 72 passed
- 7 problem_ids handled; pb-12 stubs return mock ToolResults until 5.2-5.11 replace them
