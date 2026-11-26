import { useState, type FormEvent, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { LanguageSelect } from '../components/ui/LanguageSelect'
import { PageHeader, SectionTitle } from '../components/ui/PageHeader'
import { TextField } from '../components/ui/TextField'
import { ThemeToggle } from '../components/ui/ThemeToggle'
import { ORGANISATIONS } from '../data/organisations'
import { MOCK_USER } from '../data/user'
import { isValidEmail } from '../utils/validation'

type AccountErrors = {
  name?: string
  email?: string
}

function downloadJson(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function ProfilePage() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const [name, setName] = useState(MOCK_USER.name)
  const [email, setEmail] = useState(MOCK_USER.email)
  const [errors, setErrors] = useState<AccountErrors>({})
  const [saved, setSaved] = useState(false)
  const [confirmText, setConfirmText] = useState('')

  const confirmWord = t('profile.danger.word')

  function handleSave(event: FormEvent) {
    event.preventDefault()

    const found: AccountErrors = {}
    if (!name.trim()) found.name = t('auth.errors.required')
    else if (name.trim().length > 50) found.name = t('auth.errors.tooLong')
    if (!email.trim()) found.email = t('auth.errors.required')
    else if (!isValidEmail(email)) found.email = t('auth.errors.email')

    setErrors(found)
    setSaved(Object.keys(found).length === 0)
  }

  function exportData() {
    downloadJson('transcendence-data.json', {
      exported_at: new Date().toISOString(),
      user: { name, email },
      organisations: ORGANISATIONS,
    })
  }

  return (
    <>
      <PageHeader title={t('profile.title')} subtitle={t('profile.subtitle')} />
      <p className="mt-1 font-mono text-xs text-warning">{t('profile.demo')}</p>

      <section className="mt-10">
        <SectionTitle>{t('profile.account.title')}</SectionTitle>
        <form onSubmit={handleSave} noValidate className="mt-4 flex flex-col gap-5">
          <TextField
            label={t('auth.fields.name')}
            autoComplete="name"
            maxLength={50}
            value={name}
            onChange={(event) => { setName(event.target.value); setSaved(false) }}
            error={errors.name}
          />
          <TextField
            label={t('auth.fields.email')}
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => { setEmail(event.target.value); setSaved(false) }}
            error={errors.email}
          />
          <div className="flex items-center gap-3">
            <Button type="submit">{t('profile.account.save')}</Button>
            {saved && <span role="status" className="font-mono text-xs text-success">{t('profile.account.saved')}</span>}
          </div>
        </form>
      </section>

      <section className="mt-10">
        <SectionTitle>{t('profile.preferences.title')}</SectionTitle>
        <Row label={t('profile.preferences.language')}><LanguageSelect /></Row>
        <Row label={t('profile.preferences.theme')}><ThemeToggle /></Row>
      </section>

      <section className="mt-10">
        <SectionTitle>{t('profile.security.title')}</SectionTitle>
        <Row label={t('profile.security.twoFactor')}>
          <span className="font-mono text-xs text-muted">{t('profile.security.soon')}</span>
        </Row>
      </section>

      <section className="mt-10">
        <SectionTitle>{t('profile.data.title')}</SectionTitle>
        <p className="mt-4 text-sm text-muted">{t('profile.data.text')}</p>
        <Button variant="secondary" className="mt-4" onClick={exportData}>
          {t('profile.data.export')}
        </Button>
      </section>

      <section className="mt-10 rounded-box border border-accent p-4">
        <h2 className="font-mono text-xs tracking-widest text-accent uppercase">{t('profile.danger.title')}</h2>
        <p className="mt-2 text-sm text-muted">{t('profile.danger.text')}</p>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <TextField
              label={t('profile.danger.confirmLabel', { word: confirmWord })}
              value={confirmText}
              onChange={(event) => setConfirmText(event.target.value)}
              autoComplete="off"
            />
          </div>
          <Button disabled={confirmText !== confirmWord} onClick={() => navigate('/login')}>
            {t('profile.danger.delete')}
          </Button>
        </div>
      </section>
    </>
  )
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-border py-3 text-sm">
      <span>{label}</span>
      {children}
    </div>
  )
}
