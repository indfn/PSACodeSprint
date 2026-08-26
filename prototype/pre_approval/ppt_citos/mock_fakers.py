"""Container generation logic for PPT CITOS mock data.

Procedurally generates containers based on parameters from ppt_citos_params.yaml
and reference data from mock_data.yaml.
"""

from __future__ import annotations

import random
from typing import Any

from prototype.configs import load_config
from prototype.shared.utils.yaml_reader import load_yaml
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parent
_MOCK_DATA = load_yaml(_MODULE_DIR / "mock_data.yaml")

_PARAMS = load_config("ppt_citos_params.yaml")

# Aliases for readability
_GEN = _PARAMS["generation"]
_WEIGHT = _PARAMS["weight_ranges"]
_DG_CLASSES = _PARAMS["dg_classes"]
_PREFIXES = _MOCK_DATA["container_id_prefixes"]
_CONSIGNEES = _MOCK_DATA["consignees"]
_DEST_PORTS = _MOCK_DATA["destination_ports"]
_YARD_BLOCKS = _MOCK_DATA["yard_blocks"]


def _generate_container_id(index: int) -> str:
    """Generate realistic container ID (4-letter prefix + 7 digits)."""
    prefix = _PREFIXES[index % len(_PREFIXES)]
    number = 1000000 + (index * 7919) % 9000000
    return f"{prefix}{number}"


def _generate_yard_position(block_num: int, index: int) -> tuple[str, str]:
    """Generate realistic bay/row/tier position within a yard block."""
    bay = (index % 20) + 1
    row = (index % 6) + 1
    tier = (index % 4) + 1
    return f"B-{block_num:02d}", f"Bay {bay:02d} Row {row:02d} Tier {tier:02d}"


def generate_containers() -> list[dict[str, Any]]:
    """Generate containers matching Master Charter spec.

    Counts and distribution are driven by ppt_citos_params.yaml.
    Reference data (consignees, ports, blocks) from mock_data.yaml.
    """
    rng = random.Random(_GEN["seed"])

    containers = []
    dg_count = 0

    for i in range(_GEN["total_containers"]):
        size = "40ft" if i < _GEN["fortyft_count"] else "20ft"
        block_idx = i % len(_YARD_BLOCKS)
        block_num = int(_YARD_BLOCKS[block_idx].split("-")[1])
        yard_block, yard_position = _generate_yard_position(block_num, i)

        if size == "40ft":
            weight = rng.randint(_WEIGHT["fortyft_min_kg"], _WEIGHT["fortyft_max_kg"])
        else:
            weight = rng.randint(_WEIGHT["twentyft_min_kg"], _WEIGHT["twentyft_max_kg"])

        dg_class = None
        if dg_count < _GEN["dg_container_count"] and rng.random() < 0.05:
            dg_class = rng.choice(_DG_CLASSES)
            dg_count += 1

        priority = "high" if i < _GEN["high_priority_count"] else "standard"

        container = {
            "container_id": _generate_container_id(i),
            "size": size,
            "yard_block": yard_block,
            "yard_position": yard_position,
            "weight_kg": weight,
            "dg_class": dg_class,
            "priority": priority,
            "consignee": rng.choice(_CONSIGNEES),
            "destination_port": rng.choice(_DEST_PORTS),
            "ready_for_itt": True,
        }
        containers.append(container)

    while dg_count < _GEN["dg_container_count"]:
        idx = rng.randint(0, len(containers) - 1)
        if containers[idx]["dg_class"] is None:
            containers[idx]["dg_class"] = rng.choice(_DG_CLASSES)
            dg_count += 1

    return containers
