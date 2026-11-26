import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '../components/ui/Button'
import { TextField } from '../components/ui/TextField'

type ApiKey = {
  id: string
  name: string
  prefix: string
  createdAt: string
  lastUsedAt: string | null
}

const MOCK_KEYS: ApiKey[] = [
  { id: '1', name: 'raspberry-pi', prefix: 'tr_4f9a', createdAt: '2026-11-20', lastUsedAt: '2026-11-25' },
  { id: '2', name: 'export-script', prefix: 'tr_b71c', createdAt: '2026-11-24', lastUsedAt: null },
]

function generateKey(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(24))
  return 'tr_' + Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
}

export function ApiKeysPage() {
  const { t, i18n } = useTranslation()

  const [keys, setKeys] = useState<ApiKey[]>(MOCK_KEYS)
  const [name, setName] = useState('')
  const [nameError, setNameError] = useState<string | undefined>()
  const [newKey, setNewKey] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [confirmingId, setConfirmingId] = useState<string | null>(null)

  function formatDate(date: string) {
    return new Date(date).toLocaleDateString(i18n.language)
  }

  function handleCreate(event: FormEvent) {
    event.preventDefault()

    const cleanName = name.trim()
    if (!cleanName) {
      setNameError(t('auth.errors.required'))
      return
    }
    if (cleanName.length > 50) {
      setNameError(t('auth.errors.tooLong'))
      return
    }

    const secret = generateKey()
    const created: ApiKey = {
      id: crypto.randomUUID(),
      name: cleanName,
      prefix: secret.slice(0, 7),
      createdAt: new Date().toISOString(),
      lastUsedAt: null,
    }

    setKeys((current) => [created, ...current])
    setNewKey(secret)
    setCopied(false)
    setName('')
    setNameError(undefined)
  }

  async function copyKey() {
    if (!newKey) return
    try {
      await navigator.clipboard.writeText(newKey)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  function revoke(id: string) {
    setKeys((current) => current.filter((key) => key.id !== id))
    setConfirmingId(null)
  }

  return (
    <>
      <h1 className="font-mono text-3xl">{t('apiKeys.title')}</h1>
      <p className="mt-3 text-muted">{t('apiKeys.subtitle')}</p>
      <p className="mt-1 font-mono text-xs text-warning">{t('apiKeys.demo')}</p>

      {newKey && (
        <div className="mt-8 rounded-box border border-accent bg-surface p-4" role="status">
          <p className="font-mono text-xs tracking-wide text-accent uppercase">{t('apiKeys.newKey.title')}</p>
          <p className="mt-1 text-sm">{t('apiKeys.newKey.warning')}</p>

          <code className="mt-3 block rounded-box border border-border bg-bg px-3 py-2 font-mono text-sm break-all select-all">
            {newKey}
          </code>

          <div className="mt-3 flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => void copyKey()}>
              {copied ? t('apiKeys.newKey.copied') : t('apiKeys.newKey.copy')}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setNewKey(null)}>
              {t('apiKeys.newKey.done')}
            </Button>
          </div>
        </div>
      )}

      <section className="mt-10">
        <h2 className="border-b border-fg pb-2 font-mono text-xs tracking-widest uppercase">
          {t('apiKeys.create.title')}
        </h2>

        <form onSubmit={handleCreate} noValidate className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-start">
          <div className="flex-1">
            <TextField
              label={t('apiKeys.create.nameLabel')}
              placeholder={t('apiKeys.create.namePlaceholder')}
              maxLength={50}
              value={name}
              onChange={(event) => setName(event.target.value)}
              error={nameError}
            />
          </div>
          <Button type="submit" className="sm:mt-[1.375rem]">
            {t('apiKeys.create.submit')}
          </Button>
        </form>
      </section>

      <section className="mt-10">
        <h2 className="border-b border-fg pb-2 font-mono text-xs tracking-widest uppercase">
          {t('apiKeys.list.title')}
        </h2>

        {keys.length === 0 ? (
          <p className="mt-4 text-sm text-muted">{t('apiKeys.list.empty')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left font-mono text-xs text-muted uppercase">
                  <th className="py-2 font-normal">{t('apiKeys.list.name')}</th>
                  <th className="py-2 font-normal">{t('apiKeys.list.key')}</th>
                  <th className="py-2 font-normal">{t('apiKeys.list.created')}</th>
                  <th className="py-2 font-normal">{t('apiKeys.list.lastUsed')}</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {keys.map((key) => (
                  <tr key={key.id} className="border-b border-border">
                    <td className="py-3 pr-3 font-medium">{key.name}</td>
                    <td className="py-3 pr-3 font-mono text-muted">{key.prefix}…</td>
                    <td className="py-3 pr-3 font-mono text-xs tabular-nums">{formatDate(key.createdAt)}</td>
                    <td className="py-3 pr-3 font-mono text-xs tabular-nums text-muted">
                      {key.lastUsedAt ? formatDate(key.lastUsedAt) : t('apiKeys.list.never')}
                    </td>
                    <td className="py-3 text-right whitespace-nowrap">
                      {confirmingId === key.id ? (
                        <span className="inline-flex gap-1">
                          <Button size="sm" onClick={() => revoke(key.id)}>
                            {t('apiKeys.list.confirm')}
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => setConfirmingId(null)}>
                            {t('apiKeys.list.cancel')}
                          </Button>
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          variant="secondary"
                          aria-label={t('apiKeys.list.revokeLabel', { name: key.name })}
                          onClick={() => setConfirmingId(key.id)}
                        >
                          {t('apiKeys.list.revoke')}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}
