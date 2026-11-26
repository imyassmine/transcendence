import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { TextField } from '../components/ui/TextField'
import { authErrorKey, login } from '../utils/auth'
import { isValidEmail } from '../utils/validation'

type LoginErrors = {
  email?: string
  password?: string
}

export function LoginPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<LoginErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function validate(): LoginErrors {
    const found: LoginErrors = {}

    if (!email.trim()) found.email = t('auth.errors.required')
    else if (!isValidEmail(email)) found.email = t('auth.errors.email')

    if (!password) found.password = t('auth.errors.required')

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
      await login(email.trim(), password)
      navigate('/')
    } catch (error) {
      setFormError(authErrorKey(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <h1 className="mt-6 font-mono text-2xl">{t('auth.login.title')}</h1>
      <p className="mt-1 text-sm text-muted">{t('app.tagline')}</p>

      <form onSubmit={handleSubmit} noValidate className="mt-8 flex flex-col gap-5">
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
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={errors.password}
        />

        {formError && (
          <p role="alert" className="text-sm text-accent">{t(formError)}</p>
        )}

        <Button type="submit" className="mt-2 w-full" disabled={submitting}>
          {submitting ? t('auth.login.submitting') : t('auth.login.submit')}
        </Button>
      </form>

      <p className="mt-6 text-center text-xs text-muted">
        {t('auth.login.noAccount')}{' '}
        <Link to="/signup" className="text-fg underline underline-offset-4 hover:text-accent">
          {t('auth.login.signupLink')}
        </Link>
      </p>
    </>
  )
}
