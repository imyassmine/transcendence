import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { StatusTag } from '../components/ui/StatusTag'
import { ORGANISATIONS } from '../data/organisations'

export function HomePage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const pendingCount = ORGANISATIONS.filter((org) => org.state.kind === 'pending').length

  return (
    <>
      <h1 className="font-mono text-3xl leading-tight md:text-4xl">
        {t('home.title', { count: ORGANISATIONS.length })}
      </h1>
      <p className="mt-3 text-muted">{t('home.subtitle', { count: pendingCount })}</p>

      <div className="mt-10 overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left font-mono text-xs text-muted uppercase">
              <th className="py-2 font-normal">{t('home.columns.n')}</th>
              <th className="py-2 font-normal">{t('home.columns.organisation')}</th>
              <th className="py-2 font-normal">{t('home.columns.type')}</th>
              <th className="py-2 font-normal">{t('home.columns.risk')}</th>
              <th className="py-2 text-right font-normal">{t('home.columns.state')}</th>
            </tr>
          </thead>
          <tbody>
            {ORGANISATIONS.map((org, index) => (
              <tr key={org.id} className="border-b border-border">
                <td className="py-3 pr-3 font-mono text-muted">{String(index + 1).padStart(2, '0')}</td>
                <td className="py-3 pr-3 font-medium">
                  <Link to={`/organisations/${org.id}`} className="underline-offset-4 hover:underline">
                    {org.site}
                  </Link>
                </td>
                <td className="py-3 pr-3 text-muted">{t(`types.${org.type}`)}</td>
                <td className="py-3 pr-3 font-mono tabular-nums">{org.risk}</td>
                <td className="py-3 text-right">
                  {org.state.kind === 'todo' ? (
                    <Button
                      size="sm"
                      aria-label={t('home.startLabel', { site: org.site })}
                      onClick={() => navigate(`/requests/${org.id}`)}
                    >
                      {t('home.start')}
                    </Button>
                  ) : (
                    <StatusTag state={org.state} />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
