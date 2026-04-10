import { Navigate, useParams } from 'react-router-dom'
import { SectionCard } from '../../components/SectionCard'
import { StatusPill } from '../../components/StatusPill'
import { getDemoCase } from './mockCases'

export function CaseWorkspacePage() {
  const { caseId } = useParams()
  const caseData = getDemoCase(caseId)

  if (!caseData) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="space-y-6">
      <SectionCard
        eyebrow={`Case ${caseData.id} · ${caseData.status}`}
        title={`${caseData.patientName} · ${caseData.referralQuestion}`}
        aside={<StatusPill status={caseData.status} />}
      >
        <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
          <div className="space-y-3">
            <p className="text-text">{caseData.summary}</p>
            <p className="text-sm text-text-muted">Variant input: {caseData.variantText}</p>
            <p className="text-sm text-text-muted">Source: {caseData.sourceReport}</p>
          </div>
          <aside className="space-y-3">
            <p className="eyebrow">Workflow outcome</p>
            <div className="rounded-2xl border border-white/10 bg-surface-2 p-4">
              <p className="mb-2 text-xs text-text-muted uppercase tracking-[0.16em]">Recommendation</p>
              <p className="text-sm font-medium text-text">{caseData.recommendation}</p>
            </div>
            <button
              type="button"
              className="w-full rounded-2xl border border-white/15 bg-white/5 px-4 py-3 text-sm font-medium text-text"
            >
              Re-run workflow
            </button>
          </aside>
        </div>
      </SectionCard>

      <SectionCard eyebrow="Evidence" title="Evidence bundle for clinician review">
        <div className="space-y-4">
          {caseData.evidence.map((item) => (
            <div key={item.label} className="rounded-2xl border border-white/10 bg-surface-2 p-4">
              <p className="mb-1 text-sm font-semibold text-text">{item.label}</p>
              <p className="text-sm text-text-muted">{item.value}</p>
              {item.detail ? <p className="mt-2 text-xs text-text-muted">{item.detail}</p> : null}
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard eyebrow="Clinical control" title="Uncertainty & missing data" aside={<span className="text-xs uppercase tracking-[0.2em] text-text-muted">fail-closed</span>}>
        <p className="text-sm text-text-muted">{caseData.uncertainty}</p>
        <p className="mt-2 text-sm text-text">Next step: {caseData.nextStep}</p>

        {caseData.missing.length ? (
          <ul className="mt-4 list-disc pl-5 text-sm text-text-muted">
            {caseData.missing.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}
      </SectionCard>
    </div>
  )
}
