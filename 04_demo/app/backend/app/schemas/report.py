from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ExtractionIssue(BaseModel):
    code: str
    message: str
    severity: Literal['info', 'warning', 'error'] = 'warning'


class ExtractedVariant(BaseModel):
    gene: str
    transcript_hgvs: str
    protein_change: str
    genomic_hg38: str
    variation_type: str
    consequence: str


class ExtractedCase(BaseModel):
    case_label: str
    report_title: str
    summary: str
    genome_build: str = 'GRCh38'
    variants: list[ExtractedVariant] = Field(default_factory=list)
    issues: list[ExtractionIssue] = Field(default_factory=list)


class UploadedReport(BaseModel):
    report_id: str
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
    extraction_status: Literal['completed', 'degraded']
    extracted_case: ExtractedCase
    extraction_warnings: list[str] = Field(default_factory=list)


class ReportUploadResponse(BaseModel):
    report: UploadedReport
