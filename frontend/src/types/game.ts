export type ResourceAmount = { resource: string; amount: number }
export type ModuleView = { module_key: string; level: number; is_active: boolean }
export type ModuleDefinition = {
  key: string
  name: string
  description: string
  category: string
  max_level: number
  base_cost: Record<string, number>
  upgrade_cost_growth: number
  energy_delta: number
  throughput_delta: number
  crew_requirement: number
  sort_order: number
}
export type StationView = {
  id: string
  name: string
  level: number
  specialization: string
  throughput: number
  efficiency: number
  stability: number
  reputation: number
  bottlenecks: string[]
  recommended_actions: string[]
  inventories: ResourceAmount[]
  modules: ModuleView[]
  module_catalog: ModuleDefinition[]
  last_processed_at: string
}

export type ReportView = {
  id: string
  started_at: string
  ended_at: string
  summary: Record<string, unknown>
  claimed_at: string | null
}

export type MarketRow = { resource: string; price: number; trend: number; history: number[] }
export type ContractRow = {
  id: string
  title: string
  contract_type: string
  resource: string
  quantity: number
  reward_credits: number
  reward_reputation: number
  status: string
  source: string
  issuer_station_id: string | null
  taker_station_id: string | null
  expires_at: string
}
export type MetaUpgrade = {
  key: string
  name: string
  description: string
  base_cost: number
  max_level: number
  effect_type: string
  effect_value: number
  current_level: number
}
export type SectorSnapshot = {
  sector_id: string
  sector_name: string
  market_mode: string
  market_mood: string
  players: {
    station_id: string
    station_name: string
    owner_username: string
    specialization: string
    level: number
    reputation: number
  }[]
  events: { id: string; title: string; description: string; ends_at: string }[]
}
export type NotificationRow = {
  id: string
  type: string
  title: string
  message: string
  payload: Record<string, unknown>
  read_at: string | null
}

export type LiveDashboardSnapshot = {
  station: StationView
  reports: ReportView[]
  market: MarketRow[]
  npc_contracts: ContractRow[]
  npc_contract_visibility: number
}

export type ChatMessageRow = {
  id: string
  sender_user_id: string
  sender_username: string
  recipient_user_id: string | null
  body: string
  created_at: string
}

export type ChatThreadRow = {
  user_id: string
  username: string
  station_name: string | null
  last_message: string | null
  last_message_at: string | null
  unread_count: number
}

export type AdminContentType =
  | 'resource'
  | 'module'
  | 'event'
  | 'contract_template'
  | 'meta_upgrade'
  | 'specialization'

export type AdminContentItem = {
  id: number
  content_type: AdminContentType
  key: string
  display_name: string
  source_kind: string
  status: string
  tags: string[]
  current_revision_id: number | null
  published_revision_id: number | null
  updated_by: string | null
  updated_at: string
  payload?: Record<string, unknown> | null
}

export type AdminContentRevision = {
  id: number
  version: number
  change_summary: string
  is_published: boolean
  published_at: string | null
  author_user_id: string | null
  payload_json: Record<string, unknown>
  created_at: string
}

export type AdminBalanceItem = {
  id: number
  key: string
  category: string
  scope: string
  enabled: boolean
  value_json: Record<string, unknown>
  current_revision_id: number | null
  published_revision_id: number | null
  updated_at: string
}

export type AdminBalanceRevision = {
  id: number
  version: number
  change_summary: string
  is_published: boolean
  published_at: string | null
  author_user_id: string | null
  value_json: Record<string, unknown>
  created_at: string
}

export type AdminAuditLogRow = {
  id: number
  actor_user_id: string | null
  action_type: string
  target_type: string
  target_id: string
  summary: string
  metadata_json: Record<string, unknown>
  created_at: string
}

export type AdminUserRow = {
  id: string
  username: string
  email: string
  roles: string[]
}

export type AdminPlayerSummaryRow = {
  station_id: string
  owner_user_id: string
  username: string
  email: string
  is_active: boolean
  station_name: string
  specialization: string
  level: number
  throughput: number
  efficiency: number
  stability: number
  reputation: number
  updated_at: string
}

export type AdminPlayerDetailRow = AdminPlayerSummaryRow & {
  public_notes: string
  inventories: { resource: string; amount: number }[]
  modules: { module_key: string; level: number; is_active: boolean }[]
  last_processed_at: string
}

export type AdminAuthz = {
  user_id: string
  username: string
  roles: string[]
  permissions: string[]
}
