import { api, ApiError } from './api'

const AUTH = '/api/v1/auth'

export type User = {
  id: string
  name: string
  email: string
}

export function login(email: string, password: string) {
  return api.post<User>(`${AUTH}/login`, { email, password })
}

export function me() {
  return api.get<User>(`${AUTH}/me`)
}

export async function register(name: string, email: string, password: string) {
  await api.post<User>(`${AUTH}/register`, { name, email, password })
  return login(email, password)
}

export function authErrorKey(error: unknown): string {
  if (!(error instanceof ApiError)) return 'auth.errors.network'
  if (error.status === 401) return 'auth.errors.invalidCredentials'
  if (error.status === 409) return 'auth.errors.emailTaken'
  if (error.status === 422) return 'auth.errors.invalidInput'
  return 'auth.errors.unknown'
}
