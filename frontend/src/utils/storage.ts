export function loadString(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export function saveString(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    return
  }
}
