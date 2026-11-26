import type { ReactNode } from 'react'

type PageHeaderProps = {
  title: string
  subtitle?: string
  children?: ReactNode
}

export function PageHeader({ title, subtitle, children }: PageHeaderProps) {
  return (
    <header>
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h1 className="font-mono text-3xl leading-tight">{title}</h1>
        {children}
      </div>
      {subtitle && <p className="mt-3 text-muted">{subtitle}</p>}
    </header>
  )
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h2 className="border-b border-fg pb-2 font-mono text-xs tracking-widest uppercase">
      {children}
    </h2>
  )
}
