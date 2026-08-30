"""Problem switching — runtime config reload for PSA Nexus platform.

Consumer of app/tools/registry.py (owned by Phase 5.1) — do NOT redefine registry here.
This module only loads ProblemConfig and updates the active problem id.
Tool re-registration is delegated to registry if available, otherwise no-op.
"""

from __future__ import annotations

from pathlib import Path

from app.configs.problem_config import ProblemConfig, load_problem_config, discover_problems

CONFIG_DIR = Path(__file__).resolve().parent.parent / "configs"

_active_problem_id: str = "pb-12-itt"


def _discover_canonical_stems() -> dict[str, str]:
    """Dynamically discover all problem stems from YAML files."""
    problems = discover_problems()
    stems = {}
    for pid in problems:
        # Map short form (pb-12) to full form (pb-12-itt)
        parts = pid.split("-")
        if len(parts) >= 2:
            short = f"{parts[0]}-{parts[1]}"
            stems[short] = pid
        stems[pid] = pid
    return stems


def _resolve_stem(problem_id: str) -> str:
    pid = problem_id.lower().strip()
    # Exact file exists?
    if (CONFIG_DIR / f"{pid}.yaml").exists():
        return pid
    # Dynamic discovery
    stems = _discover_canonical_stems()
    # Short form like pb-12 -> pb-12-itt
    if pid in stems:
        return stems[pid]
    # Try prefix match
    for stem in stems.values():
        if stem.startswith(pid) or pid.startswith(stem):
            return stem
    for p in CONFIG_DIR.glob("pb-*.yaml"):
        if p.stem.lower() == pid:
            return p.stem.lower()
        if p.stem.lower().startswith(pid):
            return p.stem.lower()
    return pid


def switch_problem(problem_id: str) -> ProblemConfig:
    """Load a new ProblemConfig and update the active problem id.

    Validates that the config has at least systems, tools, and hitl_gates.
    """
    global _active_problem_id
    config = load_problem_config(problem_id)
    assert config.systems, f"{problem_id}: missing systems"
    assert config.tools, f"{problem_id}: missing tools"
    assert config.hitl_gates, f"{problem_id}: missing hitl_gates"
    _active_problem_id = _resolve_stem(problem_id)
    return config


def get_active_problem_id() -> str:
    """Return the currently active problem id (file stem, e.g. pb-12-itt)."""
    return _active_problem_id


def get_active_config() -> ProblemConfig:
    """Load the currently active ProblemConfig."""
    return load_problem_config(_active_problem_id)
