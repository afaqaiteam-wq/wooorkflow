from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]


def build_health_router() -> APIRouter:
    """Liveness probe. Carries no business logic, so it calls no use case."""
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    return router
