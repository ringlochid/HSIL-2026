from __future__ import annotations

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
    reviewer_notes: str | None = None
    recommendation: str | None = None
    evidence_summary: str | None = None
    uncertainty: str | None = None
    next_step: str | None = None
    approve: bool = True


class ReviewResult(BaseModel):
    run_id: str
    report_id: str
    status: Literal['reviewed'] = 'reviewed'
    reviewed_draft: DraftPayload
    reviewer_name: str | None = None
    reviewer_notes: str | None = None
