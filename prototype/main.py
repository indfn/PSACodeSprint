# """
# PSA Code Sprint — Prototype Entry Point

# Wires the container readiness webhook (T6) into the FastAPI app.
# """

# from fastapi import FastAPI

# from pre_approval.container_readiness.webhook import (
#     router as container_readiness_router,
#     _sample_payload,
# )

# app = FastAPI(
#     title="PSA ITT Coordination Agent — Prototype",
#     description="Mock receive-container-readiness webhook (T6 / Tool 6)",
#     version="0.1.0",
# )

# app.include_router(container_readiness_router)


# @app.get("/")
# async def root():
#     return {
#         "service": "PSA ITT Coordination Agent",
#         "prototype": "pre_approval",
#         "endpoints": {
#             "POST /webhook/itt-coordination": "T6 — receive container readiness event",
#             "GET /sample-payload": "Sample ITT_COORDINATION_REQUEST for testing",
#         },
#     }


# @app.get("/sample-payload")
# async def sample_payload():
#     """Return a sample webhook payload for manual testing / demo triggers."""
#     return _sample_payload()
