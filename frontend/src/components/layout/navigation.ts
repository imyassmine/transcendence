export type NavItem = {
  to: string
  labelKey: string
  shortcut: string
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/',              labelKey: 'nav.dossier',       shortcut: '1' },
  { to: '/requests',      labelKey: 'nav.requests',      shortcut: '2' },
  { to: '/notifications', labelKey: 'nav.notifications', shortcut: '3' },
  { to: '/api-keys',      labelKey: 'nav.apiKeys',       shortcut: '4' },
  { to: '/profile',       labelKey: 'nav.profile',       shortcut: '5' },
]

export function navNumber(index: number): string {
  return String(index + 1).padStart(2, '0')
}
