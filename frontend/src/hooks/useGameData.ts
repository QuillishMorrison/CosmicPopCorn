import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import type {
  AdminAuditLogRow,
  AdminAuthz,
  AdminBalanceItem,
  AdminBalanceRevision,
  AdminContentItem,
  AdminContentRevision,
  AdminPlayerDetailRow,
  AdminPlayerSummaryRow,
  AdminUserRow,
  ChatMessageRow,
  ChatThreadRow,
  ContractRow,
  MarketRow,
  MetaUpgrade,
  NotificationRow,
  ReportView,
  SectorSnapshot,
  StationView
} from '../types/game'

type QueryOptions = {
  refetchInterval?: number | false
  enabled?: boolean
}

export function useStation(options?: QueryOptions) {
  return useQuery({
    queryKey: ['station'],
    queryFn: () => api.get<StationView>('/station/me'),
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled,
    placeholderData: keepPreviousData,
    staleTime: 10000,
    refetchOnWindowFocus: false
  })
}

export function useReports(options?: QueryOptions) {
  return useQuery({
    queryKey: ['reports'],
    queryFn: () => api.get<ReportView[]>('/station/reports'),
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled,
    placeholderData: keepPreviousData,
    staleTime: 10000,
    refetchOnWindowFocus: false
  })
}

export function useMarket(options?: QueryOptions) {
  return useQuery({
    queryKey: ['market'],
    queryFn: () => api.get<MarketRow[]>('/market/state'),
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled,
    placeholderData: keepPreviousData,
    staleTime: 10000,
    refetchOnWindowFocus: false
  })
}

export function useNpcContracts(options?: QueryOptions) {
  return useQuery({
    queryKey: ['contracts', 'npc'],
    queryFn: () => api.get<ContractRow[]>('/contracts/npc'),
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled,
    placeholderData: keepPreviousData,
    staleTime: 10000,
    refetchOnWindowFocus: false
  })
}

export function usePlayerContracts(options?: QueryOptions) {
  return useQuery({
    queryKey: ['contracts', 'player'],
    queryFn: () => api.get<ContractRow[]>('/contracts/player'),
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled,
    staleTime: 15000,
    refetchOnWindowFocus: false
  })
}

export function useMetaTree(options?: QueryOptions) {
  return useQuery({
    queryKey: ['meta'],
    queryFn: () => api.get<MetaUpgrade[]>('/meta/tree'),
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled,
    staleTime: 60000,
    refetchOnWindowFocus: false
  })
}

export function useSector(options?: QueryOptions) {
  return useQuery({
    queryKey: ['sector'],
    queryFn: () => api.get<SectorSnapshot>('/sector/snapshot'),
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled,
    staleTime: 15000,
    refetchOnWindowFocus: false
  })
}

export function useNotifications(options?: QueryOptions) {
  return useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.get<NotificationRow[]>('/notifications/'),
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled,
    staleTime: 15000,
    refetchOnWindowFocus: false
  })
}

export function useGlobalChat(options?: QueryOptions) {
  return useQuery({
    queryKey: ['chat', 'global'],
    queryFn: () => api.get<ChatMessageRow[]>('/chat/global'),
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled,
    placeholderData: keepPreviousData,
    staleTime: 5000,
    refetchOnWindowFocus: false
  })
}

export function useChatThreads(options?: QueryOptions) {
  return useQuery({
    queryKey: ['chat', 'threads'],
    queryFn: () => api.get<ChatThreadRow[]>('/chat/threads'),
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled,
    placeholderData: keepPreviousData,
    staleTime: 5000,
    refetchOnWindowFocus: false
  })
}

export function useDirectChat(userId: string | null, options?: QueryOptions) {
  return useQuery({
    queryKey: ['chat', 'direct', userId],
    queryFn: () => api.get<ChatMessageRow[]>(`/chat/direct/${userId}`),
    refetchInterval: options?.refetchInterval,
    enabled: Boolean(userId) && options?.enabled !== false,
    placeholderData: keepPreviousData,
    staleTime: 5000,
    refetchOnWindowFocus: false
  })
}

export function useAdminAuthz(options?: QueryOptions) {
  return useQuery({
    queryKey: ['admin', 'authz'],
    queryFn: () => api.get<AdminAuthz>('/admin/authz/me'),
    enabled: options?.enabled,
    staleTime: 10000,
    refetchOnWindowFocus: false
  })
}

export function useAdminContentList(search?: string, type?: string) {
  const params = new URLSearchParams()
  if (search) params.set('search', search)
  if (type) params.set('content_type', type)
  const suffix = params.toString() ? `?${params.toString()}` : ''
  return useQuery({
    queryKey: ['admin', 'content', search, type],
    queryFn: () => api.get<AdminContentItem[]>(`/admin/content${suffix}`),
    staleTime: 5000,
    refetchOnWindowFocus: false
  })
}

export function useAdminContentItem(type: string | undefined, key: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ['admin', 'content', type, key],
    queryFn: () => api.get<AdminContentItem>(`/admin/content/${type}/${key}`),
    enabled: Boolean(type && key && enabled),
    staleTime: 5000,
    refetchOnWindowFocus: false
  })
}

export function useAdminContentRevisions(type: string | undefined, key: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ['admin', 'content', type, key, 'revisions'],
    queryFn: () => api.get<AdminContentRevision[]>(`/admin/content/${type}/${key}/revisions`),
    enabled: Boolean(type && key && enabled),
    staleTime: 5000,
    refetchOnWindowFocus: false
  })
}

export function useAdminBalance() {
  return useQuery({
    queryKey: ['admin', 'balance'],
    queryFn: () => api.get<AdminBalanceItem[]>('/admin/balance'),
    staleTime: 5000,
    refetchOnWindowFocus: false
  })
}

export function useAdminBalanceRevisions(key: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ['admin', 'balance', key, 'revisions'],
    queryFn: () => api.get<AdminBalanceRevision[]>(`/admin/balance/${key}/revisions`),
    enabled: Boolean(key && enabled),
    staleTime: 5000,
    refetchOnWindowFocus: false
  })
}

export function useAdminAudit() {
  return useQuery({
    queryKey: ['admin', 'audit'],
    queryFn: () => api.get<AdminAuditLogRow[]>('/admin/audit'),
    staleTime: 5000,
    refetchOnWindowFocus: false
  })
}

export function useAdminUsers(enabled = true) {
  return useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => api.get<AdminUserRow[]>('/admin/users'),
    enabled,
    staleTime: 5000,
    refetchOnWindowFocus: false
  })
}

export function useAdminPlayers(enabled = true) {
  return useQuery({
    queryKey: ['admin', 'players'],
    queryFn: () => api.get<AdminPlayerSummaryRow[]>('/admin/players'),
    enabled,
    staleTime: 5000,
    refetchOnWindowFocus: false
  })
}

export function useAdminPlayerDetail(stationId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ['admin', 'players', stationId],
    queryFn: () => api.get<AdminPlayerDetailRow>(`/admin/players/${stationId}`),
    enabled: Boolean(stationId && enabled),
    staleTime: 5000,
    refetchOnWindowFocus: false
  })
}
