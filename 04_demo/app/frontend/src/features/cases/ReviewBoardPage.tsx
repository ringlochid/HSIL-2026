import { demoCases } from './mockCases'
import { SectionCard } from '../../components/SectionCard'
import { StatusPill } from '../../components/StatusPill'

export function ReviewBoardPage() {
  return (
    <div className="space-y-6">
      <SectionCard eyebrow="Review gate" title="Clinician review lane">
        <p className="text-text-muted">This page mirrors what a reviewer sees before finalizing output.</p>
        <div className="mt-4 space-y-4">
          {demoCases.map((item) => (
            <article key={item.id} className="surface-card-muted border border-white/10 p-4">
              <div className="mb-2 flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-base font-semibold text-text">{item.patientName}</h3>
                  <p className="text-sm text-text-muted">{item.title}</p>
                </div>
                <StatusPill status={item.status} />
              </div>
              <p className="text-sm text-text-muted">{item.recommendation}</p>
            </article>
          ))}
        </div>
      </SectionCard>

      <SectionCard eyebrow="Safety rule" title="No autonomous decisions in demo">
        <p className="text-sm text-text-muted">
          All recommendations are draft-level outputs. The final action remains a human decision.
        </p>
      </SectionCard>
    </div>
  )
}
