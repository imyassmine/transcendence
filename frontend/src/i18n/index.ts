import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import { loadString, saveString } from '../utils/storage'

import en from './locales/en.json'
import es from './locales/es.json'
import fr from './locales/fr.json'

export const LANGUAGES = [
  { code: 'en', label: 'EN' },
  { code: 'fr', label: 'FR' },
  { code: 'es', label: 'ES' },
] as const

const SUPPORTED: string[] = LANGUAGES.map((lang) => lang.code)

function detectLanguage(): string {
  const saved = loadString('lang')
  if (saved && SUPPORTED.includes(saved)) return saved

  const browser = navigator.language.slice(0, 2)
  return SUPPORTED.includes(browser) ? browser : 'en'
}

void i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    fr: { translation: fr },
    es: { translation: es },
  },
  lng: detectLanguage(),
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

function onLanguageChange(lang: string) {
  document.documentElement.lang = lang
  saveString('lang', lang)
}

onLanguageChange(i18n.language)
i18n.on('languageChanged', onLanguageChange)

export default i18n
