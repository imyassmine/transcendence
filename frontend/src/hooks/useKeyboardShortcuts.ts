import { useEffect } from 'react'

type ShortcutMap = Record<string, () => void>

function isTyping(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false

  const tag = target.tagName
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable
}

export function useKeyboardShortcuts(shortcuts: ShortcutMap) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.ctrlKey || event.metaKey || event.altKey) return
      if (isTyping(event.target)) return

      const action = shortcuts[event.key.toLowerCase()]
      if (action) {
        event.preventDefault()
        action()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [shortcuts])
}
