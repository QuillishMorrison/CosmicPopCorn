import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useAdminContentItem, useAdminContentRevisions } from '../../hooks/useGameData'
import { useActionFeedback } from '../../hooks/useActionFeedback'
import { api } from '../../lib/api'

const defaultPayloads: Record<string, Record<string, unknown>> = {
  resource: {
    key: '',
    name: '',
    description: '',
    icon_key: 'resource',
    rarity: 'common',
    category: 'utility',
    base_price: 10,
    sort_order: 100,
    is_public: true,
    is_visible: true,
    enabled: true,
    starting_amount: 0
  },
  module: {
    key: '',
    name: '',
    description: '',
    category: 'utility',
    max_level: 10,
    base_cost: { credits: 100 },
    upgrade_cost_growth: 0.45,
    base_effect: {},
    effects: [],
    energy_delta: 0,
    throughput_delta: 0,
    crew_delta: 0,
    crew_requirement: 0,
    unlock_requirements: [],
    specialization_tags: [],
    sort_order: 100,
    enabled: true,
    is_visible: true
  },
  event: {
    key: '',
    title: '',
    short_description: '',
    long_description: '',
    event_type: 'market_shift',
    duration_minutes: 60,
    weight: 1,
    conditions: { all: [{ field: 'sector_player_count', op: '>=', value: 1 }] },
    market_effects: {},
    effects: [],
    scope: 'sector',
    enabled: true,
    cooldown_minutes: 30,
    tags: []
  }
}

export function AdminContentEditorPage() {
  const params = useParams()
  const navigate = useNavigate()
  const feedback = useActionFeedback()
  const queryClient = useQueryClient()
  const type = params.type as string
  const key = params.key
  const isNew = key === undefined
  const item = useAdminContentItem(type, key, !isNew)
  const revisions = useAdminContentRevisions(type, key, !isNew)
  const [displayName, setDisplayName] = useState('')
  const [summary, setSummary] = useState('')
  const [payloadText, setPayloadText] = useState('{}')

  const template = useMemo(() => JSON.stringify(defaultPayloads[type] ?? { key: '', name: '' }, null, 2), [type])

  useEffect(() => {
    if (isNew) {
      setDisplayName('')
      setPayloadText(template)
      return
    }
    if (item.data) {
      setDisplayName(item.data.display_name)
      setPayloadText(JSON.stringify(item.data.payload ?? {}, null, 2))
    }
  }, [isNew, item.data, template])

  async function saveDraft(event: FormEvent) {
    event.preventDefault()
    try {
      const payload = JSON.parse(payloadText) as Record<string, unknown>
      const body = {
        content_type: type,
        key: String(payload.key ?? key ?? ''),
        display_name: displayName || String(payload.name ?? payload.title ?? payload.key ?? ''),
        summary,
        payload,
        tags: Array.isArray(payload.tags) ? payload.tags : []
      }
      const result = await api.post(`/admin/content`, body)
      await queryClient.invalidateQueries({ queryKey: ['admin', 'content'] })
      feedback.success('Черновик сохранён.')
      navigate(`/admin/content/${type}/${(result as { key: string }).key}`)
    } catch (error) {
      feedback.error(error)
    }
  }

  async function publish() {
    if (!key) return
    try {
      await api.post(`/admin/content/${type}/${key}/publish`)
      await queryClient.invalidateQueries({ queryKey: ['admin', 'content'] })
      feedback.success('Изменение опубликовано.')
    } catch (error) {
      feedback.error(error)
    }
  }

  async function rollback(version: number) {
    if (!key) return
    try {
      await api.post(`/admin/content/${type}/${key}/rollback?version=${version}`)
      await queryClient.invalidateQueries({ queryKey: ['admin', 'content'] })
      await queryClient.invalidateQueries({ queryKey: ['admin', 'content', type, key] })
      await queryClient.invalidateQueries({ queryKey: ['admin', 'content', type, key, 'revisions'] })
      feedback.success('Откат применён.')
    } catch (error) {
      feedback.error(error)
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
      <form className="rounded-3xl border border-borderSoft bg-panel px-4 py-4" onSubmit={saveDraft}>
        <div className="text-lg font-semibold">Редактор: {type}</div>
        <div className="mt-1 text-sm text-textMute">
          Быстрый draft/publish редактор. Для массивов и эффектов используется структурированный JSON.
          <span className="mt-2 block text-xs text-accentWarm/80">
            `key` — это технический slug для системы. Пиши его латиницей: `biofoam`, `solar_array`, `fuel_mk2`.
            Видимое имя можно писать по-русски в `name` и `display_name`.
          </span>
        </div>
        <div className="mt-4 space-y-3">
          <div>
            <div className="mb-1 text-xs text-textMute">Display name</div>
            <input
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              className="w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain"
            />
          </div>
          <div>
            <div className="mb-1 text-xs text-textMute">Summary</div>
            <input
              value={summary}
              onChange={(event) => setSummary(event.target.value)}
              className="w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain"
            />
          </div>
          <div>
            <div className="mb-1 text-xs text-textMute">Payload JSON</div>
            <textarea
              value={payloadText}
              onChange={(event) => setPayloadText(event.target.value)}
              rows={24}
              className="w-full rounded-3xl border border-borderSoft bg-panelSoft px-4 py-4 font-mono text-xs text-textMain"
            />
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button className="rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-slate-950" type="submit">
            Сохранить draft
          </button>
          {!isNew ? (
            <button
              className="rounded-2xl border border-borderSoft px-4 py-3 text-sm text-textMain"
              onClick={publish}
              type="button"
            >
              Publish
            </button>
          ) : null}
        </div>
      </form>

      <section className="rounded-3xl border border-borderSoft bg-panel px-4 py-4">
        <div className="text-sm font-semibold">История ревизий</div>
        <div className="mt-3 space-y-2">
          {(revisions.data ?? []).map((revision) => (
            <div key={revision.id} className="rounded-2xl border border-borderSoft bg-panelSoft px-3 py-3">
              <div className="flex items-center justify-between gap-2">
                <div className="text-sm text-textMain">Версия {revision.version}</div>
                {key ? (
                  <button className="text-xs text-accent" onClick={() => rollback(revision.version)} type="button">
                    Rollback
                  </button>
                ) : null}
              </div>
              <div className="mt-1 text-xs text-textMute">{revision.change_summary || 'Без описания'}</div>
              <pre className="mt-2 overflow-x-auto rounded-xl bg-bg/60 p-3 text-[11px] text-textMute">
                {JSON.stringify(revision.payload_json, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
