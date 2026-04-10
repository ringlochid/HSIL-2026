from __future__ import annotations

from fastapi import HTTPException, status

from app.schemas.draft import ClinicianReviewPayload, DraftPayload, ReviewResult


class RecommendationService:
    def __init__(self, reports_repo, run_repo) -> None:
        self.reports_repo = reports_repo
        self.run_repo = run_repo

    def apply_review(self, report_id: str, payload: ClinicianReviewPayload) -> ReviewResult:
        latest_run = self.run_repo.get_latest_run_by_report_id(report_id)
        if latest_run is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='No generated draft exists for this report yet.')
        return self.apply_review_to_run(latest_run.run_id, payload)

    def apply_review_to_run(self, run_id: str, payload: ClinicianReviewPayload) -> ReviewResult:
        run = self.run_repo.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Run not found.')
        if run.status == 'blocked':
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Blocked runs cannot be reviewed until extraction is available.')

        merged = run.draft.model_copy(update={
            'recommendation': payload.recommendation or run.draft.recommendation,
            'evidence_summary': payload.evidence_summary or run.draft.evidence_summary,
            'uncertainty': payload.uncertainty or run.draft.uncertainty,
            'next_step': payload.next_step or run.draft.next_step,
        })
        self._validate_required_fields(merged)
        review = ReviewResult(
            run_id=run.run_id,
            report_id=run.report_id,
            reviewed_draft=merged,
            reviewer_name=payload.reviewer_name,
            reviewer_notes=payload.reviewer_notes,
        )
        self.run_repo.save_review(run_id, review)
        return review

    @staticmethod
    def _validate_required_fields(draft: DraftPayload) -> None:
        for field_name in ('recommendation', 'evidence_summary', 'uncertainty', 'next_step'):
            if not getattr(draft, field_name).strip():
                raise HTTPException(status_code=422, detail=f'{field_name} cannot be empty after review merge.')
