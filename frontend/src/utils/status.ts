import type { TFunction } from 'i18next'

import type { OrgState } from '../data/organisations'
import { daysLeft } from './dates'

export function statusLabel(state: OrgState, t: TFunction): string {
  if (state.kind === 'todo') return t('status.todo')
  if (state.kind === 'erased') return t('status.erased')

  const left = daysLeft(state.sentAt)
  if (left < 0) return t('status.overdue')
  return t('status.daysLeftLabel', { count: left })
}
