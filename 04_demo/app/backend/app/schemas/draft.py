from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class DraftPayload(BaseModel):
    case_title: str
    recommendation: str
    evidence_summary: str
    uncertainty: str
    next_step: str


class ClinicianReviewPayload(BaseModel):
    reviewer_name: str | None = None
    review_note: str


class RunDropPayload(BaseModel):
    review_note: str | None = None


class ReviewResult(BaseModel):
    run_id: str
    review_status: Literal['reviewed'] = 'reviewed'
    review_note: str
    reviewed_at: datetime


class ApproveResult(BaseModel):
    run_id: str
    review_status: Literal['approved'] = 'approved'
    review_note: str | None = None
    reviewed_at: datetime | None = None
    download_path: str


class DropResult(BaseModel):
    run_id: str
    review_status: Literal['dropped'] = 'dropped'
    review_note: str | None = None
    reviewed_at: datetime | None = None
