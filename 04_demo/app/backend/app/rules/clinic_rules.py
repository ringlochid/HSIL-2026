from __future__ import annotations

from app.rules.base import DecisionInput, DecisionOutput


class ClinicRules:
    def evaluate(self, payload: DecisionInput) -> DecisionOutput:
        clinvar = payload.evidence.get("clinvar", {})
        vep = payload.evidence.get("vep", {})
        spliceai = payload.evidence.get("spliceai", {})
        franklin = payload.evidence.get("franklin", {})

        evidence_lines = [
            f"ClinVar classification: {clinvar.get('classification', 'Unavailable')} ({clinvar.get('review_status', 'review status unavailable')}).",
            f"VEP: {vep.get('most_severe_consequence', 'effect unavailable')} in {vep.get('biotype', 'unknown biotype')} transcript.",
            f"SpliceAI: AL {spliceai.get('acceptor_loss', 0.0):.2f}, DL {spliceai.get('donor_loss', 0.0):.2f}, AG {spliceai.get('acceptor_gain', 0.0):.2f}, DG {spliceai.get('donor_gain', 0.0):.2f}.",
            f"Franklin signals: functional {franklin.get('functional_data', 'Unavailable')}, population {franklin.get('population_data', 'Unavailable')}, in silico {franklin.get('in_silico_prediction', 'Unavailable')}.",
        ]

        fallback_sources = [
            name for name, status in payload.evidence_statuses.items() if status == "fallback"
        ]
        warnings = []
        if fallback_sources:
            warnings.append(f"Fallback evidence mode for: {', '.join(sorted(fallback_sources))}.")

        uncertainty = (
            "ClinVar currently reports this variant as uncertain significance, and the overall evidence "
            "should be treated as support for clinician review rather than an autonomous referral decision."
        )
        recommendation = (
            f"Escalate {payload.case_title} for clinician review. The RPE65 p.Asp87Gly signal is biologically relevant, "
            "but the combined evidence remains review-required rather than final."
        )
        next_step = "Confirm phenotype alignment, validate transcript-level fit, and complete human review before any final output."
        return DecisionOutput(
            recommendation=recommendation,
            evidence_lines=evidence_lines,
            uncertainty=uncertainty,
            next_step=next_step,
            confidence_label="medium",
            warnings=warnings,
        )
