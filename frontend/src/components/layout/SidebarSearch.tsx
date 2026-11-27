import { useState, type KeyboardEvent, type RefObject } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

import { cn } from '../../utils/cn'
import { NAV_ITEMS } from './navigation'

type SidebarSearchProps = {
  inputRef: RefObject<HTMLInputElement | null>
  onNavigate?: () => void
}

export function SidebarSearch({ inputRef, onNavigate }: SidebarSearchProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')

  const cleanQuery = query.trim().toLowerCase()
  const results = cleanQuery
    ? NAV_ITEMS.filter((item) => t(item.labelKey).toLowerCase().includes(cleanQuery))
    : []

  function goTo(path: string) {
    navigate(path)
    setQuery('')
    inputRef.current?.blur()
    onNavigate?.()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter' && results.length > 0) goTo(results[0].to)
    if (event.key === 'Escape') {
      setQuery('')
      inputRef.current?.blur()
    }
  }

  return (
    <div className="relative">
      {cleanQuery && (
        <ul className="absolute bottom-full mb-1 w-full rounded-box border border-border bg-surface py-1">
          {results.length === 0 && (
            <li className="px-3 py-2 text-xs text-muted">{t('nav.noResults')}</li>
          )}

          {results.map((item, index) => (
            <li key={item.to}>
              <button
                type="button"
                onClick={() => goTo(item.to)}
                className={cn(
                  'w-full px-3 py-2 text-left text-sm hover:text-fg',
                  index === 0 ? 'text-fg' : 'text-muted',
                )}
              >
                {t(item.labelKey)}
              </button>
            </li>
          ))}
        </ul>
      )}

      <label className="flex h-8 items-center gap-2 rounded-box border border-border px-2 focus-within:border-fg">
        <span className="sr-only">{t('nav.searchLabel')}</span>

        <input
          ref={inputRef}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('nav.search')}
          className="min-w-0 flex-1 bg-transparent text-sm text-fg outline-none placeholder:text-muted"
        />

        <kbd className="font-mono text-[10px] text-muted">/</kbd>
      </label>
    </div>
  )
}
