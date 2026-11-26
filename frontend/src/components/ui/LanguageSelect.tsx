import { useTranslation } from 'react-i18next'

import { LANGUAGES } from '../../i18n'

export function LanguageSelect() {
  const { t, i18n } = useTranslation()

  return (
    <label className="flex items-center">
      <span className="sr-only">{t('language.label')}</span>

      <select
        value={i18n.resolvedLanguage}
        onChange={(event) => void i18n.changeLanguage(event.target.value)}
        className="cursor-pointer rounded-box bg-transparent font-mono text-xs text-muted hover:text-fg"
      >
        {LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code} className="bg-surface text-fg">
            {lang.label}
          </option>
        ))}
      </select>
    </label>
  )
}
