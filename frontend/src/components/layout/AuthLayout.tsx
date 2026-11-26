import { useTranslation } from 'react-i18next'
import { Link, Outlet } from 'react-router-dom'

import { cn } from '../../utils/cn'
import { LanguageSelect } from '../ui/LanguageSelect'
import { ThemeToggle } from '../ui/ThemeToggle'

export function AuthLayout({ wide = false }: { wide?: boolean }) {
  const { t } = useTranslation()

  return (
    <div className="flex min-h-dvh flex-col px-4">
      <div className="flex justify-end gap-4 py-4">
        <LanguageSelect />
        <ThemeToggle />
      </div>

      <main className={cn('flex flex-1 justify-center', wide ? 'items-start py-8' : 'items-center pb-16')}>
        <div className={cn('w-full', wide ? 'max-w-2xl' : 'max-w-sm')}>
          <Link to="/" className="block border-b border-fg pb-3 font-mono text-xs tracking-widest uppercase">
            {t('app.name')}
          </Link>

          <Outlet />
        </div>
      </main>

      <footer className="flex justify-center gap-4 py-6 font-mono text-xs text-muted">
        <Link to="/privacy" className="hover:text-fg">{t('nav.privacy')}</Link>
        <Link to="/terms" className="hover:text-fg">{t('nav.terms')}</Link>
      </footer>
    </div>
  )
}
