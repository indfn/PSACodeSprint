"""Standalone FastAPI app for Sea ITT / PORTNET mock API.

Run:
    uvicorn pre_approval.sea_itt.app:app --reload --port 8003

Endpoints:
    POST /portnet/sea-itt/capacity     — Tool 3: Query feeder capacity & tidal constraints
    GET  /portnet/feeder/{feeder_id}   — Feeder status check (monitoring)
    POST /portnet/feeder/hold          — Request feeder hold at berth
    GET  /portnet/feeders              — List available feeders
    GET  /portnet/downstream/{port}    — Query downstream port tidal window
    POST /portnet/sea-itt/conflict     — Edge case: berth conflict simulation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import router

app = FastAPI(
    title="PORTNET Sea ITT Mock API",
    description="Feeder vessel availability and downstream port constraints — Mock for PSA Code Sprint",
    version="0.1.0",
)

# NOTE: Wildcard CORS for demo/mock only. Restrict origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "PORTNET Sea ITT Mock API",
        "description": "Feeder vessel capacity and downstream port tidal constraints",
        "version": "0.1.0",
        "endpoints": {
            "sea_itt_capacity": "POST /portnet/sea-itt/capacity",
            "feeder_status": "GET  /portnet/feeder/{feeder_id}",
            "feeder_hold": "POST /portnet/feeder/hold",
            "list_feeders": "GET  /portnet/feeders",
            "downstream_port": "GET  /portnet/downstream/{port_name}",
            "berth_conflict": "POST /portnet/sea-itt/conflict",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "portnet-sea-itt"}
