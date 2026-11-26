import { useEffect, useState, type KeyboardEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { api, ApiError } from '../utils/api'

type Notification = {
  id: string
  title: string
  message: string
  created_at: string
}

type View =
  | { status: 'loading' | 'error' | 'signed-out' }
  | { status: 'ready'; notifications: Notification[]; unreadCount: number; hasNextPage: boolean }

const NOTIFICATIONS = '/api/v1/notifications'
const PAGE_SIZE = 10
const TABS = ['unread', 'read'] as const
type NotificationTab = (typeof TABS)[number]

function isUnauthorized(error: unknown) {
  return error instanceof ApiError && error.status === 401
}

export function NotificationsPage() {
  const { t, i18n } = useTranslation()
  const locale = i18n.resolvedLanguage ?? i18n.language
  const [page, setPage] = useState<{ tab: NotificationTab; offset: number }>({ tab: 'unread', offset: 0 })
  const [view, setView] = useState<View>({ status: 'loading' })
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(false)
  const { tab, offset } = page
  const isUnreadTab = tab === 'unread'
  const unreadPageIds = view.status === 'ready' && isUnreadTab
    ? view.notifications.map(({ id }) => id)
    : []
  const allSelected = unreadPageIds.length > 0 && selectedIds.length === unreadPageIds.length

  useEffect(() => {
    let current = true
    const query = new URLSearchParams({
      limit: String(PAGE_SIZE + 1),
      offset: String(page.offset),
      read_status: page.tab,
    })

    async function load() {
      try {
        const [notifications, { unread_count }] = await Promise.all([
          api.get<Notification[]>(`${NOTIFICATIONS}?${query}`),
          api.get<{ unread_count: number }>(`${NOTIFICATIONS}/unread-count`),
        ])
        if (!current) return

        if (page.offset > 0 && notifications.length === 0) {
          setPage({ tab: page.tab, offset: Math.max(0, page.offset - PAGE_SIZE) })
          return
        }
        setView({
          status: 'ready',
          notifications: notifications.slice(0, PAGE_SIZE),
          unreadCount: unread_count,
          hasNextPage: notifications.length > PAGE_SIZE,
        })
      } catch (error) {
        if (current) setView({ status: isUnauthorized(error) ? 'signed-out' : 'error' })
      }
    }

    void load()
    return () => { current = false }
  }, [page])

  function loadPage(nextOffset: number, nextTab = tab) {
    setView({ status: 'loading' })
    setSelectedIds([])
    setSaveError(false)
    setPage({ tab: nextTab, offset: nextOffset })
  }

  function handleTabKeys(event: KeyboardEvent<HTMLDivElement>) {
    if (saving || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return

    event.preventDefault()
    const otherTab = tab === 'unread' ? 'read' : 'unread'
    const nextTab = event.key === 'Home' ? 'unread' : event.key === 'End' ? 'read' : otherTab
    event.currentTarget.querySelector<HTMLButtonElement>(`#notifications-tab-${nextTab}`)?.focus()
    if (nextTab !== tab) loadPage(0, nextTab)
  }

  function toggleSelection(id: string, checked: boolean) {
    setSelectedIds((ids) => checked ? [...ids, id] : ids.filter((selectedId) => selectedId !== id))
  }

  async function markRead(id?: string) {
    setSaving(true)
    setSaveError(false)
    try {
      if (id) {
        await api.patch<Notification>(`${NOTIFICATIONS}/${id}/read`)
      } else {
        await api.patch<string[]>(`${NOTIFICATIONS}/read`, { notification_ids: selectedIds })
      }
      loadPage(offset)
    } catch (error) {
      if (isUnauthorized(error)) setView({ status: 'signed-out' })
      else setSaveError(true)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="font-mono text-3xl">{t('nav.notifications')}</h1>
        {view.status === 'ready' && (
          <p role="status" className="font-mono text-sm text-muted">
            {t('notifications.unreadCount', { count: view.unreadCount })}
          </p>
        )}
      </div>

      <div role="tablist" aria-label={t('nav.notifications')} className="mt-6 flex gap-4 border-b border-border" onKeyDown={handleTabKeys}>
        {TABS.map((id) => (
          <button
            key={id}
            id={`notifications-tab-${id}`}
            type="button"
            role="tab"
            aria-selected={tab === id}
            aria-controls="notifications-panel"
            tabIndex={tab === id ? 0 : -1}
            disabled={saving}
            className={tab === id
              ? 'border-b-2 border-accent px-2 pb-2 text-sm font-medium text-fg'
              : 'border-b-2 border-transparent px-2 pb-2 text-sm text-muted hover:text-fg'}
            onClick={() => { if (id !== tab) loadPage(0, id) }}
          >
            {t(`notifications.tabs.${id}`)}
          </button>
        ))}
      </div>

      <section id="notifications-panel" role="tabpanel" aria-labelledby={`notifications-tab-${tab}`} tabIndex={0}>
        {view.status === 'loading' && (
          <Card className="mt-6 p-4">
            <p role="status" className="text-sm text-muted">{t('notifications.loading')}</p>
          </Card>
        )}
        {view.status === 'signed-out' && (
          <Card className="mt-6 space-y-3 p-4">
            <p role="alert" className="text-sm">{t('notifications.signedOut')}</p>
            <Link to="/login" className="text-sm font-medium text-accent underline">{t('auth.login.submit')}</Link>
          </Card>
        )}
        {view.status === 'error' && (
          <Card className="mt-6 space-y-3 p-4">
            <p role="alert" className="text-sm">{t('notifications.loadError')}</p>
            <Button variant="secondary" size="sm" onClick={() => loadPage(offset)}>{t('notifications.retry')}</Button>
          </Card>
        )}
        {view.status === 'ready' && view.notifications.length === 0 && (
          <Card className="mt-6 p-4">
            <p className="text-sm text-muted">{t(`notifications.empty.${tab}`)}</p>
          </Card>
        )}
        {view.status === 'ready' && view.notifications.length > 0 && (
          <>
            {isUnreadTab && (
              <div className="mt-6 flex flex-wrap items-center justify-between gap-2">
                <span className="text-sm text-muted">{t('notifications.selectedCount', { count: selectedIds.length })}</span>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={saving || unreadPageIds.length === 0}
                    aria-label={t(allSelected ? 'notifications.clearSelection' : 'notifications.selectAllLabel')}
                    onClick={() => setSelectedIds(allSelected ? [] : unreadPageIds)}
                  >
                    {t(allSelected ? 'notifications.clearSelection' : 'notifications.selectAll')}
                  </Button>
                  <Button size="sm" disabled={saving || selectedIds.length === 0} onClick={() => void markRead()}>
                    {t('notifications.markSelected')}
                  </Button>
                </div>
              </div>
            )}
            {saving && <p role="status" className="mt-3 text-sm text-muted">{t('notifications.saving')}</p>}
            {saveError && <p role="alert" className="mt-3 text-sm text-accent">{t('notifications.saveError')}</p>}
            <Card className={isUnreadTab ? 'mt-3' : 'mt-6'}>
              <ul className="divide-y divide-border">
                {view.notifications.map((notification) => (
                  <li key={notification.id} className="flex flex-wrap items-start gap-3 p-4 sm:flex-nowrap">
                    {isUnreadTab && (
                      <input
                        type="checkbox"
                        aria-label={t('notifications.selectLabel', { title: notification.title })}
                        className="mt-1 accent-accent"
                        checked={selectedIds.includes(notification.id)}
                        disabled={saving}
                        onChange={(event) => toggleSelection(notification.id, event.target.checked)}
                      />
                    )}
                    <div className="min-w-0 flex-1 break-words">
                      <h2 className="font-medium">{notification.title}</h2>
                      <p className="mt-1 text-sm">{notification.message}</p>
                      <time dateTime={notification.created_at} className="mt-2 block text-xs text-muted">
                        {new Date(notification.created_at).toLocaleString(locale)}
                      </time>
                    </div>
                    {isUnreadTab && (
                      <Button
                        variant="secondary"
                        size="sm"
                        aria-label={t('notifications.markReadLabel', { title: notification.title })}
                        disabled={saving}
                        onClick={() => void markRead(notification.id)}
                      >
                        {t('notifications.markRead')}
                      </Button>
                    )}
                  </li>
                ))}
              </ul>
            </Card>
            {(offset > 0 || view.hasNextPage) && (
              <nav aria-label={t('notifications.pagination.label')} className="mt-4 flex justify-end gap-2">
                <Button variant="secondary" size="sm" disabled={saving || offset === 0} onClick={() => loadPage(offset - PAGE_SIZE)}>
                  {t('notifications.pagination.previous')}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={saving || !view.hasNextPage}
                  onClick={() => loadPage(offset + PAGE_SIZE)}
                >
                  {t('notifications.pagination.next')}
                </Button>
              </nav>
            )}
          </>
        )}
      </section>
    </>
  )
}
