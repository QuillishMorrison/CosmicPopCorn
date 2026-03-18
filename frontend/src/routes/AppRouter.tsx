import { Suspense, lazy, useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from '../components/Layout'
import { api } from '../lib/api'
import { useAuthStore } from '../store/authStore'

const AuthPage = lazy(() => import('../features/auth/AuthPage').then((module) => ({ default: module.AuthPage })))
const AdminAuditPage = lazy(() =>
  import('../features/admin/AdminAuditPage').then((module) => ({ default: module.AdminAuditPage }))
)
const AdminBalancePage = lazy(() =>
  import('../features/admin/AdminBalancePage').then((module) => ({ default: module.AdminBalancePage }))
)
const AdminContentEditorPage = lazy(() =>
  import('../features/admin/AdminContentEditorPage').then((module) => ({ default: module.AdminContentEditorPage }))
)
const AdminContentListPage = lazy(() =>
  import('../features/admin/AdminContentListPage').then((module) => ({ default: module.AdminContentListPage }))
)
const AdminDashboardPage = lazy(() =>
  import('../features/admin/AdminDashboardPage').then((module) => ({ default: module.AdminDashboardPage }))
)
const AdminLayout = lazy(() =>
  import('../features/admin/AdminLayout').then((module) => ({ default: module.AdminLayout }))
)
const AdminPlayersPage = lazy(() =>
  import('../features/admin/AdminPlayersPage').then((module) => ({ default: module.AdminPlayersPage }))
)
const AdminRolesPage = lazy(() =>
  import('../features/admin/AdminRolesPage').then((module) => ({ default: module.AdminRolesPage }))
)
const ContractsPage = lazy(() =>
  import('../features/contracts/ContractsPage').then((module) => ({ default: module.ContractsPage }))
)
const DashboardPage = lazy(() =>
  import('../features/dashboard/DashboardPage').then((module) => ({ default: module.DashboardPage }))
)
const GuidePage = lazy(() => import('../features/guide/GuidePage').then((module) => ({ default: module.GuidePage })))
const MarketPage = lazy(() =>
  import('../features/market/MarketPage').then((module) => ({ default: module.MarketPage }))
)
const MetaPage = lazy(() => import('../features/meta/MetaPage').then((module) => ({ default: module.MetaPage })))
const SectorPage = lazy(() =>
  import('../features/sector/SectorPage').then((module) => ({ default: module.SectorPage }))
)
const SettingsPage = lazy(() =>
  import('../features/settings/SettingsPage').then((module) => ({ default: module.SettingsPage }))
)

function RouteLoader() {
  return <div className="py-10 text-center text-sm text-textMute">Загрузка экрана...</div>
}

function Protected() {
  const token = useAuthStore((state) => state.accessToken)
  return token ? <Layout /> : <Navigate to="/auth" replace />
}

function AdminProtected() {
  const token = useAuthStore((state) => state.accessToken)
  const roles = useAuthStore((state) => state.user?.roles ?? [])
  if (!token) return <Navigate to="/auth" replace />
  if (!roles.some((role) => ['super_admin', 'admin', 'designer', 'moderator'].includes(role))) {
    return <Navigate to="/" replace />
  }
  return <AdminLayout />
}

export function AppRouter() {
  const { accessToken, hasSessionHint, setSession, setUser, user, logout, clearSessionHint } = useAuthStore()
  const [booted, setBooted] = useState(false)

  useEffect(() => {
    if (accessToken) {
      if (!user || !Array.isArray(user.roles)) {
        void api
          .get<{ id: string; email: string; username: string; roles?: string[] }>('/auth/me')
          .then((me) => setUser(me))
          .catch(() => {
            clearSessionHint()
            logout()
          })
          .finally(() => setBooted(true))
        return
      }
      setBooted(true)
      return
    }
    if (!hasSessionHint) {
      setBooted(true)
      return
    }
    void api
      .post<{ access_token: string; user: { id: string; email: string; username: string; roles?: string[] } }>('/auth/refresh')
      .then((data) => setSession(data.access_token, data.user))
      .catch(() => {
        clearSessionHint()
        logout()
      })
      .finally(() => setBooted(true))
  }, [accessToken, clearSessionHint, hasSessionHint, logout, setSession, setUser, user])

  if (!booted) {
    return <div className="flex min-h-screen items-center justify-center bg-bg text-textMute">Синхронизация с сектором...</div>
  }

  return (
    <Suspense fallback={<RouteLoader />}>
      <Routes>
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/" element={<Protected />}>
          <Route index element={<DashboardPage />} />
          <Route path="guide" element={<GuidePage />} />
          <Route path="market" element={<MarketPage />} />
          <Route path="contracts" element={<ContractsPage />} />
          <Route path="meta" element={<MetaPage />} />
          <Route path="sector" element={<SectorPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="admin" element={<AdminProtected />}>
            <Route index element={<AdminDashboardPage />} />
            <Route path="players" element={<AdminPlayersPage />} />
            <Route path="players/:stationId" element={<AdminPlayersPage />} />
            <Route path="content" element={<AdminContentListPage />} />
            <Route path="content/new/:type" element={<AdminContentEditorPage />} />
            <Route path="content/:type/:key" element={<AdminContentEditorPage />} />
            <Route path="balance" element={<AdminBalancePage />} />
            <Route path="audit" element={<AdminAuditPage />} />
            <Route path="roles" element={<AdminRolesPage />} />
          </Route>
        </Route>
      </Routes>
    </Suspense>
  )
}
