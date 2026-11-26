import { useState, type ReactNode } from 'react'

import { saveString } from '../utils/storage'
import { ThemeContext, type Theme } from './ThemeContext'

function readInitialTheme(): Theme {
  const forced = document.documentElement.dataset.theme
  if (forced === 'light' || forced === 'dark') return forced

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(readInitialTheme)

  function toggleTheme() {
    const next = theme === 'dark' ? 'light' : 'dark'
    document.documentElement.dataset.theme = next
    saveString('theme', next)
    setTheme(next)
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}
