from __future__ import annotations

from fastapi.testclient import TestClient


def _prepare_run(client: TestClient, pdf_bytes: bytes) -> dict:
    upload = client.post(
        '/api/v1/reports/upload',
        files={'file': ('ravi-report.pdf', pdf_bytes, 'application/pdf')},
        data={'report_kind': 'test', 'case_id': 'review-case'},
    )
    report_id = upload.json()['report']['report_id']
    run_response = client.post(f'/api/v1/reports/{report_id}/run')
    assert run_response.status_code == 200
    return {'report_id': report_id, 'run_id': run_response.json()['run_id']}


def test_review_accepts_payload_and_stores_edited_draft(client: TestClient, pdf_bytes: bytes) -> None:
    ids = _prepare_run(client, pdf_bytes)
    response = client.post(
        f"/api/v1/runs/{ids['run_id']}/review",
        json={
            'reviewer_name': 'Leo',
            'reviewer_notes': 'Keep it review-required, but make the next step explicit.',
            'next_step': 'Refer to retinal genetics review with phenotype confirmation.',
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'reviewed'
    assert body['run_id'] == ids['run_id']
    assert body['reviewed_draft']['next_step'].startswith('Refer to retinal genetics review')


def test_report_scoped_review_still_targets_latest_run(client: TestClient, pdf_bytes: bytes) -> None:
    ids = _prepare_run(client, pdf_bytes)
    response = client.post(
        f"/api/v1/reports/{ids['report_id']}/review",
        json={'reviewer_name': 'Leo', 'next_step': 'Proceed with clinician review only.'},
    )
    assert response.status_code == 200
    assert response.json()['run_id'] == ids['run_id']


def test_review_cannot_process_blocked_patient_run(client: TestClient, pdf_bytes: bytes) -> None:
    upload = client.post(
        '/api/v1/reports/upload',
        files={'file': ('patient.pdf', pdf_bytes, 'application/pdf')},
        data={'report_kind': 'patient', 'case_id': 'patient-review'},
    )
    report_id = upload.json()['report']['report_id']
    run = client.post(f'/api/v1/reports/{report_id}/run')
    run_id = run.json()['run_id']
    response = client.post(f'/api/v1/runs/{run_id}/review', json={'recommendation': 'override'})
    assert response.status_code == 409


def test_finalize_creates_pdf_artifact_and_downloads_it(client: TestClient, pdf_bytes: bytes) -> None:
    ids = _prepare_run(client, pdf_bytes)
    review = client.post(
        f"/api/v1/runs/{ids['run_id']}/review",
        json={'reviewer_name': 'Leo', 'reviewer_notes': 'Looks good.'},
    )
    assert review.status_code == 200

    finalize = client.post(f"/api/v1/runs/{ids['run_id']}/finalize")
    assert finalize.status_code == 200
    body = finalize.json()
    assert body['download_path'] == f"/api/v1/runs/{ids['run_id']}/final.pdf"

    pdf = client.get(body['download_path'])
    assert pdf.status_code == 200
    assert pdf.headers['content-type'].startswith('application/pdf')
    assert pdf.content.startswith(b'%PDF')
