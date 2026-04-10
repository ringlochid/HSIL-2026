from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.draft import DraftPayload


class RunStatus(str, Enum):
    completed = 'completed'
    degraded = 'degraded'
    blocked = 'blocked'


class RunRequest(BaseModel):
    force_refresh: bool = False


class BatchRunRequest(BaseModel):
    report_ids: list[str] = Field(min_length=1)
    mode: Literal['independent'] = 'independent'
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
    batch_id: str | None = None
    status: RunStatus
    draft: DraftPayload
    evidence: list[EvidenceSourceSummary] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class BatchRunResponse(BaseModel):
    batch_id: str
    mode: Literal['independent']
    results: list[RunResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FinalizeResponse(BaseModel):
    run_id: str
    report_id: str
    status: Literal['finalized'] = 'finalized'
    filename: str
    download_path: str
