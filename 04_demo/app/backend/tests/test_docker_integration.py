from __future__ import annotations

import os

import httpx
import pytest

BASE_URL = os.getenv('HSIL_DOCKER_BASE_URL')
pytestmark = pytest.mark.skipif(not BASE_URL, reason='Set HSIL_DOCKER_BASE_URL after docker compose up.')


def test_docker_stack_upload_run_review() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        health = client.get('/healthz')
        assert health.status_code == 200
        assert health.json()['database'] == 'ok'

        upload = client.post(
            '/api/v1/reports/upload',
            files={'file': ('ravi-report.pdf', b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n', 'application/pdf')},
        )
        assert upload.status_code == 201
        report_id = upload.json()['report']['report_id']

        run = client.post(f'/api/v1/reports/{report_id}/run')
        assert run.status_code == 200
        assert run.json()['report_id'] == report_id

        review = client.post(
            f'/api/v1/reports/{report_id}/review',
            json={'reviewer_name': 'integration', 'next_step': 'Proceed to clinician review.'},
        )
        assert review.status_code == 200
        assert review.json()['status'] == 'reviewed'
