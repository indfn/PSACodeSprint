"""ProblemConfig loader — validates and parses YAML configs for all 7 C2 problems.

Usage:
    from app.configs.problem_config import load_problem_config
    cfg = load_problem_config("pb-12-itt")
    print(cfg.systems, cfg.tools)

Supports both 'pb-12-itt' and 'pb-12' style IDs (normalises to file lookup).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parent
LLM_CONFIG_PATH = CONFIG_DIR / "llm.yaml"


def discover_problems() -> dict[str, ProblemInfo]:
    """Scan configs/ for all pb-*.yaml files and return ProblemInfo for each.

    Excludes llm.yaml. Returns dict mapping problem_id (file stem) -> ProblemInfo.
    Works with any YAML that has a 'problem' block with name/sector/description.
    Uses file stem as the canonical problem_id (e.g., pb-12-itt), not the YAML id field.
    """
    problems: dict[str, ProblemInfo] = {}
    for yaml_path in sorted(CONFIG_DIR.glob("pb-*.yaml")):
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f) or {}
            pinfo = data.get("problem", {})
            if not pinfo:
                continue
            # Use file stem as canonical ID (e.g., pb-12-itt), not YAML id field
            pid = yaml_path.stem.lower()
            problems[pid] = ProblemInfo(
                id=pid,
                name=str(pinfo.get("name", pid)),
                sector=str(pinfo.get("sector", "")),
                description=str(pinfo.get("description", "")),
            )
        except Exception:
            continue
    return problems


def get_tool_names_for_problem(problem_id: str) -> list[str]:
    """Read tool names directly from a problem's YAML tools section.

    Returns list of tool names. Works with any YAML that has a 'tools' list.
    Filters out tools with type: event_trigger (not callable tools).
    """
    try:
        yaml_path = _find_yaml(problem_id)
    except FileNotFoundError:
        return []
    with open(yaml_path) as f:
        data = yaml.safe_load(f) or {}
    tools = data.get("tools", [])
    return [t.get("name", "") for t in tools if t.get("name") and t.get("type") != "event_trigger"]


def _load_global_llm_config() -> dict[str, Any]:
    """Load global LLM config from llm.yaml.

    Returns empty dict if file not found (caller applies defaults).
    """
    if not LLM_CONFIG_PATH.exists():
        return {}
    with open(LLM_CONFIG_PATH) as f:
        data = yaml.safe_load(f) or {}
    return dict(data)


@dataclass
class ProblemInfo:
    id: str
    name: str
    sector: str
    description: str


@dataclass
class SystemConfig:
    name: str
    type: str
    capabilities: list[str] = field(default_factory=list)
    # optional PSA fields
    data_freshness_max_min: int | None = None
    response_timeout_min: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolConfig:
    name: str
    systems: list[str] = field(default_factory=list)
    tool_id: str = ""
    type: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class HITLGate:
    gate_id: str
    trigger: str
    action: str
    label: str
    timeout_minutes: int = 30
    timeout_action: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class EscalationTrigger:
    trigger_id: str
    name: str
    condition: str
    threshold: Any = None


@dataclass
class ConfidenceConfig:
    enabled: bool = True
    threshold: float = 0.85
    method: str = "llm_self_assessment"


@dataclass
class EdgeCase:
    case_id: str
    name: str
    inject_at_step: int | None = None
    description: str = ""
    agent_response: str = ""


@dataclass
class ProblemConfig:
    problem: ProblemInfo
    llm: dict[str, Any]
    systems: list[SystemConfig]
    tools: list[ToolConfig]
    hitl_gates: list[HITLGate]
    escalation_triggers: list[EscalationTrigger]
    confidence: ConfidenceConfig
    cost_params: dict[str, Any]
    constraints: dict[str, Any]
    edge_cases: list[EdgeCase]
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.problem.id

    @property
    def name(self) -> str:
        return self.problem.name


def _find_yaml(problem_id: str) -> Path:
    """Locate YAML file for a problem_id.

    Tries:
      1. {problem_id}.yaml (exact, lowercased)
      2. Canonical stem match: pb-XX prefix matches pb-XX-*.yaml
    Raises FileNotFoundError with list of available configs on miss.
    """
    pid = problem_id.lower().strip()
    # 1. exact
    candidate = CONFIG_DIR / f"{pid}.yaml"
    if candidate.exists():
        return candidate
    candidate2 = CONFIG_DIR / f"{problem_id}.yaml"
    if candidate2.exists():
        return candidate2
    # 2. canonical stem match: pb-12 matches pb-12-itt.yaml
    parts = pid.split("-")
    if len(parts) >= 2:
        prefix = f"{parts[0]}-{parts[1]}"
        for p in CONFIG_DIR.glob("pb-*.yaml"):
            stem_parts = p.stem.lower().split("-")
            if len(stem_parts) >= 2 and f"{stem_parts[0]}-{stem_parts[1]}" == prefix:
                return p
    # List available configs for helpful error
    available = sorted(p.stem for p in CONFIG_DIR.glob("pb-*.yaml"))
    raise FileNotFoundError(
        f"No YAML config found for problem_id '{problem_id}' in {CONFIG_DIR}. "
        f"Available: {available}"
    )


def load_problem_config(problem_id: str) -> ProblemConfig:
    """Load and validate a problem YAML into a ProblemConfig.

    Validates required top-level fields: problem, systems, tools.
    Applies sensible defaults for optional fields (confidence, escalation_triggers, etc.)
    so sibling configs that are currently incomplete still load.

    Args:
        problem_id: e.g. 'pb-12-itt' or 'pb-12' or 'PB-12'

    Returns:
        ProblemConfig dataclass.

    Raises:
        FileNotFoundError: if YAML not found.
        ValueError: if required fields missing.
    """
    yaml_path = _find_yaml(problem_id)
    with open(yaml_path) as f:
        data = yaml.safe_load(f) or {}

    # --- validate required top-level ---
    if "problem" not in data:
        raise ValueError(f"{yaml_path}: missing 'problem' block")
    if "systems" not in data or not data["systems"]:
        raise ValueError(f"{yaml_path}: missing 'systems'")
    if "tools" not in data or not data["tools"]:
        raise ValueError(f"{yaml_path}: missing 'tools'")

    # --- problem info ---
    pinfo_raw = data["problem"]
    problem = ProblemInfo(
        id=str(pinfo_raw.get("id", problem_id)),
        name=str(pinfo_raw.get("name", "")),
        sector=str(pinfo_raw.get("sector", "")),
        description=str(pinfo_raw.get("description", "")),
    )

    # --- systems ---
    systems: list[SystemConfig] = []
    for s in data.get("systems", []):
        systems.append(SystemConfig(
            name=s.get("name", ""),
            type=s.get("type", ""),
            capabilities=list(s.get("capabilities", [])),
            data_freshness_max_min=s.get("data_freshness_max_min"),
            response_timeout_min=s.get("response_timeout_min"),
            extra={k: v for k, v in s.items() if k not in ("name", "type", "capabilities", "data_freshness_max_min", "response_timeout_min")},
        ))

    # --- tools ---
    tools: list[ToolConfig] = []
    for t in data.get("tools", []):
        tools.append(ToolConfig(
            name=t.get("name", ""),
            systems=list(t.get("systems", [])),
            tool_id=str(t.get("tool_id", "")),
            type=t.get("type"),
            extra={k: v for k, v in t.items() if k not in ("name", "systems", "tool_id", "type")},
        ))

    # --- hitl_gates ---
    hitl_gates: list[HITLGate] = []
    for g in data.get("hitl_gates", []):
        hitl_gates.append(HITLGate(
            gate_id=g.get("gate_id", ""),
            trigger=g.get("trigger", ""),
            action=g.get("action", ""),
            label=g.get("label", g.get("gate_id", "")),
            timeout_minutes=int(g.get("timeout_minutes", 30)),
            timeout_action=g.get("timeout_action"),
            extra={k: v for k, v in g.items() if k not in ("gate_id", "trigger", "action", "label", "timeout_minutes", "timeout_action")},
        ))

    # --- escalation_triggers (optional, default empty) ---
    escalation_triggers: list[EscalationTrigger] = []
    for e in data.get("escalation_triggers", []) or []:
        escalation_triggers.append(EscalationTrigger(
            trigger_id=e.get("trigger_id", ""),
            name=e.get("name", ""),
            condition=e.get("condition", ""),
            threshold=e.get("threshold"),
        ))

    # --- confidence (optional) ---
    conf_raw = data.get("confidence", {}) or {}
    confidence = ConfidenceConfig(
        enabled=bool(conf_raw.get("enabled", True)),
        threshold=float(conf_raw.get("threshold", 0.85)),
        method=str(conf_raw.get("method", "llm_self_assessment")),
    )

    # --- cost_params, constraints, edge_cases (optional) ---
    cost_params = dict(data.get("cost_params", {}) or {})
    constraints = dict(data.get("constraints", {}) or {})
    edge_cases: list[EdgeCase] = []
    for ec in data.get("edge_cases", []) or []:
        edge_cases.append(EdgeCase(
            case_id=ec.get("case_id", ""),
            name=ec.get("name", ""),
            inject_at_step=ec.get("inject_at_step"),
            description=ec.get("description", ""),
            agent_response=ec.get("agent_response", ""),
        ))

    # --- llm: merge global llm.yaml with per-problem override ---
    llm = _load_global_llm_config()
    problem_llm = dict(data.get("llm", {}) or {})
    if problem_llm:
        # Per-problem override (opt-in: only if problem YAML defines llm:)
        llm.update(problem_llm)

    return ProblemConfig(
        problem=problem,
        llm=llm,
        systems=systems,
        tools=tools,
        hitl_gates=hitl_gates,
        escalation_triggers=escalation_triggers,
        confidence=confidence,
        cost_params=cost_params,
        constraints=constraints,
        edge_cases=edge_cases,
        raw=data,
    )
