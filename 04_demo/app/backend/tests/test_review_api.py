from __future__ import annotations

from fastapi.testclient import TestClient


def _prepare_run(client: TestClient, pdf_bytes: bytes) -> str:
    upload = client.post(
        '/api/v1/reports/upload',
        files={'file': ('ravi-report.pdf', pdf_bytes, 'application/pdf')},
    )
    report_id = upload.json()['report']['report_id']
    run_response = client.post(f'/api/v1/reports/{report_id}/run')
    assert run_response.status_code == 200
    return report_id


def test_review_accepts_payload_and_stores_edited_draft(client: TestClient, pdf_bytes: bytes) -> None:
    report_id = _prepare_run(client, pdf_bytes)
    response = client.post(
        f'/api/v1/reports/{report_id}/review',
        json={
            'reviewer_name': 'Leo',
            'reviewer_notes': 'Keep it review-required, but make the next step explicit.',
            'next_step': 'Refer to retinal genetics review with phenotype confirmation.',
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'reviewed'
    assert body['reviewed_draft']['next_step'].startswith('Refer to retinal genetics review')


def test_review_cannot_silently_erase_required_draft_fields(client: TestClient, pdf_bytes: bytes) -> None:
    report_id = _prepare_run(client, pdf_bytes)
    response = client.post(
        f'/api/v1/reports/{report_id}/review',
        json={'recommendation': '   '},
    )
    assert response.status_code == 422
