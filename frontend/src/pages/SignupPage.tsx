import { useState, type FormEvent } from 'react'
import { Trans, useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { TextField } from '../components/ui/TextField'
import { authErrorKey, register } from '../utils/auth'
import { cn } from '../utils/cn'
import { PASSWORD_RULES, isStrongPassword, isValidEmail } from '../utils/validation'

type SignupErrors = {
  name?: string
  email?: string
  password?: string
}

export function SignupPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<SignupErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function validate(): SignupErrors {
    const found: SignupErrors = {}

    if (!name.trim()) found.name = t('auth.errors.required')
    else if (name.trim().length > 50) found.name = t('auth.errors.tooLong')

    if (!email.trim()) found.email = t('auth.errors.required')
    else if (!isValidEmail(email)) found.email = t('auth.errors.email')

    if (!password) found.password = t('auth.errors.required')
    else if (!isStrongPassword(password)) found.password = t('auth.errors.password')

    return found
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()

    const found = validate()
    setErrors(found)
    setFormError(null)
    if (Object.keys(found).length > 0) return

    setSubmitting(true)
    try {
      await register(name.trim(), email.trim(), password)
      navigate('/')
    } catch (error) {
      setFormError(authErrorKey(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <h1 className="mt-6 font-mono text-2xl">{t('auth.signup.title')}</h1>
      <p className="mt-1 text-sm text-muted">{t('auth.signup.subtitle')}</p>

      <form onSubmit={handleSubmit} noValidate className="mt-8 flex flex-col gap-5">
        <TextField
          label={t('auth.fields.name')}
          autoComplete="name"
          maxLength={50}
          value={name}
          onChange={(event) => setName(event.target.value)}
          error={errors.name}
        />

        <TextField
          label={t('auth.fields.email')}
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          error={errors.email}
        />

        <TextField
          label={t('auth.fields.password')}
          type="password"
          autoComplete="new-password"
          maxLength={128}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={errors.password}
        />

        <PasswordRules password={password} />

        {formError && (
          <p role="alert" className="text-sm text-accent">{t(formError)}</p>
        )}

        <Button type="submit" className="mt-2 w-full" disabled={submitting}>
          {submitting ? t('auth.signup.submitting') : t('auth.signup.submit')}
        </Button>

        <p className="text-xs text-muted">
          <Trans
            i18nKey="auth.signup.accept"
            components={{
              terms: <Link to="/terms" className="text-fg underline underline-offset-4 hover:text-accent" />,
              privacy: <Link to="/privacy" className="text-fg underline underline-offset-4 hover:text-accent" />,
            }}
          />
        </p>
      </form>

      <p className="mt-6 text-center text-xs text-muted">
        {t('auth.signup.hasAccount')}{' '}
        <Link to="/login" className="text-fg underline underline-offset-4 hover:text-accent">
          {t('auth.signup.loginLink')}
        </Link>
      </p>
    </>
  )
}

function PasswordRules({ password }: { password: string }) {
  const { t } = useTranslation()

  return (
    <div className="border-l-2 border-border pl-3">
      <p className="mb-2 font-mono text-xs tracking-wide text-muted uppercase">{t('auth.rules.title')}</p>

      <ul className="grid grid-cols-1 gap-1 sm:grid-cols-2">
        {PASSWORD_RULES.map((rule) => {
          const ok = rule.test(password)

          return (
            <li key={rule.key} className={cn('flex items-center gap-2 text-xs', ok ? 'text-success' : 'text-muted')}>
              <span aria-hidden="true" className="font-mono">{ok ? '✓' : '·'}</span>
              {t(`auth.rules.${rule.key}`)}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
