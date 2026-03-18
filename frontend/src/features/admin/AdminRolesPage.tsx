import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAdminUsers } from '../../hooks/useGameData'
import { useActionFeedback } from '../../hooks/useActionFeedback'
import { api } from '../../lib/api'

const availableRoles = ['super_admin', 'admin', 'designer', 'moderator']

export function AdminRolesPage() {
  const queryClient = useQueryClient()
  const feedback = useActionFeedback()
  const users = useAdminUsers()
  const [draftRoles, setDraftRoles] = useState<Record<string, string[]>>({})

  async function save(userId: string) {
    try {
      await api.post('/admin/roles', { user_id: userId, roles: draftRoles[userId] ?? [] })
      await queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      feedback.success('Роли обновлены.')
    } catch (error) {
      feedback.error(error)
    }
  }

  return (
    <section className="rounded-3xl border border-borderSoft bg-panel px-4 py-4">
      <div className="text-lg font-semibold">Роли и доступ</div>
      <div className="mt-3 space-y-3">
        {(users.data ?? []).map((user) => {
          const current = draftRoles[user.id] ?? user.roles
          return (
            <div key={user.id} className="rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3">
              <div className="text-sm font-semibold text-textMain">{user.username}</div>
              <div className="text-xs text-textMute">{user.email}</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {availableRoles.map((role) => {
                  const active = current.includes(role)
                  return (
                    <button
                      key={role}
                      type="button"
                      className={`rounded-full px-3 py-2 text-xs ${active ? 'bg-accent text-slate-950' : 'border border-borderSoft text-textMute'}`}
                      onClick={() =>
                        setDraftRoles((state) => ({
                          ...state,
                          [user.id]: active ? current.filter((item) => item !== role) : [...current, role]
                        }))
                      }
                    >
                      {role}
                    </button>
                  )
                })}
              </div>
              <button className="mt-3 rounded-2xl border border-borderSoft px-4 py-3 text-sm text-textMain" onClick={() => save(user.id)}>
                Сохранить роли
              </button>
            </div>
          )
        })}
      </div>
    </section>
  )
}
