export type CaseStatus = 'ready' | 'blocked' | 'reviewing'

export interface EvidenceItem {
  label: string
  value: string
  detail?: string
}

export interface DemoCase {
  id: string
  patientName: string
  title: string
  status: CaseStatus
  diseaseFocus: string
  referralQuestion: string
  summary: string
  variantText: string
  sourceReport: string
  recommendation: string
  uncertainty: string
  nextStep: string
  missing: string[]
  evidence: EvidenceItem[]
}
