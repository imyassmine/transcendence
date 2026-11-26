import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

type LegalSection = {
  title: string
  body: string
}

export function LegalPage({ kind }: { kind: 'privacy' | 'terms' }) {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const sections = t(`${kind}.sections`, { returnObjects: true }) as LegalSection[]

  return (
    <article className="mt-6">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="rounded-box font-mono text-xs text-muted hover:text-fg"
      >
        ← {t('legal.back')}
      </button>

      <h1 className="mt-4 font-mono text-2xl">{t(`${kind}.title`)}</h1>
      <p className="mt-1 font-mono text-xs text-muted">{t('legal.updated')}</p>
      <p className="mt-4 border-l-2 border-warning pl-3 text-xs text-warning">{t('legal.draft')}</p>

      <p className="mt-8 leading-relaxed">{t(`${kind}.intro`)}</p>

      <ol className="mt-8 flex flex-col gap-6">
        {sections.map((section, index) => (
          <li key={section.title} className="border-t border-border pt-4">
            <h2 className="font-mono text-sm">
              <span className="text-muted">§{index + 1}</span> {section.title}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">{section.body}</p>
          </li>
        ))}
      </ol>
    </article>
  )
}
