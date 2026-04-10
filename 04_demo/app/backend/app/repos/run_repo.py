from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.core.db import RunRecord, session_scope
from app.schemas.run import RunResponse


class RunRepo:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def create_run(self, report_id: str) -> str:
        run_id = f'run_{uuid4().hex[:12]}'
        with session_scope(self.session_factory) as session:
            record = RunRecord(
                report_id=report_id,
                run_id=run_id,
                events=[],
                response_data=None,
                updated_at=datetime.now(timezone.utc),
            )
            session.merge(record)
        return run_id

    def append_event(self, report_id: str, stage: str, detail: str) -> None:
        with session_scope(self.session_factory) as session:
            record = session.get(RunRecord, report_id)
            if record is None:
                record = RunRecord(
                    report_id=report_id,
                    run_id=f'run_{uuid4().hex[:12]}',
                    events=[],
                    response_data=None,
                    updated_at=datetime.now(timezone.utc),
                )
            events = list(record.events or [])
            events.append({'stage': stage, 'detail': detail})
            record.events = events
            record.updated_at = datetime.now(timezone.utc)
            session.merge(record)

    def finalize(self, report_id: str, response: RunResponse) -> RunResponse:
        with session_scope(self.session_factory) as session:
            record = session.get(RunRecord, report_id)
            if record is None:
                record = RunRecord(
                    report_id=report_id,
                    run_id=response.run_id,
                    events=[],
                    response_data=response.model_dump(mode='json'),
                    updated_at=datetime.now(timezone.utc),
                )
            else:
                record.run_id = response.run_id
                record.response_data = response.model_dump(mode='json')
                record.updated_at = datetime.now(timezone.utc)
            session.merge(record)
        return response

    def get_run_by_report_id(self, report_id: str) -> RunResponse | None:
        with session_scope(self.session_factory) as session:
            record = session.get(RunRecord, report_id)
            if record is None or not record.response_data:
                return None
            return RunResponse.model_validate(record.response_data)

    def get_events(self, report_id: str) -> list[dict[str, str]]:
        with session_scope(self.session_factory) as session:
            record = session.get(RunRecord, report_id)
            if record is None:
                return []
            return list(record.events or [])
