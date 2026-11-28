import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { RiskMeter } from '../components/ui/RiskMeter'
import { DeadlineBar, StatusTag } from '../components/ui/StatusTag'
import { ORGANISATIONS } from '../data/organisations'
import { cn } from '../utils/cn'

const STEPS = ['dossier', 'risk', 'request'] as const

type Step = (typeof STEPS)[number]

function daysAgo(n: number): string {
  const date = new Date()
  date.setDate(date.getDate() - n)
  return date.toISOString()
}

export function OnboardingPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const titleRef = useRef<HTMLHeadingElement>(null)
  const [index, setIndex] = useState(0)

  const step = STEPS[index]
  const last = index === STEPS.length - 1

  useEffect(() => {
    titleRef.current?.focus()
  }, [index])

  function finish() {
    navigate('/')
  }

  return (
    <div className="mt-8">
      <div className="flex items-center justify-between font-mono text-xs text-muted">
        <span>{t('onboarding.progress', { current: index + 1, total: STEPS.length })}</span>
        <button type="button" onClick={finish} className="rounded-box hover:text-fg">
          {t('onboarding.skip')}
        </button>
      </div>

      <div className="mt-2 flex gap-1" aria-hidden="true">
        {STEPS.map((item, position) => (
          <div key={item} className={cn('h-1 flex-1', position <= index ? 'bg-accent' : 'bg-border')} />
        ))}
      </div>

      <h1 ref={titleRef} tabIndex={-1} className="mt-8 font-mono text-2xl outline-none">
        {t(`onboarding.steps.${step}.title`)}
      </h1>
      <p className="mt-3 leading-relaxed text-muted">
        {t(`onboarding.steps.${step}.body`, { start: t('home.start') })}
      </p>

      <div className="mt-8 rounded-box border border-border bg-surface p-4">
        <Example step={step} />
      </div>

      <div className="mt-10 flex items-center justify-between">
        <Button variant="ghost" onClick={() => setIndex(index - 1)} disabled={index === 0}>
          ← {t('onboarding.back')}
        </Button>
        <Button onClick={() => (last ? finish() : setIndex(index + 1))}>
          {last ? t('onboarding.finish') : `${t('onboarding.next')} →`}
        </Button>
      </div>
    </div>
  )
}

function Example({ step }: { step: Step }) {
  const { t } = useTranslation()

  if (step === 'dossier') {
    return (
      <ul>
        {[ORGANISATIONS[0], ORGANISATIONS[1], ORGANISATIONS[4]].map((org) => (
          <li key={org.id} className="flex items-center justify-between gap-4 border-b border-border py-2 text-sm last:border-b-0">
            <span className="font-medium">{org.site}</span>
            <span className="flex-1 text-muted">{t(`types.${org.type}`)}</span>
            <StatusTag state={org.state} />
          </li>
        ))}
      </ul>
    )
  }

  if (step === 'risk') {
    return (
      <div className="flex flex-col gap-4">
        <RiskMeter value={85} />
        <RiskMeter value={55} />
        <RiskMeter value={20} />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <p className="font-mono text-xs text-muted">{t('onboarding.example.deadline')}</p>
      <DeadlineBar sentAt={daysAgo(12)} />
    </div>
  )
}
