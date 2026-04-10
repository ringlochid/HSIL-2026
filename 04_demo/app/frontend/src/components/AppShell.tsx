import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Dashboard', exact: true },
  { to: '/cases/ravi', label: 'Hero case', exact: false },
  { to: '/review', label: 'Review board', exact: false },
]

const flowSteps = [
  'case intake',
  'variant tools',
  'evidence merge',
  'narrow rules',
  'draft output',
  'clinician review',
]

export function AppShell() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-white/8 bg-black/10 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4 sm:px-6 lg:px-8">
          <div>
            <p className="eyebrow">HSIL 2026</p>
            <h1 className="mt-2 text-xl font-semibold tracking-tight text-text sm:text-2xl">
              Genomic referral-support demo
            </h1>
          </div>
          <div className="hidden rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-right text-sm text-text-muted md:block">
            <div>frontend: Vite + React TS + Tailwind v4</div>
            <div>backend: thin API + tools + review gate</div>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-5 py-6 sm:px-6 lg:grid-cols-[260px_minmax(0,1fr)] lg:px-8">
        <aside className="space-y-6">
          <nav className="surface-card p-4">
            <p className="eyebrow mb-3">Navigation</p>
            <div className="space-y-2">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.exact}
                  className={({ isActive }) =>
                    [
                      'flex items-center justify-between rounded-2xl border px-4 py-3 text-sm font-medium transition',
                      isActive
                        ? 'border-primary/40 bg-primary-soft text-on-primary'
                        : 'border-white/8 bg-white/4 text-text-muted hover:border-white/14 hover:text-text',
                    ].join(' ')
                  }
                >
                  <span>{item.label}</span>
                  <span className="text-xs uppercase tracking-[0.18em]">open</span>
                </NavLink>
              ))}
            </div>
          </nav>

          <section className="surface-card p-4">
            <p className="eyebrow mb-3">Core workflow</p>
            <ol className="space-y-3 text-sm text-text-muted">
              {flowSteps.map((step, index) => (
                <li key={step} className="flex items-center gap-3">
                  <span className="flex size-7 items-center justify-center rounded-full border border-white/10 bg-white/5 text-xs font-semibold text-text">
                    {index + 1}
                  </span>
                  <span className="capitalize">{step}</span>
                </li>
              ))}
            </ol>
          </section>
        </aside>

        <main className="min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
