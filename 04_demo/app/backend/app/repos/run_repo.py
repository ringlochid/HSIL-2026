from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import desc, select

from app.core.db import RunRecord, session_scope
from app.schemas.draft import ReviewResult
from app.schemas.run import RunResponse


class RunRepo:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def create_run(self, report_id: str, batch_id: str | None = None) -> str:
        run_id = f'run_{uuid4().hex[:12]}'
        with session_scope(self.session_factory) as session:
            record = RunRecord(
                run_id=run_id,
                report_id=report_id,
                batch_id=batch_id,
                status='completed',
                events=[],
                response_data=None,
                review_data=None,
                final_pdf_path=None,
                updated_at=datetime.now(timezone.utc),
            )
            session.add(record)
        return run_id

    def append_event(self, run_id: str, stage: str, detail: str) -> None:
        with session_scope(self.session_factory) as session:
            record = session.get(RunRecord, run_id)
            if record is None:
                raise KeyError(run_id)
            events = list(record.events or [])
            events.append({'stage': stage, 'detail': detail})
            record.events = events
            record.updated_at = datetime.now(timezone.utc)
            session.add(record)

    def finalize(self, run_id: str, response: RunResponse) -> RunResponse:
        with session_scope(self.session_factory) as session:
            record = session.get(RunRecord, run_id)
            if record is None:
                raise KeyError(run_id)
            record.status = response.status.value if hasattr(response.status, 'value') else str(response.status)
            record.response_data = response.model_dump(mode='json')
            record.updated_at = datetime.now(timezone.utc)
            session.add(record)
        return response

    def get_run(self, run_id: str) -> RunResponse | None:
        with session_scope(self.session_factory) as session:
            record = session.get(RunRecord, run_id)
            if record is None or not record.response_data:
                return None
            return RunResponse.model_validate(record.response_data)

    def get_latest_run_by_report_id(self, report_id: str) -> RunResponse | None:
        with session_scope(self.session_factory) as session:
            stmt = (
                select(RunRecord)
                .where(RunRecord.report_id == report_id, RunRecord.response_data.is_not(None))
                .order_by(desc(RunRecord.updated_at))
                .limit(1)
            )
            record = session.execute(stmt).scalar_one_or_none()
            if record is None:
                return None
            return RunResponse.model_validate(record.response_data)

    def save_review(self, run_id: str, review: ReviewResult) -> ReviewResult:
        with session_scope(self.session_factory) as session:
            record = session.get(RunRecord, run_id)
            if record is None:
                raise KeyError(run_id)
            record.review_data = review.model_dump(mode='json')
            record.updated_at = datetime.now(timezone.utc)
            session.add(record)
        return review

    def get_review(self, run_id: str) -> ReviewResult | None:
        with session_scope(self.session_factory) as session:
            record = session.get(RunRecord, run_id)
            if record is None or not record.review_data:
                return None
            return ReviewResult.model_validate(record.review_data)

    def save_final_pdf_path(self, run_id: str, final_pdf_path: str) -> str:
        with session_scope(self.session_factory) as session:
            record = session.get(RunRecord, run_id)
            if record is None:
                raise KeyError(run_id)
            record.final_pdf_path = final_pdf_path
            record.updated_at = datetime.now(timezone.utc)
            session.add(record)
        return final_pdf_path

    def get_final_pdf_path(self, run_id: str) -> str | None:
        with session_scope(self.session_factory) as session:
            record = session.get(RunRecord, run_id)
            if record is None:
                return None
            return record.final_pdf_path
