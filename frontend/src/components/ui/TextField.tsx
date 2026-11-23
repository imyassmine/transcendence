import { useId, type InputHTMLAttributes } from 'react'

import { cn } from '../../lib/cn'

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  error?: string
}

export function TextField({ label, error, className, ...rest }: TextFieldProps) {
  const id = useId()
  const errorId = `${id}-error`

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="font-mono text-xs tracking-wide text-muted uppercase">
        {label}
      </label>

      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          'h-10 rounded-box border bg-surface px-3 text-sm outline-none',
          'focus:border-fg',
          error ? 'border-accent' : 'border-border',
          className,
        )}
        {...rest}
      />

      {error && (
        <p id={errorId} className="text-xs text-accent">
          {error}
        </p>
      )}
    </div>
  )
}
