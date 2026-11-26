export const LEGAL_DELAY_DAYS = 30

const DAY_MS = 24 * 60 * 60 * 1000

export function daysSince(iso: string): number {
  return Math.floor((Date.now() - new Date(iso).getTime()) / DAY_MS)
}

export function daysLeft(sentAt: string): number {
  return LEGAL_DELAY_DAYS - daysSince(sentAt)
}

export function addDays(iso: string, days: number): string {
  const date = new Date(iso)
  date.setDate(date.getDate() + days)
  return date.toISOString()
}

export function formatDate(iso: string, lang: string): string {
  return new Date(iso).toLocaleDateString(lang, { day: 'numeric', month: 'short', year: 'numeric' })
}
