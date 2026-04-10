from fastapi import APIRouter, File, Request, UploadFile, status

from app.schemas.report import ReportUploadResponse

router = APIRouter(prefix='/api/v1/reports', tags=['reports'])


@router.post('/upload', response_model=ReportUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_report(request: Request, file: UploadFile = File(...)) -> ReportUploadResponse:
    return await request.app.state.intake_service.ingest_upload(file)
