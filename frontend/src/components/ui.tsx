import { ReactNode } from 'react'
import clsx from 'clsx'

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <section
      className={clsx(
        'overflow-hidden rounded-xl2 border border-borderSoft bg-panel p-4 shadow-panel',
        className
      )}
    >
      {children}
    </section>
  )
}

export function SectionTitle({ title, subtitle }: { title: ReactNode; subtitle?: ReactNode }) {
  return (
    <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h2 className="text-base font-semibold leading-tight text-textMain text-balance">{title}</h2>
        {subtitle ? <p className="text-xs leading-relaxed text-textMute text-pretty">{subtitle}</p> : null}
      </div>
    </div>
  )
}

export function Button({
  children,
  className,
  variant = 'primary',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'ghost' | 'danger' }) {
  const styles = {
    primary: 'bg-accent text-slate-950',
    ghost: 'border border-borderSoft bg-panelSoft text-textMain',
    danger: 'bg-danger text-slate-950'
  }[variant]
  return (
    <button
      className={clsx(
        'min-h-11 break-words whitespace-normal rounded-xl px-4 py-2 text-center text-sm font-semibold leading-tight transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60',
        styles,
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-2xl border border-borderSoft bg-panelSoft px-3 py-2">
      <div className="truncate text-[10px] uppercase tracking-[0.2em] text-textMute">{label}</div>
      <div className="break-words text-sm font-semibold text-textMain">{value}</div>
    </div>
  )
}

export function Progress({ value }: { value: number }) {
  return (
    <div className="h-2 rounded-full bg-slate-900">
      <div
        className="h-2 rounded-full bg-accent transition-all"
        style={{ width: `${Math.max(3, Math.min(100, value))}%` }}
      />
    </div>
  )
}

export function Sparkline({ values }: { values: number[] }) {
  if (!values.length) return <div className="h-8 rounded bg-panelSoft" />
  const max = Math.max(...values)
  const min = Math.min(...values)
  const points = values.map((value, index) => {
    const x = (index / Math.max(1, values.length - 1)) * 100
    const y = 28 - ((value - min) / Math.max(1, max - min)) * 24
    return `${x},${y}`
  })
  return (
    <svg viewBox="0 0 100 32" className="h-8 w-full">
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        points={points.join(' ')}
        className="text-accent"
      />
    </svg>
  )
}

export function Tooltip({
  label,
  children
}: {
  label: string
  children: ReactNode
}) {
  return (
    <span className="inline-flex max-w-full cursor-pointer items-center" title={label} tabIndex={0}>
      {children}
      <span className="ml-1 inline-flex h-4 w-4 shrink-0 cursor-pointer items-center justify-center rounded-full border border-borderSoft text-[10px] text-textMute">
        ?
      </span>
    </span>
  )
}
