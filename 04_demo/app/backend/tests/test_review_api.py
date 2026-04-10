from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfReader


def _prepare_run(client: TestClient, pdf_bytes: bytes) -> str:
    upload = client.post(
        '/api/v1/reports/upload',
        files={'file': ('ravi-report.pdf', pdf_bytes, 'application/pdf')},
        data={'report_kind': 'test'},
    )
    report_id = upload.json()['report']['report_id']
    run_response = client.post(
        '/api/v1/runs',
        json={'patient_id': 'review-case', 'report_ids': [report_id]},
    )
    assert run_response.status_code == 200
    return run_response.json()['run_id']


def test_review_only_stores_note_and_timestamp(client: TestClient, pdf_bytes: bytes) -> None:
    run_id = _prepare_run(client, pdf_bytes)
    response = client.post(
        f'/api/v1/runs/{run_id}/review',
        json={'reviewer_name': 'Leo', 'review_note': 'Looks good, minor wording tweak needed.'},
    )
    assert response.status_code == 200
    body = response.json()
    assert body['run_id'] == run_id
    assert body['review_status'] == 'reviewed'
    assert body['review_note'] == 'Looks good, minor wording tweak needed.'


def test_review_requires_note_text(client: TestClient, pdf_bytes: bytes) -> None:
    run_id = _prepare_run(client, pdf_bytes)
    response = client.post(f'/api/v1/runs/{run_id}/review', json={'reviewer_name': 'Leo', 'review_note': ''})
    assert response.status_code == 400


def test_approve_generates_frozen_pdf(client: TestClient, pdf_bytes: bytes) -> None:
    run_id = _prepare_run(client, pdf_bytes)
    client.post(
        f'/api/v1/runs/{run_id}/review',
        json={'reviewer_name': 'Leo', 'review_note': 'Approved with note.'},
    )

    response = client.post(f'/api/v1/runs/{run_id}/approve')
    assert response.status_code == 200
    body = response.json()
    assert body['run_id'] == run_id
    assert body['download_path'].endswith('/pdf')

    pdf = client.get(f'/api/v1/runs/{run_id}/pdf')
    assert pdf.status_code == 200
    assert pdf.headers['content-type'].startswith('application/pdf')
    assert pdf.content.startswith(b'%PDF')

    reader = PdfReader(BytesIO(pdf.content))
    text = '\n'.join((page.extract_text() or '') for page in reader.pages)
    assert '4. Variant Summary' in text
    assert '5. Expanded Evidence' in text
    assert text.index('4. Variant Summary') < text.index('5. Expanded Evidence')


def test_drop_marks_run_dropped_and_blocks_pdf(client: TestClient, pdf_bytes: bytes) -> None:
    run_id = _prepare_run(client, pdf_bytes)
    drop = client.post(f'/api/v1/runs/{run_id}/drop', json={'review_note': 'Noisy extraction.'})
    assert drop.status_code == 200
    assert drop.json()['review_status'] == 'dropped'

    pdf = client.get(f'/api/v1/runs/{run_id}/pdf')
    assert pdf.status_code == 409
