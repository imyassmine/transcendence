import { useTranslation } from 'react-i18next'

import { Button } from '../components/ui/Button'

type RowState =
  | { kind: 'todo' }
  | { kind: 'pending'; daysLeft: number }
  | { kind: 'erased' }

type Row = {
  n: string
  site: string
  type: 'broker' | 'search' | 'social'
  risk: number
  state: RowState
}

const ROWS: Row[] = [
  { n: '01', site: '42 paris', type: 'broker', risk: 80, state: { kind: 'todo' } },
  { n: '02', site: '42 lisbon', type: 'search', risk: 60, state: { kind: 'pending', daysLeft: 8 } },
  { n: '03', site: '42 tokyo', type: 'social', risk: 30, state: { kind: 'erased' } },
]

export function HomePage() {
  const { t } = useTranslation()
  const pendingCount = ROWS.filter((row) => row.state.kind === 'pending').length

  return (
    <>
      <h1 className="font-mono text-3xl leading-tight md:text-4xl">
        {t('home.title', { count: ROWS.length })}
      </h1>
      <p className="mt-3 text-muted">{t('home.subtitle', { count: pendingCount })}</p>

      <table className="mt-10 w-full border-collapse text-sm">
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
          {ROWS.map((row) => (
            <tr key={row.n} className="border-b border-border">
              <td className="py-3 font-mono text-muted">{row.n}</td>
              <td className="py-3 font-medium">{row.site}</td>
              <td className="py-3 text-muted">{t(`home.types.${row.type}`)}</td>
              <td className="py-3 font-mono tabular-nums">{row.risk}</td>
              <td className="py-3 text-right">
                <RowStatus site={row.site} state={row.state} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}

function RowStatus({ site, state }: { site: string; state: RowState }) {
  const { t } = useTranslation()

  if (state.kind === 'todo') {
    return (
      <Button size="sm" aria-label={t('home.startLabel', { site })}>
        {t('home.start')}
      </Button>
    )
  }

  if (state.kind === 'pending') {
    return (
      <span
        className="font-mono text-xs text-warning"
        title={t('home.daysLeftLabel', { count: state.daysLeft })}
      >
        {t('home.daysLeft', { count: state.daysLeft })}
      </span>
    )
  }

  return <span className="font-mono text-xs text-success uppercase">{t('home.erased')}</span>
}
