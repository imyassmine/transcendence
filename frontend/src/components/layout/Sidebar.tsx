import type { RefObject } from 'react'
import { useTranslation } from 'react-i18next'
import { NavLink } from 'react-router-dom'

import { cn } from '../../utils/cn'
import { LanguageSelect } from '../ui/LanguageSelect'
import { ThemeToggle } from '../ui/ThemeToggle'
import { NAV_ITEMS, navNumber } from './navigation'
import { SidebarSearch } from './SidebarSearch'

type SidebarProps = {
  collapsed: boolean
  searchRef: RefObject<HTMLInputElement | null>
  onLogout: () => void
  onToggleCollapse?: () => void
  onClose?: () => void
}

function rowClasses(isActive: boolean, collapsed: boolean): string {
  return cn(
    'flex h-9 w-full items-center gap-3 border-l-2 px-2 text-sm transition-colors',
    collapsed && 'justify-center',
    isActive ? 'border-accent text-fg' : 'border-transparent text-muted hover:text-fg',
  )
}

export function Sidebar({ collapsed, searchRef, onLogout, onToggleCollapse, onClose }: SidebarProps) {
  const { t } = useTranslation()

  return (
    <nav aria-label={t('nav.label')} className="flex h-full flex-col gap-8 border-r border-border bg-surface px-3 py-6">
      <div className={cn('flex items-center border-b border-fg pb-3', collapsed ? 'justify-center' : 'justify-between')}>
        {!collapsed && (
          <span className="font-mono text-xs tracking-widest uppercase">{t('app.name')}</span>
        )}

        {onToggleCollapse && (
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label={collapsed ? t('nav.expand') : t('nav.collapse')}
            title={`${collapsed ? t('nav.expand') : t('nav.collapse')} ( [ )`}
            className="rounded-box font-mono text-xs text-muted hover:text-fg"
          >
            {collapsed ? '»' : '«'}
          </button>
        )}

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label={t('nav.closeMenu')}
            className="rounded-box font-mono text-sm text-muted hover:text-fg"
          >
            ×
          </button>
        )}
      </div>

      <ol className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item, index) => {
          const label = t(item.labelKey)

          return (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === '/'}
                onClick={onClose}
                title={collapsed ? label : t('nav.shortcut', { key: item.shortcut })}
                className={({ isActive }) => rowClasses(isActive, collapsed)}
              >
                {({ isActive }) => (
                  <>
                    <span className={cn('font-mono text-xs tabular-nums', isActive ? 'text-accent' : 'text-muted')}>
                      {navNumber(index)}
                    </span>

                    {collapsed ? (
                      <span className="sr-only">{label}</span>
                    ) : (
                      <>
                        <span className="flex-1 truncate">{label}</span>
                        <kbd className="font-mono text-[10px] text-muted">{item.shortcut}</kbd>
                      </>
                    )}
                  </>
                )}
              </NavLink>
            </li>
          )
        })}
      </ol>

      <div className="flex flex-col gap-4 border-t border-border pt-4">
        {!collapsed && <SidebarSearch inputRef={searchRef} onNavigate={onClose} />}

        <button
          type="button"
          onClick={onLogout}
          title={collapsed ? t('nav.logout') : undefined}
          className={rowClasses(false, collapsed)}
        >
          {collapsed ? (
            <span className="font-mono text-xs">⏻</span>
          ) : (
            <>
              <span className="flex-1 text-left">{t('nav.logout')}</span>
              <kbd className="font-mono text-[10px] text-muted">X</kbd>
            </>
          )}
        </button>

        <div className={cn('flex items-center px-2', collapsed ? 'flex-col gap-3' : 'justify-between')}>
          <LanguageSelect />
          <ThemeToggle />
        </div>
      </div>
    </nav>
  )
}
