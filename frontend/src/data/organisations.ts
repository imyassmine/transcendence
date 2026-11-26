export type OrgType = 'broker' | 'search' | 'social' | 'breach'

export type DataKind = 'name' | 'email' | 'phone' | 'address' | 'birthdate' | 'photo' | 'password'

export type OrgState =
  | { kind: 'todo' }
  | { kind: 'pending'; sentAt: string }
  | { kind: 'erased'; sentAt: string; erasedAt: string }

export type Organisation = {
  id: string
  site: string
  domain: string
  type: OrgType
  risk: number
  found: DataKind[]
  state: OrgState
}

export type RiskLevel = 'high' | 'medium' | 'low'

function daysAgo(n: number): string {
  const date = new Date()
  date.setDate(date.getDate() - n)
  return date.toISOString()
}

export const ORGANISATIONS: Organisation[] = [
  {
    id: 'paris',
    site: '42 paris',
    domain: '42paris.example',
    type: 'broker',
    risk: 80,
    found: ['name', 'email', 'address', 'phone'],
    state: { kind: 'todo' },
  },
  {
    id: 'berlin',
    site: '42 berlin',
    domain: '42berlin.example',
    type: 'breach',
    risk: 90,
    found: ['email', 'password'],
    state: { kind: 'pending', sentAt: daysAgo(25) },
  },
  {
    id: 'lisbon',
    site: '42 lisbon',
    domain: '42lisbon.example',
    type: 'search',
    risk: 60,
    found: ['name', 'photo', 'address'],
    state: { kind: 'pending', sentAt: daysAgo(22) },
  },
  {
    id: 'madrid',
    site: '42 madrid',
    domain: '42madrid.example',
    type: 'social',
    risk: 45,
    found: ['name', 'photo', 'birthdate'],
    state: { kind: 'todo' },
  },
  {
    id: 'tokyo',
    site: '42 tokyo',
    domain: '42tokyo.example',
    type: 'social',
    risk: 30,
    found: ['name', 'email'],
    state: { kind: 'erased', sentAt: daysAgo(40), erasedAt: daysAgo(12) },
  },
]

export function findOrganisation(id: string): Organisation | undefined {
  return ORGANISATIONS.find((org) => org.id === id)
}

export function riskLevel(risk: number): RiskLevel {
  if (risk >= 70) return 'high'
  if (risk >= 40) return 'medium'
  return 'low'
}
