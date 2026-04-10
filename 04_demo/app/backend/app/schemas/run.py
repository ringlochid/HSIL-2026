from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.draft import DraftPayload


class RunStatus(str, Enum):
    completed = 'completed'
    degraded = 'degraded'


class RunRequest(BaseModel):
    force_refresh: bool = False


class EvidenceSourceSummary(BaseModel):
    source: str
    status: str
    request_identity: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class RunResponse(BaseModel):
    run_id: str
    report_id: str
    status: RunStatus
    draft: DraftPayload
    evidence: list[EvidenceSourceSummary] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
