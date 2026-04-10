from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException, status

from app.rules.base import DecisionInput
from app.schemas.run import ReportPayload, RunRequest, RunResponse, RunStatus, EvidenceSourceSummary, VariantSummaryRow
from app.schemas.report import ExtractedCase, ExtractedVariant


class WorkflowService:
    def __init__(self, reports_repo, run_repo, tool_registry, rule_engine) -> None:
        self.reports_repo = reports_repo
        self.run_repo = run_repo
        self.tool_registry = tool_registry
        self.rule_engine = rule_engine

    def create_run(self, payload: RunRequest) -> RunResponse:
        if not payload.report_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='At least one report_id is required.')

        reports = []
        missing = []
        for report_id in payload.report_ids:
            report = self.reports_repo.get(report_id)
            if report is None:
                missing.append(report_id)
            else:
                reports.append(report)

        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Reports not found: {", ".join(missing)}',
            )

        report_statuses = [report.extraction_status for report in reports]

        evidence = []
        evidence_map = {}
        evidence_statuses = {}
        warnings: list[str] = []
        for name in ('vep', 'spliceai', 'clinvar', 'franklin'):
            tool = self.tool_registry[name]
            result = tool.get_evidence()
            summary = EvidenceSourceSummary(
                source=result.source,
                status=result.status,
                request_identity=result.request_identity,
                summary=result.summary,
                warnings=result.warnings,
            )
            evidence.append(summary)
            evidence_map[name] = result.summary
            evidence_statuses[name] = result.status
            warnings.extend(result.warnings)

        run_status = self._derive_run_status(report_statuses, evidence_statuses, warnings)

        case_title = self._extract_case_title(reports)
        decision_input = DecisionInput(case_title=case_title, evidence=evidence_map, evidence_statuses=evidence_statuses)
        decision = self.rule_engine.evaluate(decision_input)

        report_payload = self._build_report_payload(
            patient_id=payload.patient_id,
            reports=reports,
            decision=decision,
            evidence_lines=decision.evidence_lines,
        )

        run_response = self.run_repo.create_run(
            run_id=f'run_{uuid4().hex[:12]}',
            patient_id=payload.patient_id,
            report_ids=payload.report_ids,
            run_status=run_status,
            report_payload=report_payload,
            evidence=evidence,
            warnings=warnings,
        )

        return RunResponse(
            run_id=run_response.run_id,
            patient_id=run_response.patient_id,
            report_ids=run_response.report_ids,
            run_status=run_response.run_status,
            review_status=run_response.review_status,
            report_payload=report_payload,
            evidence=evidence,
            warnings=warnings,
            review_note=None,
            reviewed_at=None,
            approved_pdf_path=None,
        )

    def get_run(self, run_id: str) -> RunResponse:
        run = self.run_repo.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Run not found.')
        return run

    def _derive_run_status(
        self,
        report_statuses: list[str],
        evidence_statuses: dict[str, str],
        warnings: list[str],
    ) -> RunStatus:
        if report_statuses and all(item == 'blocked' for item in report_statuses):
            return RunStatus.blocked

        evidence_problem = {
            status.lower()
            for status in evidence_statuses.values()
            if isinstance(status, str)
        }
        if evidence_problem & {'fallback', 'degraded', 'error', 'failed'}:
            return RunStatus.degraded
        if warnings:
            return RunStatus.degraded
        if any(item in {'blocked', 'degraded'} for item in report_statuses):
            return RunStatus.degraded
        return RunStatus.completed

    def _extract_case_title(self, reports) -> str:
        titles = [report.extracted_case.report_title for report in reports if report.extracted_case.report_title]
        if titles:
            return titles[0]
        return 'Genomic interpretation report'

    def _collect_variants(self, reports) -> list[VariantSummaryRow]:
        rows: list[VariantSummaryRow] = []
        for report in reports:
            extracted = report.extracted_case if isinstance(report.extracted_case, ExtractedCase) else ExtractedCase.model_validate(report.extracted_case)
            for variant in extracted.variants:
                if isinstance(variant, ExtractedVariant):
                    rows.append(
                        VariantSummaryRow(
                            gene=variant.gene,
                            transcript_hgvs=variant.transcript_hgvs,
                            protein_change=variant.protein_change,
                            genomic_hg38=variant.genomic_hg38,
                            variation_type=variant.variation_type,
                            consequence=variant.consequence,
                        )
                    )
                else:
                    payload = getattr(variant, 'model_dump', lambda: variant)()
                    rows.append(VariantSummaryRow(**payload))
        return rows

    def _build_report_payload(self, patient_id: str, reports, decision, evidence_lines: list[str]) -> ReportPayload:
        phenotype_sections = [
            report.extracted_case.summary
            for report in reports
            if getattr(report.extracted_case, 'summary', '').strip()
        ]
        clinical_phenotype = '\n\n'.join(phenotype_sections).strip() or None

        variant_rows = self._collect_variants(reports)

        acmg_lines = []
        for item in evidence_lines[:3]:
            if item:
                acmg_lines.append(item)
        acmg_classification = '; '.join(acmg_lines[:2]).strip() or None

        expected_symptoms = 'Progressive vision loss, night blindness, peripheral vision loss.'

        return ReportPayload(
            patient_id=patient_id,
            clinical_phenotype=clinical_phenotype,
            ai_clinical_summary=decision.recommendation,
            variant_summary_rows=variant_rows,
            expanded_evidence='\n'.join(evidence_lines),
            acmg_classification=acmg_classification,
            clinical_integration=decision.next_step,
            expected_symptoms=expected_symptoms,
            recommendations=decision.next_step,
            limitations=decision.uncertainty,
        )
