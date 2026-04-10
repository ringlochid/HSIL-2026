import type { DemoCase } from '../../types/demo'

export const demoCases: DemoCase[] = [
  {
    id: 'ravi',
    patientName: 'Ravi',
    title: 'Inherited retinal disease triage',
    status: 'ready',
    diseaseFocus: 'IRD / referral-support lane',
    referralQuestion: 'Does this case support escalation to specialist inherited retinal review?',
    summary:
      'Golden-path case for the live demo. Enough evidence exists to generate a grounded referral-support draft and still show uncertainty language.',
    variantText: 'NM_000350.3:c.2991+1655A>G (RPE65-associated context)',
    sourceReport:
      'Existing genomic report plus phenotype notes are already available. Backend should parse, enrich, and draft a reviewable next-step recommendation.',
    recommendation:
      'Supports referral to specialist inherited retinal review, pending clinician confirmation and completion of the missing phenotype checklist.',
    uncertainty:
      'Recommendation is assistive only. Final referral decision stays with the clinician and depends on phenotype confirmation and local pathway rules.',
    nextStep:
      'Open the clinician review board, confirm phenotype evidence, then export the final referral-support note.',
    missing: ['Confirm phenotype checklist', 'Confirm local referral destination'],
    evidence: [
      {
        label: 'Variant annotation',
        value: 'RPE65-linked variant parsed and normalized',
        detail: 'Use Franklin/VEP to turn raw variant text into structured transcript-level evidence.',
      },
      {
        label: 'Clinical evidence',
        value: 'ClinVar + disease-specific references',
        detail: 'Show classification context, review status, and any disease-specific evidence used in the draft.',
      },
      {
        label: 'Workflow status',
        value: 'Ready for draft generation',
        detail: 'This is the case we should keep polished for the live judge demo.',
      },
    ],
  },
  {
    id: 'owen',
    patientName: 'Owen',
    title: 'Blocked comparison case',
    status: 'blocked',
    diseaseFocus: 'Same workflow, incomplete evidence branch',
    referralQuestion: 'Can the system safely avoid overclaiming when evidence is incomplete?',
    summary:
      'Side-by-side blocked case used to prove the app is fail-closed instead of pretending certainty.',
    variantText: 'Candidate variant present, but supporting phenotype and pathway evidence are incomplete.',
    sourceReport:
      'Input report is not enough to support an automated recommendation. The app should surface missing fields, not hallucinate a confident answer.',
    recommendation:
      'Insufficient evidence for automated recommendation. Hold for clinician review and collect the missing case details.',
    uncertainty:
      'The correct behavior here is a visible block, not a weak or generic recommendation.',
    nextStep:
      'Capture the missing phenotype and referral details, then rerun the narrow workflow.',
    missing: ['Phenotype details', 'Referral pathway lock', 'Disease-specific evidence mapping'],
    evidence: [
      {
        label: 'Annotation coverage',
        value: 'Partial',
        detail: 'The app should still return structured status, even if live evidence calls fail or coverage is incomplete.',
      },
      {
        label: 'Decision status',
        value: 'Blocked by missing information',
        detail: 'This case demonstrates safe fallback behavior during the demo.',
      },
    ],
  },
]

export function getDemoCase(caseId?: string) {
  return demoCases.find((item) => item.id === caseId)
}
