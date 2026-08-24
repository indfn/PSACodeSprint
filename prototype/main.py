"""PSA Mock API Server — serves all 5 mock PSA systems on port 8000.

Run: uvicorn prototype.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from prototype.mocks.citos_ppt import router as citos_ppt_router
from prototype.mocks.citos_tuas import router as citos_tuas_router
from prototype.mocks.optetruck import router as optetruck_router
from prototype.mocks.feeder import router as feeder_router
from prototype.mocks.portnet import router as portnet_router
from prototype.mocks.webhook import router as webhook_router

app = FastAPI(
    title="PSA Mock API Server",
    description="Mock APIs for PSA Code Sprint — CITOS, OptETruck, Feeder, PORTNET",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all mock system routers
app.include_router(citos_ppt_router)
app.include_router(citos_tuas_router)
app.include_router(optetruck_router)
app.include_router(feeder_router)
app.include_router(portnet_router)
app.include_router(webhook_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "psa-mock-api"}
