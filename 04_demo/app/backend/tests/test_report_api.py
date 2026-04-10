from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_upload_report_returns_report_id_and_extraction_summary(client: TestClient, pdf_bytes: bytes) -> None:
    response = client.post(
        '/api/v1/reports/upload',
        files={'file': ('ravi-report.pdf', pdf_bytes, 'application/pdf')},
    )
    assert response.status_code == 201
    body = response.json()
    assert body['report']['report_id'].startswith('report_')
    assert body['report']['extracted_case']['variants'][0]['gene'] == 'RPE65'
    assert body['report']['extracted_case']['variants'][0]['protein_change'] == 'p.Asp87Gly'


def test_upload_rejects_invalid_file_type(client: TestClient) -> None:
    response = client.post(
        '/api/v1/reports/upload',
        files={'file': ('notes.txt', b'not a pdf', 'text/plain')},
    )
    assert response.status_code == 415


def test_upload_rejects_oversize_payload(tmp_path: Path, pdf_bytes: bytes) -> None:
    settings = Settings(
        upload_dir=tmp_path / 'uploads',
        database_url=f"sqlite+pysqlite:///{(tmp_path / 'oversize.db').as_posix()}",
        llm_provider='mock',
        use_real_apis=False,
        max_upload_mb=0,
        debug=True,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.post(
            '/api/v1/reports/upload',
            files={'file': ('too-big.pdf', pdf_bytes, 'application/pdf')},
        )
    assert response.status_code == 413
