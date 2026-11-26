const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function isValidEmail(email: string): boolean {
  return EMAIL_REGEX.test(email.trim())
}

export const PASSWORD_RULES = [
  { key: 'length',  test: (p: string) => p.length >= 8 && p.length <= 128 },
  { key: 'upper',   test: (p: string) => /[A-Z]/.test(p) },
  { key: 'lower',   test: (p: string) => /[a-z]/.test(p) },
  { key: 'digit',   test: (p: string) => /\d/.test(p) },
  { key: 'special', test: (p: string) => /[^A-Za-z0-9]/.test(p) },
] as const

export function isStrongPassword(password: string): boolean {
  return PASSWORD_RULES.every((rule) => rule.test(password))
}
