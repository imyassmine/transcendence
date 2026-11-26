export type NavItem = {
  to: string
  labelKey: string
  shortcut: string
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/',              labelKey: 'nav.dossier',       shortcut: '1' },
  { to: '/notifications', labelKey: 'nav.notifications', shortcut: '2' },
]

export function navNumber(index: number): string {
  return String(index + 1).padStart(2, '0')
}
