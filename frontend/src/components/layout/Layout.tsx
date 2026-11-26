import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Outlet, useNavigate } from 'react-router-dom'

import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import { cn } from '../../utils/cn'
import { loadString, saveString } from '../../utils/storage'
import { NAV_ITEMS } from './navigation'
import { Sidebar } from './Sidebar'

export function Layout() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const searchRef = useRef<HTMLInputElement>(null)

  const [collapsed, setCollapsed] = useState(() => loadString('sidebar') === 'collapsed')
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    saveString('sidebar', collapsed ? 'collapsed' : 'expanded')
  }, [collapsed])

  const logout = useCallback(() => {
    navigate('/login')
  }, [navigate])

  const shortcuts = useMemo(() => {
    const map: Record<string, () => void> = {
      '/': () => {
        setCollapsed(false)
        setTimeout(() => searchRef.current?.focus(), 0)
      },
      '[': () => setCollapsed((value) => !value),
      'x': logout,
    }

    for (const item of NAV_ITEMS) {
      map[item.shortcut] = () => navigate(item.to)
    }

    return map
  }, [navigate, logout])

  useKeyboardShortcuts(shortcuts)

  return (
    <div className="flex min-h-dvh">
      <aside
        className={cn(
          'sticky top-0 hidden h-dvh shrink-0 transition-[width] duration-200 md:block',
          collapsed ? 'w-16' : 'w-60',
        )}
      >
        <Sidebar
          collapsed={collapsed}
          searchRef={searchRef}
          onLogout={logout}
          onToggleCollapse={() => setCollapsed((value) => !value)}
        />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-fg/40"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
          <aside className="relative h-full w-64 max-w-[85vw]">
            <Sidebar
              collapsed={false}
              searchRef={searchRef}
              onLogout={logout}
              onClose={() => setMobileOpen(false)}
            />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-between border-b border-fg px-4 py-3 md:hidden">
          <span className="font-mono text-xs tracking-widest uppercase">{t('app.name')}</span>
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            aria-label={t('nav.openMenu')}
            className="rounded-box font-mono text-xs text-muted hover:text-fg"
          >
            ≡
          </button>
        </div>

        <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 md:px-8 md:py-12">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
