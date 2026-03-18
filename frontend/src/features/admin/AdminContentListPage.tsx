import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAdminContentList } from '../../hooks/useGameData'

const types = ['resource', 'module', 'event', 'contract_template', 'meta_upgrade', 'specialization']

export function AdminContentListPage() {
  const [type, setType] = useState('')
  const [search, setSearch] = useState('')
  const content = useAdminContentList(search, type || undefined)

  return (
    <div className="space-y-4">
      <section className="rounded-3xl border border-borderSoft bg-panel px-4 py-4">
        <div className="flex flex-wrap gap-3">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Поиск по key или названию"
            className="min-w-[240px] flex-1 rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain"
          />
          <select
            value={type}
            onChange={(event) => setType(event.target.value)}
            className="rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain"
          >
            <option value="">Все типы</option>
            {types.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section className="rounded-3xl border border-borderSoft bg-panel px-4 py-4">
        <div className="mb-3 flex flex-wrap gap-2">
          {types.map((item) => (
            <Link
              key={item}
              to={`/admin/content/new/${item}`}
              className="rounded-full border border-borderSoft px-3 py-2 text-xs text-textMain"
            >
              Создать {item}
            </Link>
          ))}
        </div>
        <div className="space-y-2">
          {(content.data ?? []).map((item) => (
            <Link
              key={`${item.content_type}-${item.key}`}
              to={`/admin/content/${item.content_type}/${item.key}`}
              className="block rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 transition hover:border-accent/40"
            >
              <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.18em] text-textMute">
                <span>{item.content_type}</span>
                <span>{item.status}</span>
                <span>{item.source_kind}</span>
              </div>
              <div className="mt-2 flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-textMain">{item.display_name}</div>
                  <div className="text-xs text-textMute">{item.key}</div>
                </div>
                <div className="text-xs text-textMute">rev {item.current_revision_id ?? '—'}</div>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
