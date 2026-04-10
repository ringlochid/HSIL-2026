import type { PropsWithChildren, ReactNode } from 'react'

interface SectionCardProps extends PropsWithChildren {
  eyebrow?: string
  title: string
  aside?: ReactNode
}

export function SectionCard({ eyebrow, title, aside, children }: SectionCardProps) {
  return (
    <section className="surface-card p-6 sm:p-7">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h2 className="text-xl font-semibold tracking-tight text-text sm:text-2xl">{title}</h2>
        </div>
        {aside ? <div>{aside}</div> : null}
      </div>
      {children}
    </section>
  )
}
