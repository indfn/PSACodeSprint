"""Realistic mock container data for PPT CITOS — 120 containers across 4 yard blocks.

Based on Master Charter §3 Tool 1 sample output and PSA Pasir Panjang Terminal
operational parameters.
"""

from datetime import datetime, timedelta
import random

# Consignees realistic for Singapore transhipment
CONSIGNEES = [
    "DB Schenker", "Kuehne+Nagel", "DHL Supply Chain", "Sinotrans",
    "CMA CGM Logistics", "Maersk Logistics", "PSA Marine", "YCH Group",
    "CEVA Logistics", "Agility Logistics", "Bolloré Logistics", "Expeditors"
]

# Destination ports for feeder connections
DESTINATION_PORTS = [
    "LA", "Rotterdam", "Port Klang", "Tanjung Pelepas", "Laem Chabang",
    "Hai Phong", "Shanghai", "Busan", "Colombo", "Dubai"
]

# Yard blocks at PPT (Pasir Panjang Terminal)
YARD_BLOCKS = ["B-07", "B-08", "B-12", "B-14"]


def _generate_container_id(index: int) -> str:
    """Generate realistic container ID (4-letter prefix + 7 digits)."""
    prefixes = ["MSKU", "TCLU", "CMAU", "SEGU", "PCIU", "EISU", "KKFU", "OOLU"]
    prefix = prefixes[index % len(prefixes)]
    number = 1000000 + (index * 7919) % 9000000  # Pseudo-random 7-digit
    return f"{prefix}{number}"


def _generate_yard_position(block_num: int, index: int) -> tuple[str, str]:
    """Generate realistic bay/row/tier position within a yard block."""
    bay = (index % 20) + 1
    row = (index % 6) + 1
    tier = (index % 4) + 1
    return f"B-{block_num:02d}", f"Bay {bay:02d} Row {row:02d} Tier {tier:02d}"


def generate_containers() -> list[dict]:
    """Generate 120 containers matching Master Charter spec:
    - 40x 40ft (FEU) + 80x 20ft (TEU) = 160 TEU total
    - 3 DG containers
    - 0 reefer containers
    - Distributed across 4 yard blocks
    """
    rng = random.Random(42)  # Local RNG — no global state mutation

    containers = []
    dg_count = 0

    for i in range(120):
        size = "40ft" if i < 40 else "20ft"
        block_idx = i % 4
        yard_block, yard_position = _generate_yard_position(
            int(YARD_BLOCKS[block_idx].split("-")[1]), i
        )

        # Weight: 40ft ~18-32k kg, 20ft ~8-18k kg
        if size == "40ft":
            weight = rng.randint(18000, 32000)
        else:
            weight = rng.randint(8000, 18000)

        # DG class — only 3 containers total
        dg_class = None
        if dg_count < 3 and rng.random() < 0.05:
            dg_class = rng.choice(["3", "8"])
            dg_count += 1

        # Priority: 45 high, 75 standard
        priority = "high" if i < 45 else "standard"

        container = {
            "container_id": _generate_container_id(i),
            "size": size,
            "yard_block": yard_block,
            "yard_position": yard_position,
            "weight_kg": weight,
            "dg_class": dg_class,
            "priority": priority,
            "consignee": rng.choice(CONSIGNEES),
            "destination_port": rng.choice(DESTINATION_PORTS),
            "ready_for_itt": True,
        }
        containers.append(container)

    # Ensure exactly 3 DG containers
    while dg_count < 3:
        idx = rng.randint(0, len(containers) - 1)
        if containers[idx]["dg_class"] is None:
            containers[idx]["dg_class"] = rng.choice(["3", "8"])
            dg_count += 1

    return containers


def get_itt_candidates(vessel_id: str = "MV PACIFIC STAR") -> dict:
    """Full ITT candidates response — matches Master Charter §3 Tool 1 schema."""
    containers = generate_containers()

    fortyft = [c for c in containers if c["size"] == "40ft"]
    twentyft = [c for c in containers if c["size"] == "20ft"]
    dg = [c for c in containers if c["dg_class"] is not None]

    # Preserve insertion order (deterministic) instead of set()
    seen_blocks: set[str] = set()
    blocks_affected: list[str] = []
    for c in containers:
        if c["yard_block"] not in seen_blocks:
            seen_blocks.add(c["yard_block"])
            blocks_affected.append(c["yard_block"])

    return {
        "status": "success",
        "vessel_id": vessel_id,
        "tuas_departure": "2026-08-19T20:00:00+08:00",
        "total_containers": len(containers),
        "total_teu": len(fortyft) * 2 + len(twentyft),
        "container_breakdown": {
            "40ft_feu": len(fortyft),
            "20ft_teu": len(twentyft),
        },
        "lta_truck_trip_requirement": {
            "40ft_feu_trips": len(fortyft),  # 1x 40ft per prime mover
            "20ft_teu_trips": len(twentyft) // 2,  # 2x 20ft per prime mover
            "total_potential_truck_trips_100pct_road": len(fortyft) + len(twentyft) // 2,
        },
        "containers": containers,
        "blocks_affected": blocks_affected,
        "dg_containers": len(dg),
        "reefer_containers": 0,
    }


# Simulate data staleness for edge case testing
def get_itt_candidates_stale(vessel_id: str = "MV PACIFIC STAR", age_minutes: float = 25.0) -> dict:
    """Returns ITT candidates with a simulated data age for staleness edge case."""
    result = get_itt_candidates(vessel_id)
    result["data_timestamp"] = (
        datetime.now() - timedelta(minutes=age_minutes)
    ).isoformat()
    result["data_age_minutes"] = age_minutes
    return result


# Yard block status for yard queries
YARD_BLOCK_STATUS = {
    "B-07": {
        "block_id": "B-07",
        "capacity_teu": 4500,
        "current_occupancy_teu": 3200,
        "containers_in_block": 85,
        "status": "normal",
    },
    "B-08": {
        "block_id": "B-08",
        "capacity_teu": 4500,
        "current_occupancy_teu": 3800,
        "containers_in_block": 92,
        "status": "moderate",
    },
    "B-12": {
        "block_id": "B-12",
        "capacity_teu": 4500,
        "current_occupancy_teu": 2900,
        "containers_in_block": 71,
        "status": "normal",
    },
    "B-14": {
        "block_id": "B-14",
        "capacity_teu": 4500,
        "current_occupancy_teu": 4100,
        "containers_in_block": 103,
        "status": "high",
    },
}


def get_yard_status() -> dict:
    """Return yard block occupancy status for all affected blocks."""
    return {
        "status": "success",
        "terminal": "PPT",
        "blocks": YARD_BLOCK_STATUS,
        "last_updated": datetime.now().isoformat(),
        "data_age_minutes": 0.5,
    }
