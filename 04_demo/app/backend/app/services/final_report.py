from __future__ import annotations

from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.draft import ApproveResult, DropResult
from app.schemas.run import RunStatus, ReviewStatus


class FinalReportService:
    def __init__(self, settings, run_repo) -> None:
        self.settings = settings
        self.run_repo = run_repo

    def get_pdf(self, run_id: str) -> Path:
        run = self.run_repo.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Run not found.')
        if run.review_status == ReviewStatus.dropped:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Dropped run does not have an approved PDF.')

        if run.review_status == ReviewStatus.approved and run.approved_pdf_path:
            path = Path(run.approved_pdf_path)
            if not path.exists():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Approved PDF is missing.')
            return path

        preview_path = self.settings.final_report_dir / f'{run_id}_preview.pdf'
        self._render_pdf(preview_path, run.report_payload, run.review_note)
        return preview_path

    def approve(self, run_id: str) -> ApproveResult:
        run = self.run_repo.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Run not found.')
        if run.review_status == ReviewStatus.dropped:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Dropped run cannot be approved.')
        if run.run_status == RunStatus.blocked:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Blocked run cannot be approved until extractable.')

        approved_path = self.settings.final_report_dir / f'{run_id}_final.pdf'
        self._render_pdf(approved_path, run.report_payload, run.review_note)
        approved_at = datetime.now().astimezone()
        self.run_repo.save_approved_pdf_path(run_id, str(approved_path))
        approved = self.run_repo.approve(run_id, approved_at)
        return approved

    def drop(self, run_id: str, review_note: str | None = None) -> DropResult:
        run = self.run_repo.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Run not found.')
        return self.run_repo.drop(run_id, drop_note=review_note)

    def _render_pdf(self, output_path: Path, report_payload, review_note: str | None = None) -> None:
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading2']
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['BodyText'],
            spaceAfter=6,
            leading=14,
            wordWrap='CJK',
            splitLongWords=True,
        )
        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['BodyText'],
            fontSize=9,
            leading=11,
            textColor=colors.black,
            wordWrap='CJK',
            splitLongWords=True,
        )
        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['BodyText'],
            fontSize=9,
            leading=11,
            wordWrap='CJK',
            splitLongWords=True,
        )
        small_style = ParagraphStyle(
            'SmallMuted',
            parent=styles['BodyText'],
            fontSize=9,
            textColor=colors.HexColor('#555555'),
            wordWrap='CJK',
            splitLongWords=True,
        )

        def as_paragraph(value: object, style: ParagraphStyle = body_style) -> Paragraph:
            text = escape(str(value or '')).replace('\n', '<br/>')
            return Paragraph(text, style)

        story = [Paragraph('AI-Assisted Genomic Report (Mock)', title_style), Spacer(1, 6 * mm)]

        patient_rows = [
            [as_paragraph('Field', table_header_style), as_paragraph('Value', table_header_style)],
            [as_paragraph('Patient ID', table_cell_style), as_paragraph(report_payload.patient_id, table_cell_style)],
        ]
        patient_table = Table(patient_rows, colWidths=[55 * mm, 115 * mm], repeatRows=1, splitByRow=1)
        patient_table.setStyle(
            TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d9d9d9')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ])
        )
        story.append(Paragraph('1. Patient & Referral Context', heading_style))
        story.append(patient_table)
        story.append(Spacer(1, 4 * mm))

        intro_sections = [
            ('2. Clinical Phenotype (AI Extracted)', report_payload.clinical_phenotype),
            ('3. AI Clinical Summary', report_payload.ai_clinical_summary),
        ]
        detail_sections = [
            ('5. Expanded Evidence', report_payload.expanded_evidence),
            ('6. ACMG Classification', report_payload.acmg_classification),
            ('7. Clinical Integration', report_payload.clinical_integration),
            ('8. Expected Symptoms', report_payload.expected_symptoms),
            ('9. Recommendations', report_payload.recommendations),
            ('10. Limitations', report_payload.limitations),
        ]

        for heading, content in intro_sections:
            if not content:
                continue
            story.append(Paragraph(heading, heading_style))
            story.append(as_paragraph(content, body_style))
            story.append(Spacer(1, 4 * mm))

        if report_payload.variant_summary_rows:
            story.append(Paragraph('4. Variant Summary', heading_style))
            rows = [[
                as_paragraph('Gene', table_header_style),
                as_paragraph('Transcript HGVS', table_header_style),
                as_paragraph('Protein Change', table_header_style),
                as_paragraph('Consequence', table_header_style),
            ]]
            for item in report_payload.variant_summary_rows:
                rows.append([
                    as_paragraph(item.gene or 'N/A', table_cell_style),
                    as_paragraph(item.transcript_hgvs or 'N/A', table_cell_style),
                    as_paragraph(item.protein_change or 'N/A', table_cell_style),
                    as_paragraph(item.consequence or item.variation_type or 'N/A', table_cell_style),
                ])
            variant_table = Table(rows, colWidths=[28 * mm, 54 * mm, 34 * mm, 59 * mm], repeatRows=1, splitByRow=1)
            variant_table.setStyle(
                TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d9d9d9')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ])
            )
            story.append(variant_table)
            story.append(Spacer(1, 4 * mm))

        for heading, content in detail_sections:
            if not content:
                continue
            story.append(Paragraph(heading, heading_style))
            story.append(as_paragraph(content, body_style))
            story.append(Spacer(1, 4 * mm))

        if review_note:
            note = (review_note or '').strip()
            if note:
                story.append(Paragraph('11. Clinician Review Note', heading_style))
                story.append(as_paragraph(note, body_style))
                story.append(Spacer(1, 4 * mm))

        story.append(as_paragraph('Generated for demo use only. Patient-facing release requires human clinical governance.', small_style))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(str(output_path), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
        doc.build(story)
