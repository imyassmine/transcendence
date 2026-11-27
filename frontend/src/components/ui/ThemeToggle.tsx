import { useTranslation } from 'react-i18next'

import { useTheme } from '../../theme/ThemeContext'

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const { t } = useTranslation()

  const label = theme === 'dark' ? t('theme.toLight') : t('theme.toDark')

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={label}
      title={label}
      className="rounded-box font-mono text-xs text-muted hover:text-fg"
    >
      {theme === 'dark' ? t('theme.light') : t('theme.dark')}
    </button>
  )
}
