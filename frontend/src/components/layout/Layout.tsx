import { NavLink, Outlet } from 'react-router-dom'

import { cn } from '../../lib/cn'

const LINKS = [
  { to: '/', label: 'Dossier' },
  { to: '/notifications', label: 'Notifications' },
]

export function Layout() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <header className="flex items-baseline justify-between border-b border-fg pb-3">
        <span className="font-mono text-xs tracking-widest uppercase">Transcendence</span>

        <nav className="flex gap-4">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/'}
              className={({ isActive }) =>
                cn('font-mono text-xs', isActive ? 'text-fg underline underline-offset-4' : 'text-muted hover:text-fg')
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mt-6">
        <Outlet />
      </main>
    </div>
  )
}
