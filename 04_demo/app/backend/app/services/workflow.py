from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException, status

from app.rules.base import DecisionInput
from app.schemas.report import ExtractedCase, ExtractedVariant
from app.schemas.run import (
    EvidenceSourceSummary,
    ReportPayload,
    RunRequest,
    RunResponse,
    RunStatus,
    VariantSummaryRow,
)


class WorkflowService:
    def __init__(
        self,
        reports_repo,
        run_repo,
        tool_registry,
        rule_engine,
        search_index_service=None,
    ) -> None:
        self.reports_repo = reports_repo
        self.run_repo = run_repo
        self.tool_registry = tool_registry
        self.rule_engine = rule_engine
        self.search_index_service = search_index_service

    def create_run(self, payload: RunRequest) -> RunResponse:
        if not payload.report_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one report_id is required.",
            )

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
                detail=f"Reports not found: {', '.join(missing)}",
            )

        report_statuses = [report.extraction_status for report in reports]

        evidence = []
        evidence_map = {}
        evidence_statuses = {}
        warnings: list[str] = []
        for name in ("vep", "spliceai", "clinvar", "franklin"):
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
        decision_input = DecisionInput(
            case_title=case_title, evidence=evidence_map, evidence_statuses=evidence_statuses
        )
        decision = self.rule_engine.evaluate(decision_input)

        report_payload = self._build_report_payload(
            patient_id=payload.patient_id,
            reports=reports,
            decision=decision,
            evidence_map=evidence_map,
            evidence_statuses=evidence_statuses,
        )

        run_response = self.run_repo.create_run(
            run_id=f"run_{uuid4().hex[:12]}",
            patient_id=payload.patient_id,
            report_ids=payload.report_ids,
            run_status=run_status,
            report_payload=report_payload,
            evidence=evidence,
            warnings=warnings,
        )

        response = RunResponse(
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
        if self.search_index_service is not None:
            self.search_index_service.index_run(response, reports)
        return response

    def get_run(self, run_id: str) -> RunResponse:
        run = self.run_repo.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
        return run

    def _derive_run_status(
        self,
        report_statuses: list[str],
        evidence_statuses: dict[str, str],
        warnings: list[str],
    ) -> RunStatus:
        if report_statuses and all(item == "blocked" for item in report_statuses):
            return RunStatus.blocked

        evidence_problem = {
            status.lower() for status in evidence_statuses.values() if isinstance(status, str)
        }
        if evidence_problem & {"fallback", "degraded", "error", "failed"}:
            return RunStatus.degraded
        if warnings:
            return RunStatus.degraded
        if any(item in {"blocked", "degraded"} for item in report_statuses):
            return RunStatus.degraded
        return RunStatus.completed

    def _extract_case_title(self, reports) -> str:
        titles = [
            self._coerce_case(report).report_title
            for report in reports
            if self._coerce_case(report).report_title
        ]
        if titles:
            return titles[0]
        return "Genomic interpretation report"

    def _coerce_case(self, report) -> ExtractedCase:
        extracted = report.extracted_case
        if isinstance(extracted, ExtractedCase):
            return extracted
        return ExtractedCase.model_validate(extracted)

    def _collect_variants(self, reports) -> list[VariantSummaryRow]:
        rows: list[VariantSummaryRow] = []
        for report in reports:
            extracted = self._coerce_case(report)
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
                    payload = getattr(variant, "model_dump", lambda: variant)()
                    if isinstance(payload, dict):
                        rows.append(VariantSummaryRow.model_validate(payload))
                    else:
                        rows.append(VariantSummaryRow())
        return rows

    def _build_report_payload(
        self,
        patient_id: str,
        reports,
        decision,
        evidence_map: dict[str, dict],
        evidence_statuses: dict[str, str],
    ) -> ReportPayload:
        variant_rows = self._collect_variants(reports)
        primary_case = self._coerce_case(reports[0]) if reports else None
        clinical_phenotype = self._build_clinical_context(reports)

        return ReportPayload(
            patient_id=patient_id,
            case_label=primary_case.case_label if primary_case else None,
            report_title=primary_case.report_title if primary_case else None,
            source_filenames=[report.filename for report in reports if getattr(report, "filename", None)],
            clinical_phenotype=clinical_phenotype,
            ai_clinical_summary=self._build_ai_clinical_summary(
                variant_rows=variant_rows,
                evidence_map=evidence_map,
                decision=decision,
            ),
            variant_summary_rows=variant_rows,
            expanded_evidence=self._build_evidence_categorisation(
                evidence_map=evidence_map,
                evidence_statuses=evidence_statuses,
            ),
            acmg_classification=self._build_classification_snapshot(evidence_map),
            clinical_integration=self._build_clinical_integration(
                clinical_phenotype=clinical_phenotype,
                variant_rows=variant_rows,
                evidence_map=evidence_map,
            ),
            expected_symptoms=self._build_expected_symptoms(
                clinical_phenotype=clinical_phenotype,
                variant_rows=variant_rows,
            ),
            recommendations=self._build_recommendations(clinical_phenotype=clinical_phenotype),
            limitations=decision.uncertainty,
        )

    def _build_clinical_context(self, reports) -> str:
        extracted_lines: list[str] = []
        seen: set[str] = set()
        keywords = (
            "phenotype",
            "history",
            "symptom",
            "referral",
            "indication",
            "presentation",
            "vision",
            "retinal",
            "nyctalopia",
            "night blindness",
        )

        for report in reports:
            raw_text = (getattr(report, "raw_extracted_text", None) or "").splitlines()
            for raw_line in raw_text:
                line = " ".join(raw_line.split()).strip(" -•\t")
                if not line:
                    continue
                lowered = line.lower()
                if not any(keyword in lowered for keyword in keywords):
                    continue
                if line.lower().startswith("variant:"):
                    continue
                if line not in seen:
                    extracted_lines.append(line)
                    seen.add(line)

        if extracted_lines:
            return "\n".join(extracted_lines)

        summaries = []
        for report in reports:
            summary = (self._coerce_case(report).summary or "").strip()
            if not summary:
                continue
            lowered = summary.lower()
            if any(keyword in lowered for keyword in keywords):
                summaries.append(summary)

        if summaries:
            return "\n\n".join(summaries)

        return (
            "No explicit phenotype or referral history was extracted from the uploaded report. "
            "Current context is limited to the reported genomic finding and still needs clinician correlation."
        )

    def _build_ai_clinical_summary(self, variant_rows, evidence_map: dict[str, dict], decision) -> str:
        variant_label = self._variant_label(variant_rows)
        clinvar = evidence_map.get("clinvar", {})
        classification = clinvar.get("classification", "uncertain significance")
        return (
            f"The reported {variant_label} finding remains clinically review-required. "
            f"Current external evidence is most consistent with {classification.lower()} rather than a final autonomous interpretation, "
            "so the case should stay in clinician review rather than patient-facing release."
        )

    def _build_evidence_categorisation(
        self,
        evidence_map: dict[str, dict],
        evidence_statuses: dict[str, str],
    ) -> str:
        clinvar = evidence_map.get("clinvar", {})
        vep = evidence_map.get("vep", {})
        spliceai = evidence_map.get("spliceai", {})
        franklin = evidence_map.get("franklin", {})

        splice_label, splice_score = self._format_spliceai_effect(spliceai)
        franklin_bits = []
        for label, value in (
            ("functional", franklin.get("functional_data")),
            ("population", franklin.get("population_data")),
            ("in silico", franklin.get("in_silico_prediction")),
        ):
            if value:
                franklin_bits.append(f"{label} {value}")

        external_support = "; ".join(franklin_bits) if franklin_bits else "Unavailable"
        if evidence_statuses.get("franklin") == "fallback":
            external_support = f"{external_support} (Franklin fallback mode)"

        return "\n".join(
            [
                (
                    "Classification (ClinVar): "
                    f"{clinvar.get('classification', 'Unavailable')} "
                    f"({clinvar.get('review_status', 'review status unavailable')})."
                ),
                (
                    "Protein consequence (Ensembl VEP): "
                    f"{vep.get('most_severe_consequence', 'effect unavailable')} in "
                    f"{vep.get('biotype', 'unknown biotype')} transcript."
                ),
                (
                    "Splicing effect (SpliceAI): "
                    f"{splice_label} (max delta {splice_score:.2f}; low >0.20, moderate >0.50, high >0.80; "
                    f"AL {float(spliceai.get('acceptor_loss', 0.0) or 0.0):.2f}, "
                    f"DL {float(spliceai.get('donor_loss', 0.0) or 0.0):.2f}, "
                    f"AG {float(spliceai.get('acceptor_gain', 0.0) or 0.0):.2f}, "
                    f"DG {float(spliceai.get('donor_gain', 0.0) or 0.0):.2f})."
                ),
                f"Population / external support (Franklin): {external_support}.",
            ]
        )

    def _build_classification_snapshot(self, evidence_map: dict[str, dict]) -> str:
        clinvar = evidence_map.get("clinvar", {})
        vep = evidence_map.get("vep", {})
        return (
            f"Current external classification snapshot remains {clinvar.get('classification', 'unavailable').lower()}. "
            f"The retrieved consequence is {vep.get('most_severe_consequence', 'effect unavailable')} in a "
            f"{vep.get('biotype', 'unknown biotype')} transcript. "
            "This section is a source-grounded snapshot, not a formal ACMG evidence-code assignment."
        )

    def _build_clinical_integration(
        self,
        clinical_phenotype: str | None,
        variant_rows: list[VariantSummaryRow],
        evidence_map: dict[str, dict],
    ) -> str:
        gene = variant_rows[0].gene if variant_rows else "reported gene"
        phenotype_line = (clinical_phenotype or "").replace("\n", " ").strip()
        phenotype_lower = phenotype_line.lower()
        retinal_context = any(
            token in phenotype_lower
            for token in ("retinal", "nyctalopia", "night blindness", "vision loss")
        )
        if gene == "RPE65" and retinal_context:
            phenotype_note = "The uploaded clinical context is phenotype-compatible with inherited retinal disease."
        elif phenotype_line and not phenotype_line.startswith("No explicit phenotype"):
            phenotype_note = "The uploaded report includes phenotype context that should be checked against the reported variant."
        else:
            phenotype_note = "Phenotype context was not cleanly extractable from the uploaded report, so correlation remains manual."

        clinvar = evidence_map.get("clinvar", {})
        classification = clinvar.get("classification", "uncertain significance").lower()
        return (
            f"{gene} is clinically relevant to this review. {phenotype_note} "
            f"Current evidence remains aligned with {classification} rather than a stand-alone pathogenic conclusion, "
            "so clinician correlation is still required before any final interpretation."
        )

    def _build_expected_symptoms(
        self,
        clinical_phenotype: str | None,
        variant_rows: list[VariantSummaryRow],
    ) -> str:
        phenotype_lines = []
        for raw_line in (clinical_phenotype or "").splitlines():
            line = raw_line.strip()
            lowered = line.lower()
            if not line or line.startswith("No explicit phenotype"):
                continue
            if lowered.startswith("referral:") or lowered.startswith("history:"):
                continue
            if "phenotype" in lowered or any(
                token in lowered for token in ("nyctalopia", "night blindness", "vision loss", "retinal")
            ):
                phenotype_lines.append(line)

        if phenotype_lines:
            return "\n".join(phenotype_lines)

        genes = {row.gene for row in variant_rows if row.gene}
        if "RPE65" in genes:
            return "Progressive vision loss, night blindness, peripheral vision loss."
        return "Gene-/disease-associated phenotype was not clearly extractable from the uploaded report."

    def _build_recommendations(self, clinical_phenotype: str | None) -> str:
        phenotype_present = bool(clinical_phenotype and not clinical_phenotype.startswith("No explicit phenotype"))
        first_step = (
            "Correlate the reported variant with the extracted phenotype/history from the uploaded report."
            if phenotype_present
            else "Obtain or confirm phenotype/history details before final interpretation."
        )
        return "\n".join(
            [
                first_step,
                "Confirm transcript-level fit, zygosity, and overall variant context.",
                "Consider segregation testing or orthogonal confirmation if clinically indicated.",
                "Keep patient-facing release gated on clinician review and sign-off.",
            ]
        )

    def _variant_label(self, variant_rows: list[VariantSummaryRow]) -> str:
        if not variant_rows:
            return "reported variant"
        first = variant_rows[0]
        gene = first.gene or "reported gene"
        protein = first.protein_change or first.transcript_hgvs or "reported variant"
        return f"{gene} {protein}"

    def _format_spliceai_effect(self, spliceai: dict[str, object]) -> tuple[str, float]:
        scores = [
            float(spliceai.get("acceptor_loss", 0.0) or 0.0),
            float(spliceai.get("donor_loss", 0.0) or 0.0),
            float(spliceai.get("acceptor_gain", 0.0) or 0.0),
            float(spliceai.get("donor_gain", 0.0) or 0.0),
        ]
        max_score = max(scores) if scores else 0.0
        if max_score > 0.80:
            return "high predicted splice impact", max_score
        if max_score > 0.50:
            return "moderate predicted splice impact", max_score
        if max_score > 0.20:
            return "low predicted splice impact", max_score
        return "minimal predicted splice impact", max_score
