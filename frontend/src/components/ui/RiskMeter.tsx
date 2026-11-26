import { useTranslation } from 'react-i18next'

import { riskLevel } from '../../data/organisations'
import { cn } from '../../utils/cn'

const FILL = {
  high: 'bg-accent',
  medium: 'bg-warning',
  low: 'bg-success',
}

export function RiskMeter({ value }: { value: number }) {
  const { t } = useTranslation()
  const level = riskLevel(value)

  return (
    <div className="flex items-center gap-3">
      <span className="font-mono text-2xl tabular-nums">{value}</span>
      <div className="flex flex-1 flex-col gap-1">
        <div className="h-1 w-full bg-border" aria-hidden="true">
          <div className={cn('h-full', FILL[level])} style={{ width: `${value}%` }} />
        </div>
        <span className="font-mono text-xs text-muted">{t(`risk.${level}`)}</span>
      </div>
    </div>
  )
}
