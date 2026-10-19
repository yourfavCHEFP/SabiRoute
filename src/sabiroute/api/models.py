from __future__ import annotations

from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    policy: str = Field(default="ultimate")
    candidates: list[str] = Field(default_factory=list)


class RouteResponse(BaseModel):
    policy: str
    deployment: str
    attempt: int


class HealthResponse(BaseModel):
    status: str
    service: str
