from __future__ import annotations

from fastapi.testclient import TestClient

from app.tools.base import ToolResult


def _upload_report(client: TestClient, pdf_bytes: bytes, report_kind: str = 'test', case_id: str | None = None) -> str:
    response = client.post(
        '/api/v1/reports/upload',
        files={'file': ('ravi-report.pdf', pdf_bytes, 'application/pdf')},
        data={'report_kind': report_kind, 'case_id': case_id or ''},
    )
    assert response.status_code == 201
    return response.json()['report']['report_id']


def test_run_returns_deterministic_draft_and_evidence(client: TestClient, pdf_bytes: bytes) -> None:
    report_id = _upload_report(client, pdf_bytes, report_kind='test', case_id='demo-1')
    response = client.post(f'/api/v1/reports/{report_id}/run')
    assert response.status_code == 200
    body = response.json()
    assert body['report_id'] == report_id
    assert body['status'] == 'completed'
    assert body['draft']['case_title'] == 'RPE65 variant review demo case'
    assert 'clinician review' in body['draft']['recommendation'].lower()
    assert len(body['evidence']) == 4
    assert {item['source'] for item in body['evidence']} == {'vep', 'spliceai', 'clinvar', 'franklin'}


def test_patient_run_fails_closed_without_ai(client: TestClient, pdf_bytes: bytes) -> None:
    report_id = _upload_report(client, pdf_bytes, report_kind='patient', case_id='patient-001')
    response = client.post(f'/api/v1/reports/{report_id}/run')
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'blocked'
    assert 'Interpretation blocked' in body['draft']['recommendation']
    assert body['evidence'] == []


def test_batch_run_returns_independent_results_for_multiple_reports(client: TestClient, pdf_bytes: bytes) -> None:
    test_report = _upload_report(client, pdf_bytes, report_kind='test', case_id='batch-test')
    patient_report = _upload_report(client, pdf_bytes, report_kind='patient', case_id='batch-patient')
    response = client.post('/api/v1/runs/batch', json={'report_ids': [test_report, patient_report], 'mode': 'independent'})
    assert response.status_code == 200
    body = response.json()
    assert body['batch_id'].startswith('batch_')
    assert len(body['results']) == 2
    statuses = {item['report_id']: item['status'] for item in body['results']}
    assert statuses[test_report] == 'completed'
    assert statuses[patient_report] == 'blocked'


def test_run_surface_degraded_evidence_when_tool_falls_back(client: TestClient, app, pdf_bytes: bytes, monkeypatch) -> None:
    report_id = _upload_report(client, pdf_bytes)

    def fake_fallback_result() -> ToolResult:
        return ToolResult(
            source='clinvar',
            status='fallback',
            request_identity={'clinvar_id': '1421454'},
            summary={
                'gene': 'RPE65',
                'classification': 'Uncertain significance',
                'review_status': 'criteria provided, single submitter',
            },
            warnings=['live_fetch_failed:RuntimeError'],
        )

    monkeypatch.setattr(app.state.workflow_service.tool_registry['clinvar'], 'get_evidence', fake_fallback_result)

    response = client.post(f'/api/v1/reports/{report_id}/run')
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'degraded'
    assert any('Fallback evidence mode' in warning for warning in body['warnings'])
    clinvar_entry = next(item for item in body['evidence'] if item['source'] == 'clinvar')
    assert clinvar_entry['status'] == 'fallback'
    assert any('live_fetch_failed' in warning for warning in clinvar_entry['warnings'])
