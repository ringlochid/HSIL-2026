from fastapi import APIRouter, Body, Request
from fastapi.responses import FileResponse

from app.schemas.run import BatchRunRequest, BatchRunResponse, FinalizeResponse, RunRequest, RunResponse

router = APIRouter(prefix='/api/v1', tags=['runs'])


@router.post('/reports/{report_id}/run', response_model=RunResponse)
def run_report(report_id: str, request: Request, payload: RunRequest | None = Body(default=None)) -> RunResponse:
    return request.app.state.workflow_service.run_report(report_id, payload or RunRequest())


@router.post('/runs/batch', response_model=BatchRunResponse)
def run_batch(request: Request, payload: BatchRunRequest) -> BatchRunResponse:
    return request.app.state.workflow_service.run_batch(payload)


@router.post('/runs/{run_id}/finalize', response_model=FinalizeResponse)
def finalize_run(run_id: str, request: Request) -> FinalizeResponse:
    return request.app.state.final_report_service.finalize_run(run_id)


@router.get('/runs/{run_id}/final.pdf')
def get_final_pdf(run_id: str, request: Request) -> FileResponse:
    pdf_path = request.app.state.final_report_service.get_final_pdf_path(run_id)
    return FileResponse(path=pdf_path, media_type='application/pdf', filename=pdf_path.name)
