from fastapi import APIRouter, Request

from app.schemas.draft import ClinicianReviewPayload, ReviewResult

router = APIRouter(prefix='/api/v1/reports', tags=['reviews'])


@router.post('/{report_id}/review', response_model=ReviewResult)
def review_report(report_id: str, payload: ClinicianReviewPayload, request: Request) -> ReviewResult:
    return request.app.state.recommendation_service.apply_review(report_id, payload)
