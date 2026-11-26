import { useTranslation } from 'react-i18next'

import type { OrgState } from '../../data/organisations'
import { cn } from '../../utils/cn'
import { daysLeft, daysSince, LEGAL_DELAY_DAYS } from '../../utils/dates'
import { statusLabel } from '../../utils/status'

export function StatusTag({ state }: { state: OrgState }) {
  const { t } = useTranslation()
  const label = statusLabel(state, t)

  if (state.kind === 'todo') {
    return <span className="font-mono text-xs text-accent uppercase">{label}</span>
  }

  if (state.kind === 'erased') {
    return <span className="font-mono text-xs text-success uppercase">{label}</span>
  }

  const left = daysLeft(state.sentAt)

  return (
    <span title={label} className={cn('font-mono text-xs tabular-nums', left < 0 ? 'text-accent' : 'text-warning')}>
      {left < 0 ? t('status.overdue') : t('status.daysLeft', { count: left })}
    </span>
  )
}

export function DeadlineBar({ sentAt }: { sentAt: string }) {
  const elapsed = Math.min(Math.max(daysSince(sentAt), 0), LEGAL_DELAY_DAYS)
  const overdue = daysLeft(sentAt) < 0

  return (
    <div className="flex items-center gap-3">
      <div className="h-1 w-20 bg-border" aria-hidden="true">
        <div
          className={cn('h-full', overdue ? 'bg-accent' : 'bg-warning')}
          style={{ width: `${(elapsed / LEGAL_DELAY_DAYS) * 100}%` }}
        />
      </div>
      <StatusTag state={{ kind: 'pending', sentAt }} />
    </div>
  )
}
