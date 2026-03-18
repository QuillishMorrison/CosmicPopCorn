import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { ToastViewport } from './ToastViewport'
import { ChatWidget } from './ChatWidget'
import { useAuthStore } from '../store/authStore'
import { useStation } from '../hooks/useGameData'
import { describeResource, labelForResource } from '../lib/i18n'
import { useActionPreviewStore } from '../store/actionPreviewStore'
import { useLiveDataStore } from '../store/liveDataStore'

type FloatingDelta = {
  id: string
  resource: string
  amount: number
}

const links = [
  { to: '/', label: 'Хаб' },
  { to: '/guide', label: 'Гид' },
  { to: '/market', label: 'Рынок' },
  { to: '/contracts', label: 'Контракты' },
  { to: '/meta', label: 'Мета' },
  { to: '/sector', label: 'Сектор' },
  { to: '/settings', label: 'Аккаунт' }
]

const t = {
  panel: 'Панель автономного сектора',
  inventory: 'Склад станции',
  logout: 'Выйти'
}

function formatAmount(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function formatDelta(value: number) {
  const abs = Math.abs(value)
  const text = Number.isInteger(abs) ? String(abs) : abs.toFixed(1)
  return `${value > 0 ? '+' : '-'}${text}`
}

export function Layout() {
  const location = useLocation()
  const isDashboardRoute = location.pathname === '/'
  const navigate = useNavigate()
  const auth = useAuthStore()
  const navigationLinks =
    auth.user?.roles?.some((role) => ['super_admin', 'admin', 'designer', 'moderator'].includes(role))
      ? [...links, { to: '/admin', label: 'Admin' }]
      : links
  const snapshot = useLiveDataStore((state) => state.snapshot)
  const fallbackStation = useStation({ enabled: true, refetchInterval: 1000 })
  const preview = useActionPreviewStore((state) => state.preview)
  const inventories = isDashboardRoute
    ? snapshot?.station.inventories ?? fallbackStation.data?.inventories ?? []
    : fallbackStation.data?.inventories ?? []
  const [floatingDeltas, setFloatingDeltas] = useState<FloatingDelta[]>([])
  const previousAmountsRef = useRef<Record<string, number>>({})
  const isFirstPaintRef = useRef(true)

  useEffect(() => {
    setFloatingDeltas([])
    previousAmountsRef.current = {}
    isFirstPaintRef.current = true
  }, [location.pathname])

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState !== 'visible') return
      setFloatingDeltas([])
      previousAmountsRef.current = {}
      isFirstPaintRef.current = true
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  useEffect(() => {
    if (!inventories.length) return

    const currentAmounts = Object.fromEntries(inventories.map((item) => [item.resource, Number(item.amount)]))

    if (isFirstPaintRef.current) {
      previousAmountsRef.current = currentAmounts
      isFirstPaintRef.current = false
      return
    }

    const nextDeltas = inventories
      .map((item) => {
        const previous = previousAmountsRef.current[item.resource]
        const current = Number(item.amount)
        const delta = previous === undefined ? 0 : Number((current - previous).toFixed(2))
        if (!delta) return null
        return {
          id: `${item.resource}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          resource: item.resource,
          amount: delta
        }
      })
      .filter((item): item is FloatingDelta => item !== null)

    previousAmountsRef.current = currentAmounts

    if (!nextDeltas.length) return

    setFloatingDeltas((current) => {
      const incomingResources = new Set(nextDeltas.map((item) => item.resource))
      const preserved = current.filter((item) => !incomingResources.has(item.resource))
      return [...preserved, ...nextDeltas]
    })

    const timers = nextDeltas.map((delta) =>
      window.setTimeout(() => {
        setFloatingDeltas((current) => current.filter((item) => item.id !== delta.id))
      }, 1100)
    )

    return () => {
      timers.forEach((timer) => window.clearTimeout(timer))
    }
  }, [inventories])

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,#182637_0%,#0b1118_60%)] text-textMain">
      <header className="sticky top-0 z-20 border-b border-borderSoft bg-bg/90 px-4 py-3 backdrop-blur">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="text-[10px] uppercase tracking-[0.28em] text-accentWarm">Sector Relay</div>
            <div className="text-sm text-textMute">{t.panel}</div>
          </div>
          <div className="hidden items-center gap-2 md:flex">
            {navigationLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `rounded-full px-3 py-2 text-sm ${isActive ? 'bg-panelSoft text-accent' : 'text-textMute'}`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </div>
          <button
            className="rounded-full border border-borderSoft px-3 py-2 text-xs text-textMute"
            onClick={async () => {
              await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
              auth.logout()
              navigate('/auth')
            }}
          >
            {t.logout}
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-[1600px] lg:pl-[296px]">
        <aside className="fixed bottom-0 left-0 top-[73px] hidden w-[280px] border-r border-borderSoft bg-bg/92 px-4 py-4 backdrop-blur lg:block">
          <div className="flex h-full flex-col">
            <div className="pb-4">
              <div className="text-[10px] uppercase tracking-[0.24em] text-accentWarm">{t.inventory}</div>
            </div>

            <div className="flex-1 space-y-2 overflow-y-auto pr-1">
              {inventories.map((item) => {
                const requirement = preview?.costs.find((cost) => cost.resource === item.resource)
                const available = Number(item.amount)
                const needed = requirement?.amount ?? 0
                const isEnough = requirement ? available >= needed : false
                const isMissing = requirement ? available < needed : false
                const activeDeltas = floatingDeltas.filter((delta) => delta.resource === item.resource)

                return (
                  <div
                    key={item.resource}
                    className={`relative min-h-[74px] overflow-visible rounded-2xl border px-3 py-3 transition ${
                      isEnough
                        ? 'border-emerald-500/50 bg-emerald-500/10'
                        : isMissing
                          ? 'border-danger/50 bg-danger/10'
                          : 'border-borderSoft bg-panelSoft'
                    }`}
                    title={describeResource(item.resource)}
                  >
                    {activeDeltas.map((delta) => (
                      <div
                        key={delta.id}
                        className={`inventory-delta z-[80] ${delta.amount > 0 ? 'inventory-delta-positive' : 'inventory-delta-negative'}`}
                        style={{ right: 8, top: 6 }}
                      >
                        {formatDelta(delta.amount)}
                      </div>
                    ))}

                    <div className="pr-14 text-[10px] uppercase tracking-[0.18em] text-textMute">
                      {labelForResource(item.resource)}
                    </div>
                    <div className="mt-1 text-lg font-semibold text-textMain">{formatAmount(item.amount)}</div>

                    {requirement ? (
                      <div
                        className={`absolute bottom-2 right-2 text-[11px] ${isEnough ? 'text-emerald-300/90' : 'text-danger/90'}`}
                      >
                        {Math.ceil(needed)}
                      </div>
                    ) : null}
                  </div>
                )
              })}
            </div>
          </div>
        </aside>

        <main className="px-4 pb-28 pt-4">
          <Outlet />
        </main>
      </div>

      <ToastViewport />
      <ChatWidget />

      <nav className="fixed bottom-0 left-0 right-0 border-t border-borderSoft bg-bg/95 px-2 py-2 backdrop-blur md:hidden">
        <div className="mx-auto flex max-w-3xl gap-2 overflow-x-auto">
          {navigationLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `min-w-[72px] rounded-xl px-2 py-3 text-center text-[11px] ${isActive ? 'bg-panelSoft text-accent' : 'text-textMute'}`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
