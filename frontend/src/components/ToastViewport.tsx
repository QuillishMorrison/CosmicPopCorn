import { useEffect } from 'react'
import { useToastStore } from '../store/toastStore'

export function ToastViewport() {
  const { items, remove } = useToastStore()

  useEffect(() => {
    if (!items.length) return
    const timers = items.map((item) =>
      window.setTimeout(() => {
        remove(item.id)
      }, 1800)
    )
    return () => {
      timers.forEach((timer) => window.clearTimeout(timer))
    }
  }, [items, remove])

  return (
    <div className="pointer-events-none fixed right-4 top-20 z-50 flex w-[min(360px,calc(100vw-2rem))] flex-col gap-2">
      {items.map((item) => (
        <div
          key={item.id}
          className={`pointer-events-auto rounded-xl border px-4 py-3 text-sm shadow-panel backdrop-blur ${
            item.tone === 'error'
              ? 'border-danger/45 bg-danger/10 text-red-100'
              : item.tone === 'success'
                ? 'border-accent/30 bg-accent/8 text-textMain'
                : 'border-borderSoft bg-panel/85 text-textMain'
          }`}
        >
          <div className="flex items-start gap-3">
            <div className="min-w-0 flex-1">
              <div>{item.title}</div>
              {item.count > 1 ? <div className="mt-1 text-[11px] text-textMute">Повторений: {item.count}</div> : null}
            </div>
            <button
              type="button"
              className="shrink-0 rounded-full border border-borderSoft px-2 py-1 text-xs text-textMute transition hover:text-textMain"
              onClick={() => remove(item.id)}
              aria-label="Закрыть уведомление"
              title="Закрыть"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
