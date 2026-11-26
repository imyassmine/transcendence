import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { SectionTitle } from '../components/ui/PageHeader'
import { DeadlineBar, StatusTag } from '../components/ui/StatusTag'
import { mockLetter, type Letter } from '../data/letters'
import { findOrganisation } from '../data/organisations'
import { MOCK_USER } from '../data/user'
import { addDays, formatDate, LEGAL_DELAY_DAYS } from '../utils/dates'
import { NotFoundPage } from './NotFoundPage'

export function RequestPage() {
  const { t, i18n } = useTranslation()
  const { id = '' } = useParams()
  const org = findOrganisation(id)

  const [letter, setLetter] = useState<Letter | null>(null)
  const [copied, setCopied] = useState(false)
  const [sentAt, setSentAt] = useState<string | null>(
    org && org.state.kind !== 'todo' ? org.state.sentAt : null,
  )

  useEffect(() => {
    if (!org) return
    const timer = setTimeout(() => setLetter(mockLetter(org, MOCK_USER.name, MOCK_USER.email)), 600)
    return () => clearTimeout(timer)
  }, [org])

  if (!org) return <NotFoundPage />

  const date = (iso: string) => formatDate(iso, i18n.language)
  const erased = org.state.kind === 'erased'

  async function copyLetter() {
    if (!letter) return
    try {
      await navigator.clipboard.writeText(`${letter.subject}\n\n${letter.body}`)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  const mailto = letter?.recipient_email
    ? `mailto:${letter.recipient_email}?subject=${encodeURIComponent(letter.subject)}&body=${encodeURIComponent(letter.body)}`
    : null

  return (
    <>
      <Link to="/requests" className="font-mono text-xs text-muted hover:text-fg">
        ← {t('nav.requests')}
      </Link>

      <h1 className="mt-4 font-mono text-3xl">{org.site}</h1>
      <p className="mt-1 text-muted">{t('letter.title')}</p>
      <p className="mt-1 font-mono text-xs text-warning">{t('letter.demo')}</p>

      <div className="mt-8 border-t border-fg pt-4">
        {erased && org.state.kind === 'erased' ? (
          <StatusTag state={org.state} />
        ) : sentAt ? (
          <div className="flex flex-col gap-2">
            <p className="text-sm text-muted">
              {t('letter.sent', { date: date(sentAt) })} · {t('letter.deadline', { date: date(addDays(sentAt, LEGAL_DELAY_DAYS)) })}
            </p>
            <DeadlineBar sentAt={sentAt} />
          </div>
        ) : (
          <StatusTag state={{ kind: 'todo' }} />
        )}
      </div>

      {!letter ? (
        <p role="status" className="mt-10 font-mono text-sm text-muted">{t('letter.generating')}</p>
      ) : (
        <>
          <section className="mt-10">
            <SectionTitle>{t('letter.draft')}</SectionTitle>

            <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
              <dt className="font-mono text-xs text-muted uppercase">{t('letter.to')}</dt>
              <dd className="font-mono break-all">{letter.recipient_email ?? '—'}</dd>

              {letter.contact_url && (
                <>
                  <dt className="font-mono text-xs text-muted uppercase">{t('letter.contactPage')}</dt>
                  <dd className="font-mono break-all text-muted">{letter.contact_url}</dd>
                </>
              )}

              <dt className="font-mono text-xs text-muted uppercase">{t('letter.subject')}</dt>
              <dd>{letter.subject}</dd>
            </dl>

            <pre className="mt-4 rounded-box border border-border bg-surface p-4 font-mono text-sm leading-relaxed whitespace-pre-wrap">
              {letter.body}
            </pre>

            <p className="mt-3 font-mono text-xs text-muted">
              {letter.legal_refs.join(' · ')} — {t(`letter.generatedBy.${letter.generated_by}`)}
            </p>

            {letter.warnings.length > 0 && (
              <ul className="mt-3 border-l-2 border-warning pl-3 text-xs text-warning">
                {letter.warnings.map((warning) => <li key={warning}>{warning}</li>)}
              </ul>
            )}
          </section>

          {!erased && (
            <div className="mt-6 flex flex-wrap gap-2">
              <Button variant="secondary" onClick={() => void copyLetter()}>
                {copied ? t('letter.copied') : t('letter.copy')}
              </Button>
              {mailto && (
                <a
                  href={mailto}
                  className="inline-flex h-10 items-center rounded-box border border-fg px-4 text-sm font-medium hover:bg-fg hover:text-bg"
                >
                  {t('letter.mail')}
                </a>
              )}
              {!sentAt && (
                <Button onClick={() => setSentAt(new Date().toISOString())}>{t('letter.markSent')}</Button>
              )}
            </div>
          )}
        </>
      )}
    </>
  )
}
