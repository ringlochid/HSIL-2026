from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.run import FinalizeResponse


class FinalReportService:
    def __init__(self, settings, reports_repo, run_repo) -> None:
        self.settings = settings
        self.reports_repo = reports_repo
        self.run_repo = run_repo

    def finalize_run(self, run_id: str) -> FinalizeResponse:
        run = self.run_repo.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Run not found.')
        if run.status == 'blocked':
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Blocked runs cannot be finalized.')

        review = self.run_repo.get_review(run_id)
        if review is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='A reviewed draft is required before finalization.')

        report = self.reports_repo.get(run.report_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Report not found.')

        output_path = self.settings.final_report_dir / f'{run_id}.pdf'
        self._render_pdf(output_path, report, run, review)
        self.run_repo.save_final_pdf_path(run_id, str(output_path))
        return FinalizeResponse(
            run_id=run.run_id,
            report_id=run.report_id,
            filename=output_path.name,
            download_path=f'/api/v1/runs/{run_id}/final.pdf',
        )

    def get_final_pdf_path(self, run_id: str) -> Path:
        path = self.run_repo.get_final_pdf_path(run_id)
        if not path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Final PDF not found for this run.')
        pdf_path = Path(path)
        if not pdf_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Stored final PDF artifact is missing.')
        return pdf_path

    def _render_pdf(self, output_path: Path, report, run, review) -> None:
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading2']
        body_style = styles['BodyText']
        body_style.spaceAfter = 6
        small_style = ParagraphStyle('SmallMuted', parent=styles['BodyText'], fontSize=9, textColor=colors.HexColor('#555555'))

        story = []
        story.append(Paragraph('AI-Assisted Genomic Report (Mock)', title_style))
        story.append(Spacer(1, 6 * mm))

        patient_rows = [
            ['Field', 'Value'],
            ['Report ID', report.report_id],
            ['Run ID', run.run_id],
            ['Report Kind', report.report_kind],
            ['Case ID', report.case_id or 'N/A'],
            ['Filename', report.filename],
        ]
        if report.extracted_case.variants:
            variant = report.extracted_case.variants[0]
            patient_rows.extend([
                ['Gene', variant.gene],
                ['Variant', variant.protein_change],
                ['Transcript HGVS', variant.transcript_hgvs],
            ])

        evidence_table = [['Source', 'Status', 'Summary']]
        for item in run.evidence:
            summary_text = '; '.join(f'{key}: {value}' for key, value in item.summary.items())
            evidence_table.append([item.source, item.status, summary_text[:180] or 'N/A'])

        sections = [
            ('1. Patient & Referral Context', None),
            ('2. Clinical Phenotype / Extracted Context', report.extracted_case.summary),
            ('3. AI Clinical Summary', review.reviewed_draft.recommendation),
            ('4. Variant Summary', None),
            ('5. Expanded Evidence', review.reviewed_draft.evidence_summary),
            ('6. Clinical Uncertainty', review.reviewed_draft.uncertainty),
            ('7. Next Step', review.reviewed_draft.next_step),
        ]

        for heading, text in sections:
            story.append(Paragraph(heading, heading_style))
            if heading == '1. Patient & Referral Context':
                table = Table(patient_rows, colWidths=[55 * mm, 115 * mm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d9d9d9')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(table)
            elif heading == '4. Variant Summary':
                table = Table(evidence_table, colWidths=[28 * mm, 24 * mm, 118 * mm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d9d9d9')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(table)
            else:
                story.append(Paragraph(text or 'N/A', body_style))
            story.append(Spacer(1, 4 * mm))

        story.append(Paragraph('Reviewer Notes', heading_style))
        story.append(Paragraph(review.reviewer_notes or 'No reviewer notes supplied.', body_style))
        story.append(Paragraph('Generated for demo use only. Patient-facing release requires human clinical governance.', small_style))

        doc = SimpleDocTemplate(str(output_path), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
        doc.build(story)
