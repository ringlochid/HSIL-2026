from __future__ import annotations

import os

import httpx
import pytest

BASE_URL = os.getenv('HSIL_DOCKER_BASE_URL')
pytestmark = pytest.mark.skipif(not BASE_URL, reason='Set HSIL_DOCKER_BASE_URL after docker compose up.')


PDF_BYTES = b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n'


def test_docker_stack_upload_batch_review_finalize() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        health = client.get('/healthz')
        assert health.status_code == 200
        assert health.json()['database'] == 'ok'

        upload_test = client.post(
            '/api/v1/reports/upload',
            files={'file': ('test.pdf', PDF_BYTES, 'application/pdf')},
            data={'report_kind': 'test', 'case_id': 'docker-test'},
        )
        upload_patient = client.post(
            '/api/v1/reports/upload',
            files={'file': ('patient.pdf', PDF_BYTES, 'application/pdf')},
            data={'report_kind': 'patient', 'case_id': 'docker-patient'},
        )
        assert upload_test.status_code == 201
        assert upload_patient.status_code == 201
        test_report_id = upload_test.json()['report']['report_id']
        patient_report_id = upload_patient.json()['report']['report_id']

        batch = client.post(
            '/api/v1/runs/batch',
            json={'report_ids': [test_report_id, patient_report_id], 'mode': 'independent'},
        )
        assert batch.status_code == 200
        results = batch.json()['results']
        test_run = next(item for item in results if item['report_id'] == test_report_id)
        patient_run = next(item for item in results if item['report_id'] == patient_report_id)
        assert test_run['status'] == 'completed'
        assert patient_run['status'] == 'blocked'

        review = client.post(
            f"/api/v1/runs/{test_run['run_id']}/review",
            json={'reviewer_name': 'integration', 'reviewer_notes': 'Proceed.'},
        )
        assert review.status_code == 200

        finalize = client.post(f"/api/v1/runs/{test_run['run_id']}/finalize")
        assert finalize.status_code == 200
        pdf = client.get(finalize.json()['download_path'])
        assert pdf.status_code == 200
        assert pdf.content.startswith(b'%PDF')
