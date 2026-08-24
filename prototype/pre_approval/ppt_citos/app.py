"""Standalone FastAPI app for PPT CITOS mock API.

Run:
    uvicorn pre_approval.ppt_citos.app:app --reload --port 8001

Endpoints:
    POST /citos/ppt/itt-candidates     — Tool 1: Query containers ready for ITT
    GET  /citos/ppt/yard-status        — Yard block occupancy status
    POST /citos/ppt/webhook/itt-coordination — T6: Webhook event trigger
    POST /citos/ppt/itt-candidates-stale     — Edge case: stale data simulation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import router

app = FastAPI(
    title="PPT CITOS Mock API",
    description="Pasir Panjang Terminal Container Operating System — Mock for PSA Code Sprint",
    version="0.1.0",
)

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
        "service": "PPT CITOS Mock API",
        "terminal": "Pasir Panjang Terminal (PPT)",
        "version": "0.1.0",
        "endpoints": {
            "itt_candidates": "POST /citos/ppt/itt-candidates",
            "yard_status": "GET /citos/ppt/yard-status",
            "webhook": "POST /citos/ppt/webhook/itt-coordination",
            "itt_candidates_stale": "POST /citos/ppt/itt-candidates-stale",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ppt-citos"}
