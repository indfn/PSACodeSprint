"""Tool 3: check_sea_itt_capacity — Feeder Vessel & Downstream Port Query

Queries PORTNET for feeder vessel availability, berth status, departure window,
and downstream port tidal constraints (Port Klang, Tanjung Pelepas, etc.).

Correlations:
  - Receives: feeder_id + current_time (from agent ingest / webhook trigger)
  - Feeds into: compute_itt_split (Tool 4) — sea_capacity parameter
  - Integrates with: Tool 1 (ITT candidates — container count for sea allocation)
                     Tool 2 (Road ITT capacity — for split comparison)
                     Tool 5 (Tuas loading sequence — arrival coordination)
  - Triggers: esc_2 (feeder hold > 1.5 hrs), esc_6 (feeder unresponsive > 15 min)

Master Charter ref: Section 3, Tool 3
Tech Stack ref: Section 8, YAML config (tools.check_sea_itt_capacity)
"""
from .sea_itt_tools import check_sea_itt_capacity

__all__ = [
    "check_sea_itt_capacity"
]