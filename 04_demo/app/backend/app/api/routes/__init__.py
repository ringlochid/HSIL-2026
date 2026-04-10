from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.reports import router as reports_router
from app.api.routes.runs import router as runs_router


def build_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(reports_router)
    router.include_router(runs_router)
    router.include_router(health_router)
    return router
