import { Link } from 'react-router-dom'
import { SectionCard } from '../../components/SectionCard'
import { StatusPill } from '../../components/StatusPill'
import { demoCases } from './mockCases'

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <section className="surface-card p-6 sm:p-7">
        <p className="eyebrow">What this demo proves</p>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight text-text sm:text-3xl">Clinical decision-support, not generic report generation</h2>
        <p className="mt-4 max-w-3xl text-text-muted">
          We keep one narrow decision lane, apply deterministic referral logic, and keep the AI used for
          evidence phrasing + draft rendering only.
        </p>
      </section>

      <SectionCard eyebrow="Case list" title="Demo cases">
        <div className="grid gap-4 md:grid-cols-2">
          {demoCases.map((caseItem) => (
            <article key={caseItem.id} className="surface-card-muted p-4 sm:p-5">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-text-muted">{caseItem.id}</p>
                  <h3 className="text-lg font-semibold text-text">{caseItem.title}</h3>
                  <p className="text-sm text-text-muted">{caseItem.diseaseFocus}</p>
                </div>
                <StatusPill status={caseItem.status} />
              </div>

              <p className="mb-5 text-sm text-text-muted">{caseItem.summary}</p>

              <Link
                to={`/cases/${caseItem.id}`}
                className="inline-flex items-center rounded-xl border border-primary/40 bg-primary-soft px-4 py-2 text-sm font-semibold text-on-primary"
              >
                Open case workspace
              </Link>
            </article>
          ))}
        </div>
      </SectionCard>
    </div>
  )
}
