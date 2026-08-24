# PPT CITOS Mock API

Pasir Panjang Terminal Container Operating System — mock implementation for PSA Code Sprint prototype.

## Quick Start

```bash
cd /Users/varun/Documents/PSACodeSprint/prototype
pip install -r ppt_citos/requirements.txt
uvicorn ppt_citos.app:app --reload --port 8001
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/citos/ppt/itt-candidates` | Tool 1: Query containers ready for ITT transfer |
| `GET` | `/citos/ppt/yard-status` | Yard block occupancy status |
| `POST` | `/citos/ppt/webhook/itt-coordination` | T6: Webhook event trigger |
| `POST` | `/citos/ppt/itt-candidates-stale` | Edge case: stale data simulation |
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |

## Example: Query ITT Candidates

```bash
curl -X POST http://localhost:8001/citos/ppt/itt-candidates \
  -H "Content-Type: application/json" \
  -d '{"cit_ppt_endpoint": "CITOS_PPT", "vessel_id": "MV PACIFIC STAR"}'
```

Returns 120 containers (40x 40ft + 80x 20ft = 160 TEU) across 4 yard blocks.

## Example: Webhook Trigger (T6)

```bash
curl -X POST http://localhost:8001/citos/ppt/webhook/itt-coordination \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "ITT_COORDINATION_REQUEST",
    "timestamp": "2026-08-19T10:30:00+08:00",
    "source": "CITOS_PPT",
    "priority": "high",
    "origin_terminal": "PPT",
    "destination_terminal": "TUAS",
    "vessel_id": "MV PACIFIC STAR",
    "tuas_vessel_departure": "2026-08-19T20:00:00+08:00",
    "container_count": 120,
    "containers_ready": 120,
    "blocks_affected": ["B-07", "B-08", "B-12", "B-14"],
    "dg_containers": 3,
    "priority_containers": 45,
    "requested_by": "PPT_Yard_Planner_Lim",
    "notes": "Priority transhipment for MV PACIFIC STAR"
  }'
```

## Mock Data

- **120 containers**: 40x 40ft (FEU) + 80x 20ft (TEU) = 160 TEU
- **3 DG containers** (classes 3 and 8)
- **4 yard blocks**: B-07, B-08, B-12, B-14
- **Consignees**: DB Schenker, Kuehne+Nagel, DHL, Sinotrans, etc.
- **Destination ports**: LA, Rotterdam, Port Klang, Tanjung Pelepas, etc.

## Interactive Docs

Visit http://localhost:8001/docs for Swagger UI.
