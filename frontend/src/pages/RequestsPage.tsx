import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { PageHeader, SectionTitle } from '../components/ui/PageHeader'
import { DeadlineBar } from '../components/ui/StatusTag'
import { ORGANISATIONS, type Organisation } from '../data/organisations'
import { addDays, formatDate, LEGAL_DELAY_DAYS } from '../utils/dates'

const HEAD = 'border-b border-border text-left font-mono text-xs text-muted uppercase'
const CELL = 'py-3 pr-3'

export function RequestsPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()

  const pending = ORGANISATIONS.filter((org) => org.state.kind === 'pending')
  const erased = ORGANISATIONS.filter((org) => org.state.kind === 'erased')
  const todo = ORGANISATIONS.filter((org) => org.state.kind === 'todo')

  const date = (iso: string) => formatDate(iso, i18n.language)

  return (
    <>
      <PageHeader title={t('requests.title')} subtitle={t('requests.subtitle', { days: LEGAL_DELAY_DAYS })} />
      <p className="mt-2 font-mono text-xs text-muted">
        {t('requests.summary', { pending: pending.length, erased: erased.length, todo: todo.length })}
      </p>

      <section className="mt-10">
        <SectionTitle>{t('requests.sections.pending')}</SectionTitle>
        {pending.length === 0 ? (
          <Empty />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className={HEAD}>
                  <th className="py-2 font-normal">{t('requests.columns.organisation')}</th>
                  <th className="py-2 font-normal">{t('requests.columns.sent')}</th>
                  <th className="py-2 font-normal">{t('requests.columns.deadline')}</th>
                  <th className="py-2 font-normal">{t('requests.columns.progress')}</th>
                </tr>
              </thead>
              <tbody>
                {pending.map((org) => org.state.kind === 'pending' && (
                  <tr key={org.id} className="border-b border-border">
                    <td className={CELL}><OrgLink org={org} /></td>
                    <td className={`${CELL} font-mono text-xs tabular-nums`}>{date(org.state.sentAt)}</td>
                    <td className={`${CELL} font-mono text-xs tabular-nums`}>
                      {date(addDays(org.state.sentAt, LEGAL_DELAY_DAYS))}
                    </td>
                    <td className="py-3"><DeadlineBar sentAt={org.state.sentAt} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="mt-10">
        <SectionTitle>{t('requests.sections.todo')}</SectionTitle>
        {todo.length === 0 ? (
          <Empty />
        ) : (
          <ul>
            {todo.map((org) => (
              <li key={org.id} className="flex items-center justify-between gap-3 border-b border-border py-3 text-sm">
                <span>
                  <OrgLink org={org} />
                  <span className="ml-3 font-mono text-xs text-muted">
                    {t('requests.columns.risk')} {org.risk}
                  </span>
                </span>
                <Button
                  size="sm"
                  aria-label={t('home.startLabel', { site: org.site })}
                  onClick={() => navigate(`/requests/${org.id}`)}
                >
                  {t('home.start')}
                </Button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mt-10">
        <SectionTitle>{t('requests.sections.erased')}</SectionTitle>
        {erased.length === 0 ? (
          <Empty />
        ) : (
          <ul>
            {erased.map((org) => org.state.kind === 'erased' && (
              <li key={org.id} className="flex items-center justify-between gap-3 border-b border-border py-3 text-sm">
                <OrgLink org={org} />
                <span className="font-mono text-xs text-success">
                  {t('requests.erasedOn', { date: date(org.state.erasedAt) })}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  )
}

function OrgLink({ org }: { org: Organisation }) {
  return (
    <Link to={`/requests/${org.id}`} className="font-medium underline-offset-4 hover:underline">
      {org.site}
    </Link>
  )
}

function Empty() {
  const { t } = useTranslation()
  return <p className="mt-4 text-sm text-muted">{t('requests.empty')}</p>
}
