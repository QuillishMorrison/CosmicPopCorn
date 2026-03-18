import { NavLink, Outlet } from 'react-router-dom'

const links = [
  { to: '/admin', label: 'Обзор' },
  { to: '/admin/players', label: 'Игроки' },
  { to: '/admin/content', label: 'Контент' },
  { to: '/admin/balance', label: 'Баланс' },
  { to: '/admin/audit', label: 'Аудит' },
  { to: '/admin/roles', label: 'Роли' }
]

export function AdminLayout() {
  return (
    <div className="space-y-4">
      <div className="rounded-3xl border border-borderSoft bg-panel px-4 py-4">
        <div className="text-[11px] uppercase tracking-[0.22em] text-accentWarm">Designer Console</div>
        <div className="mt-2 text-sm text-textMute">
          Живые правки баланса, контента, ролей и показателей игроков без перезапуска сервера.
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/admin'}
              className={({ isActive }) =>
                `rounded-full px-3 py-2 text-sm ${isActive ? 'bg-accent text-slate-950' : 'bg-panelSoft text-textMute'}`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>
      </div>
      <Outlet />
    </div>
  )
}
