import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

export function NotFoundPage() {
  const { t } = useTranslation()

  return (
    <div className="mt-6">
      <p className="font-mono text-6xl text-accent">404</p>
      <h1 className="mt-4 font-mono text-2xl">{t('notFound.title')}</h1>
      <p className="mt-2 text-sm text-muted">{t('notFound.text')}</p>
      <Link to="/" className="mt-8 inline-block font-mono text-xs underline underline-offset-4 hover:text-accent">
        ← {t('notFound.back')}
      </Link>
    </div>
  )
}
