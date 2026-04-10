from fastapi import APIRouter, Body, Request

from app.schemas.run import RunRequest, RunResponse

router = APIRouter(prefix='/api/v1/reports', tags=['runs'])


@router.post('/{report_id}/run', response_model=RunResponse)
def run_report(report_id: str, request: Request, payload: RunRequest | None = Body(default=None)) -> RunResponse:
    return request.app.state.workflow_service.run_report(report_id, payload or RunRequest())
