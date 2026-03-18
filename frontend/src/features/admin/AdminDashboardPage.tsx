import { Link } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useActionFeedback } from '../../hooks/useActionFeedback'
import { useAdminAudit, useAdminAuthz, useAdminBalance, useAdminContentList } from '../../hooks/useGameData'
import { api } from '../../lib/api'

export function AdminDashboardPage() {
  const content = useAdminContentList()
  const balance = useAdminBalance()
  const audit = useAdminAudit()
  const authz = useAdminAuthz()
  const queryClient = useQueryClient()
  const feedback = useActionFeedback()
  const canWipeServer = authz.data?.permissions.includes('*') || authz.data?.permissions.includes('server.wipe')

  const stats = [
    { label: 'Контентных записей', value: content.data?.length ?? 0 },
    { label: 'Баланс-параметров', value: balance.data?.length ?? 0 },
    { label: 'Последних действий', value: audit.data?.length ?? 0 }
  ]

  async function wipeServer() {
    if (!canWipeServer) return
    const confirmed = window.confirm(
      'Сделать полный вайп сервера? Это сбросит игровой прогресс всех игроков, но сохранит аккаунты, роли и админ-контент.'
    )
    if (!confirmed) return
    try {
      await api.post('/admin/server/wipe')
      await queryClient.invalidateQueries({ queryKey: ['admin'] })
      await queryClient.invalidateQueries({ queryKey: ['station'] })
      await queryClient.invalidateQueries({ queryKey: ['market'] })
      await queryClient.invalidateQueries({ queryKey: ['contracts'] })
      feedback.success('Серверный вайп выполнен.')
    } catch (error) {
      feedback.error(error)
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
      <section className="rounded-3xl border border-borderSoft bg-panel px-4 py-4">
        <div className="text-lg font-semibold">Панель администратора</div>
        <div className="mt-1 text-sm text-textMute">
          Последние изменения, быстрые входы в редакторы и live-контекст сектора.
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {stats.map((item) => (
            <div key={item.label} className="rounded-2xl border border-borderSoft bg-panelSoft px-3 py-3">
              <div className="text-xs text-textMute">{item.label}</div>
              <div className="mt-1 text-2xl font-semibold text-textMain">{item.value}</div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link className="rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-slate-950" to="/admin/content/new/module">
            Создать модуль
          </Link>
          <Link className="rounded-2xl border border-borderSoft px-4 py-3 text-sm text-textMain" to="/admin/content/new/resource">
            Создать ресурс
          </Link>
          <Link className="rounded-2xl border border-borderSoft px-4 py-3 text-sm text-textMain" to="/admin/content/new/event">
            Создать событие
          </Link>
          {canWipeServer ? (
            <button
              className="rounded-2xl border border-danger/50 bg-danger/10 px-4 py-3 text-sm text-danger"
              onClick={wipeServer}
              type="button"
            >
              Вайп сервера
            </button>
          ) : null}
        </div>
      </section>

      <section className="rounded-3xl border border-borderSoft bg-panel px-4 py-4">
        <div className="text-sm font-semibold">Последний аудит</div>
        <div className="mt-3 space-y-2">
          {(audit.data ?? []).slice(0, 6).map((item) => (
            <div key={item.id} className="rounded-2xl border border-borderSoft bg-panelSoft px-3 py-3">
              <div className="text-xs uppercase tracking-[0.18em] text-textMute">{item.action_type}</div>
              <div className="mt-1 text-sm text-textMain">{item.summary}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
