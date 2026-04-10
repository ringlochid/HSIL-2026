from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.schemas.report import ExtractedCase, ReportUploadResponse, UploadedReport


class IntakeService:
    def __init__(self, settings, reports_repo, report_pdf_tool, extraction_chain) -> None:
        self.settings = settings
        self.reports_repo = reports_repo
        self.report_pdf_tool = report_pdf_tool
        self.extraction_chain = extraction_chain

    async def ingest_upload(self, upload: UploadFile) -> ReportUploadResponse:
        filename = upload.filename or 'report.pdf'
        if not filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail='Only PDF uploads are supported.')

        content = await upload.read()
        size_limit = self.settings.max_upload_mb * 1024 * 1024
        if len(content) > size_limit:
            raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail='Uploaded file exceeds configured size limit.')

        report_id = f'report_{uuid4().hex[:12]}'
        file_path = self.settings.upload_dir / f'{report_id}.pdf'
        file_path.write_bytes(content)

        pdf_result = self.report_pdf_tool.extract(file_path)
        if self.extraction_chain is None:
            extracted_payload = ExtractedCase.model_validate_json(
                (self.settings.fixtures_root / 'reports' / 'ravi_extracted.json').read_text()
            ).model_dump(mode='json')
        else:
            extracted_payload = self.extraction_chain.invoke({
                'filename': filename,
                'report_text': pdf_result.get('text', ''),
            })
        extracted_case = ExtractedCase.model_validate(extracted_payload)
        warnings = list(pdf_result.get('warnings', []))
        extraction_status = 'degraded' if warnings else 'completed'

        report = UploadedReport(
            report_id=report_id,
            filename=filename,
            content_type=upload.content_type or 'application/pdf',
            size_bytes=len(content),
            created_at=datetime.now(timezone.utc),
            extraction_status=extraction_status,
            extracted_case=extracted_case,
            extraction_warnings=warnings,
        )
        self.reports_repo.save(report)
        return ReportUploadResponse(report=report)
