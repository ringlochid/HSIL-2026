from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


pytestmark = pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY'),
    reason='OPENAI_API_KEY not configured',
)


def test_real_agent_run_is_not_blocked_when_openai_available() -> None:
    settings = Settings(
        upload_dir=Path('/tmp') / 'hsil_real_uploads',
        final_report_dir=Path('/tmp') / 'hsil_real_final_reports',
        database_url='sqlite+pysqlite:////tmp/hsil_real_agent.db',
        llm_provider='openai',
        use_real_apis=True,
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        max_upload_mb=20,
        debug=True,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        upload = client.post(
            '/api/v1/reports/upload',
            files={'file': ('real-agent.pdf', b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n', 'application/pdf')},
            data={'report_kind': 'patient'},
        )
        assert upload.status_code == 201
        report_id = upload.json()['report']['report_id']

        response = client.post(
            '/api/v1/runs',
            json={'patient_id': 'REAL-OPENAI', 'report_ids': [report_id]},
        )
        assert response.status_code == 200
        assert response.json()['run_status'] in {'completed', 'degraded'}
