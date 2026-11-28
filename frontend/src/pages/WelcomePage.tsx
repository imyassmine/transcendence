import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'

import { SectionTitle } from '../components/ui/PageHeader'
import { me } from '../utils/auth'
import { cn } from '../utils/cn'

const STEPS = ['find', 'score', 'request', 'track'] as const

export function WelcomePage() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  useEffect(() => {
    let current = true

    me()
      .then(() => {
        if (current) navigate('/', { replace: true })
      })
      .catch(() => {})

    return () => {
      current = false
    }
  }, [navigate])

  const promises = t('welcome.promises.items', { returnObjects: true }) as string[]

  return (
    <div className="mt-10">
      <p className="font-mono text-xs tracking-widest text-accent uppercase">{t('welcome.kicker')}</p>
      <h1 className="mt-4 font-mono text-3xl leading-tight sm:text-4xl">{t('welcome.title')}</h1>
      <p className="mt-4 max-w-xl leading-relaxed text-muted">{t('welcome.subtitle')}</p>

      <CallToAction className="mt-8" />

      <section className="mt-16">
        <SectionTitle>{t('welcome.how')}</SectionTitle>

        <ol>
          {STEPS.map((step, index) => (
            <li key={step} className="grid grid-cols-[2.5rem_1fr] gap-x-4 border-b border-border py-4">
              <span className="font-mono text-xs text-accent tabular-nums">
                {String(index + 1).padStart(2, '0')}
              </span>
              <div>
                <h3 className="font-mono text-sm">{t(`welcome.steps.${step}.title`)}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted">{t(`welcome.steps.${step}.body`)}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="mt-12 border-l-2 border-accent pl-4">
        <h2 className="font-mono text-xs tracking-widest text-muted uppercase">{t('welcome.law.label')}</h2>
        <p className="mt-2 leading-relaxed">{t('welcome.law.text')}</p>
      </section>

      <section className="mt-12">
        <SectionTitle>{t('welcome.promises.title')}</SectionTitle>

        <ul className="mt-4 flex flex-col gap-2 text-sm">
          {promises.map((promise) => (
            <li key={promise} className="flex gap-3">
              <span aria-hidden="true" className="font-mono text-success">✓</span>
              {promise}
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-16 border-t border-fg pt-8">
        <h2 className="font-mono text-xl">{t('welcome.final')}</h2>
        <CallToAction className="mt-6" />
      </section>
    </div>
  )
}

function CallToAction({ className }: { className?: string }) {
  const { t } = useTranslation()

  return (
    <div className={cn('flex flex-wrap gap-3', className)}>
      <Link
        to="/signup"
        className="inline-flex h-10 items-center rounded-box bg-accent px-4 text-sm font-medium text-accent-fg hover:opacity-90"
      >
        {t('welcome.signup')}
      </Link>
      <Link
        to="/login"
        className="inline-flex h-10 items-center rounded-box border border-fg px-4 text-sm font-medium hover:bg-fg hover:text-bg"
      >
        {t('auth.login.submit')}
      </Link>
    </div>
  )
}
