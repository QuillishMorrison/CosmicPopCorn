import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAdminBalance, useAdminBalanceRevisions } from '../../hooks/useGameData'
import { useActionFeedback } from '../../hooks/useActionFeedback'
import { api } from '../../lib/api'

export function AdminBalancePage() {
  const queryClient = useQueryClient()
  const feedback = useActionFeedback()
  const balance = useAdminBalance()
  const [selectedKey, setSelectedKey] = useState<string | undefined>(undefined)
  const [value, setValue] = useState('1')
  const revisions = useAdminBalanceRevisions(selectedKey)

  async function save(key: string, category: string) {
    try {
      await api.patch('/admin/balance', {
        key,
        category,
        scope: 'global',
        summary: 'Quick edit from admin balance page',
        value: { value: Number(value) },
        enabled: true
      })
      await queryClient.invalidateQueries({ queryKey: ['admin', 'balance'] })
      feedback.success('Параметр сохранён.')
    } catch (error) {
      feedback.error(error)
    }
  }

  async function publish(key: string) {
    try {
      await api.post(`/admin/balance/${key}/publish`)
      await queryClient.invalidateQueries({ queryKey: ['admin', 'balance'] })
      feedback.success('Баланс опубликован.')
    } catch (error) {
      feedback.error(error)
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_0.9fr]">
      <section className="rounded-3xl border border-borderSoft bg-panel px-4 py-4">
        <div className="text-lg font-semibold">Баланс и экономика</div>
        <div className="mt-3 space-y-2">
          {(balance.data ?? []).map((item) => (
            <div key={item.key} className="rounded-2xl border border-borderSoft bg-panelSoft px-3 py-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="text-sm font-semibold text-textMain">{item.key}</div>
                  <div className="text-xs text-textMute">{item.category}</div>
                </div>
                <button
                  className="rounded-full border border-borderSoft px-3 py-2 text-xs text-textMain"
                  onClick={() => {
                    setSelectedKey(item.key)
                    setValue(String(item.value_json.value ?? 0))
                  }}
                >
                  Редактировать
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-borderSoft bg-panel px-4 py-4">
        <div className="text-sm font-semibold">Редактор параметра</div>
        {selectedKey ? (
          <div className="mt-3 space-y-3">
            <div className="text-sm text-textMain">{selectedKey}</div>
            <input value={value} onChange={(event) => setValue(event.target.value)} className="w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain" />
            <div className="flex gap-2">
              <button className="rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-slate-950" onClick={() => save(selectedKey, 'custom')}>
                Сохранить draft
              </button>
              <button className="rounded-2xl border border-borderSoft px-4 py-3 text-sm text-textMain" onClick={() => publish(selectedKey)}>
                Publish
              </button>
            </div>
            <div className="space-y-2">
              {(revisions.data ?? []).map((revision) => (
                <div key={revision.id} className="rounded-2xl border border-borderSoft bg-panelSoft px-3 py-3 text-xs text-textMute">
                  v{revision.version} • {revision.change_summary || 'Без описания'}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="mt-3 text-sm text-textMute">Выбери параметр слева.</div>
        )}
      </section>
    </div>
  )
}
