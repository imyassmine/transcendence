import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, Outlet } from 'react-router-dom'

import { ApiError } from '../../utils/api'
import { me } from '../../utils/auth'
import { Button } from '../ui/Button'

type View = { status: 'loading' | 'signed-out' | 'error' | 'ready' }

export function RequireAuth() {
  const { t } = useTranslation()
  const [view, setView] = useState<View>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let current = true

    me()
      .then(() => {
        if (current) setView({ status: 'ready' })
      })
      .catch((error: unknown) => {
        if (!current) return
        const signedOut = error instanceof ApiError && error.status === 401
        setView({ status: signedOut ? 'signed-out' : 'error' })
      })

    return () => {
      current = false
    }
  }, [attempt])

  function retry() {
    setView({ status: 'loading' })
    setAttempt((value) => value + 1)
  }

  if (view.status === 'ready') return <Outlet />
  if (view.status === 'signed-out') return <Navigate to="/welcome" replace />

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 px-4 text-center">
      {view.status === 'loading' ? (
        <p className="font-mono text-xs tracking-widest text-muted uppercase">{t('auth.session.checking')}</p>
      ) : (
        <>
          <p role="alert" className="text-sm text-accent">{t('auth.session.error')}</p>
          <Button variant="secondary" onClick={retry}>{t('auth.session.retry')}</Button>
        </>
      )}
    </div>
  )
}
