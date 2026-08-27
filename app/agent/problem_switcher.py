"""Problem switching — runtime config reload for PSA Nexus platform.

Consumer of app/tools/registry.py (owned by Phase 5.1) — do NOT redefine registry here.
This module only loads ProblemConfig and updates the active problem id.
Tool re-registration is delegated to registry if available, otherwise no-op.
"""

from __future__ import annotations

from pathlib import Path

from app.configs.problem_config import ProblemConfig, load_problem_config

CONFIG_DIR = Path(__file__).resolve().parent.parent / "configs"

# Canonical file stems for all 7 problems
CANONICAL_STEMS = {
    "pb-01": "pb-01-berth",
    "pb-02": "pb-02-dtqc",
    "pb-04": "pb-04-feeder",
    "pb-09": "pb-09-expressway",
    "pb-10": "pb-10-sea-air",
    "pb-11": "pb-11-customs",
    "pb-12": "pb-12-itt",
}

_active_problem_id: str = "pb-12-itt"


def _resolve_stem(problem_id: str) -> str:
    pid = problem_id.lower().strip()
    # Exact file exists?
    if (CONFIG_DIR / f"{pid}.yaml").exists():
        return pid
    # Short form like pb-12 -> pb-12-itt
    if pid in CANONICAL_STEMS:
        return CANONICAL_STEMS[pid]
    # Try prefix match: pb-12 matches pb-12-itt
    for stem in CANONICAL_STEMS.values():
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
