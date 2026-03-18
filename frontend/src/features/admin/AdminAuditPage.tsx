import { useAdminAudit } from '../../hooks/useGameData'

export function AdminAuditPage() {
  const audit = useAdminAudit()

  return (
    <section className="rounded-3xl border border-borderSoft bg-panel px-4 py-4">
      <div className="text-lg font-semibold">Audit log</div>
      <div className="mt-3 space-y-2">
        {(audit.data ?? []).map((item) => (
          <div key={item.id} className="rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3">
            <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.18em] text-textMute">
              <span>{item.action_type}</span>
              <span>{item.target_type}</span>
              <span>{item.target_id}</span>
            </div>
            <div className="mt-2 text-sm text-textMain">{item.summary}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
