from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfReader
from reportlab.pdfgen import canvas


def _prepare_run(client: TestClient, pdf_bytes: bytes) -> str:
    upload = client.post(
        "/api/v1/reports/upload",
        files={"file": ("ravi-report.pdf", pdf_bytes, "application/pdf")},
        data={"report_kind": "test"},
    )
    report_id = upload.json()["report"]["report_id"]
    run_response = client.post(
        "/api/v1/runs",
        json={"patient_id": "review-case", "report_ids": [report_id]},
    )
    assert run_response.status_code == 200
    return run_response.json()["run_id"]


def _build_context_rich_pdf_bytes() -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 760, "HSIL demo PDF fixture")
    pdf.drawString(72, 740, "Referral: phenotype-genotype correlation for inherited retinal dystrophy")
    pdf.drawString(72, 720, "Phenotype: nyctalopia, progressive vision loss, peripheral field loss")
    pdf.drawString(72, 700, "History: childhood-onset retinal dystrophy")
    pdf.drawString(72, 680, "Variant: RPE65 NM_000329.3:c.260A>G / p.Asp87Gly")
    pdf.save()
    return buffer.getvalue()


def test_review_only_stores_note_and_timestamp(client: TestClient, pdf_bytes: bytes) -> None:
    run_id = _prepare_run(client, pdf_bytes)
    response = client.post(
        f"/api/v1/runs/{run_id}/review",
        json={"reviewer_name": "Leo", "review_note": "Looks good, minor wording tweak needed."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run_id
    assert body["review_status"] == "reviewed"
    assert body["review_note"] == "Looks good, minor wording tweak needed."


def test_review_requires_note_text(client: TestClient, pdf_bytes: bytes) -> None:
    run_id = _prepare_run(client, pdf_bytes)
    response = client.post(
        f"/api/v1/runs/{run_id}/review", json={"reviewer_name": "Leo", "review_note": ""}
    )
    assert response.status_code == 400


def test_approve_generates_frozen_pdf(client: TestClient, pdf_bytes: bytes) -> None:
    run_id = _prepare_run(client, pdf_bytes)
    client.post(
        f"/api/v1/runs/{run_id}/review",
        json={"reviewer_name": "Leo", "review_note": "Approved with note."},
    )

    response = client.post(f"/api/v1/runs/{run_id}/approve")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run_id
    assert body["download_path"].endswith("/pdf")

    pdf = client.get(f"/api/v1/runs/{run_id}/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content.startswith(b"%PDF")

    reader = PdfReader(BytesIO(pdf.content))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    assert "4. Variant Summary" in text
    assert "5. Evidence Categorisation" in text
    assert text.index("4. Variant Summary") < text.index("5. Evidence Categorisation")
    assert "7. Clinical Integration" in text
    assert "9. Recommendations" in text


def test_approve_pdf_uses_distinct_clinical_sections(client: TestClient) -> None:
    run_id = _prepare_run(client, _build_context_rich_pdf_bytes())
    client.post(
        f"/api/v1/runs/{run_id}/review",
        json={"reviewer_name": "Leo", "review_note": "Approved with richer clinical context."},
    )

    pdf = client.post(f"/api/v1/runs/{run_id}/approve")
    assert pdf.status_code == 200

    approved_pdf = client.get(f"/api/v1/runs/{run_id}/pdf")
    assert approved_pdf.status_code == 200

    text = "\n".join(
        (page.extract_text() or "")
        for page in PdfReader(BytesIO(approved_pdf.content)).pages
    )
    assert "1. Patient & Report Context" in text
    assert "2. Clinical Context (Extracted)" in text
    assert "5. Evidence Categorisation" in text
    assert "6. Current Classification Snapshot" in text
    assert "8. Gene-/Disease-Associated Phenotype" in text
    assert "Classification (ClinVar):" in text
    assert "Splicing effect (SpliceAI):" in text
    assert "Phenotype: nyctalopia, progressive vision loss, peripheral field loss" in text
    assert "Current evidence remains aligned with uncertain significance" in text
    assert "Correlate the reported variant with the extracted phenotype/history from the uploaded report." in text
    assert "Keep patient-facing release gated on clinician review and sign-off." in text


def test_drop_marks_run_dropped_and_blocks_pdf(client: TestClient, pdf_bytes: bytes) -> None:
    run_id = _prepare_run(client, pdf_bytes)
    drop = client.post(f"/api/v1/runs/{run_id}/drop", json={"review_note": "Noisy extraction."})
    assert drop.status_code == 200
    assert drop.json()["review_status"] == "dropped"

    pdf = client.get(f"/api/v1/runs/{run_id}/pdf")
    assert pdf.status_code == 409
