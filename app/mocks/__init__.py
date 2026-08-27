"""Mocks package — exposes consolidated mock routers."""

from app.mocks.routers.citos_ppt import router as citos_ppt_router
from app.mocks.routers.citos_tuas import router as citos_tuas_router
from app.mocks.routers.optetruck import router as optetruck_router
from app.mocks.routers.feeder import router as feeder_router
from app.mocks.routers.portnet import router as portnet_router

__all__ = [
    "citos_ppt_router",
    "citos_tuas_router",
    "optetruck_router",
    "feeder_router",
    "portnet_router",
]
