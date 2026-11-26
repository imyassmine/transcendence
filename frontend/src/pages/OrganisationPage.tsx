import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { SectionTitle } from '../components/ui/PageHeader'
import { Button } from '../components/ui/Button'
import { RiskMeter } from '../components/ui/RiskMeter'
import { DeadlineBar, StatusTag } from '../components/ui/StatusTag'
import { findOrganisation } from '../data/organisations'
import { addDays, formatDate, LEGAL_DELAY_DAYS } from '../utils/dates'
import { NotFoundPage } from './NotFoundPage'

export function OrganisationPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { id = '' } = useParams()
  const org = findOrganisation(id)

  if (!org) return <NotFoundPage />

  const { state } = org

  return (
    <>
      <Link to="/" className="font-mono text-xs text-muted hover:text-fg">
        ← {t('nav.dossier')}
      </Link>

      <h1 className="mt-4 font-mono text-3xl">{org.site}</h1>
      <p className="mt-1 font-mono text-sm text-muted">
        {org.domain} · {t(`types.${org.type}`)}
      </p>

      <dl className="mt-10 grid grid-cols-1 gap-6 border-t border-fg pt-6 sm:grid-cols-2">
        <Field label={t('organisation.risk')}>
          <RiskMeter value={org.risk} />
        </Field>
        <Field label={t('organisation.status')}>
          <StatusTag state={state} />
        </Field>
      </dl>

      <section className="mt-12">
        <SectionTitle>{t('organisation.dataFound', { count: org.found.length })}</SectionTitle>
        <ul>
          {org.found.map((kind) => (
            <li key={kind} className="border-b border-border py-3 text-sm">
              {t(`dataKinds.${kind}`)}
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-12">
        <SectionTitle>{t('organisation.erasure')}</SectionTitle>

        {state.kind === 'todo' && (
          <div className="mt-4 flex flex-col items-start gap-4">
            <p className="text-sm text-muted">{t('organisation.todoText', { days: LEGAL_DELAY_DAYS })}</p>
            <Button onClick={() => navigate(`/requests/${org.id}`)}>{t('organisation.start')}</Button>
          </div>
        )}

        {state.kind === 'pending' && (
          <div className="mt-4 flex flex-col items-start gap-4">
            <p className="text-sm text-muted">
              {t('organisation.pendingText', {
                sent: formatDate(state.sentAt, i18n.language),
                deadline: formatDate(addDays(state.sentAt, LEGAL_DELAY_DAYS), i18n.language),
              })}
            </p>
            <DeadlineBar sentAt={state.sentAt} />
            <Link to={`/requests/${org.id}`} className="font-mono text-xs underline underline-offset-4 hover:text-accent">
              {t('organisation.viewRequest')} →
            </Link>
          </div>
        )}

        {state.kind === 'erased' && (
          <p className="mt-4 text-sm text-muted">
            {t('organisation.erasedText', { date: formatDate(state.erasedAt, i18n.language) })}
          </p>
        )}
      </section>
    </>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="font-mono text-xs tracking-wide text-muted uppercase">{label}</dt>
      <dd className="mt-2">{children}</dd>
    </div>
  )
}
