import type { CaseStatus } from '../types/demo'

const styles: Record<CaseStatus, string> = {
  ready: 'bg-success/16 text-success border-success/30',
  blocked: 'bg-danger/14 text-danger border-danger/30',
  reviewing: 'bg-warning/14 text-warning border-warning/30',
}

interface StatusPillProps {
  status: CaseStatus
}

export function StatusPill({ status }: StatusPillProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${styles[status]}`}
    >
      {status}
    </span>
  )
}
