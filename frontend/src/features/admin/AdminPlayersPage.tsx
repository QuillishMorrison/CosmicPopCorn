import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useActionFeedback } from '../../hooks/useActionFeedback'
import { useAdminAuthz, useAdminPlayerDetail, useAdminPlayers } from '../../hooks/useGameData'
import { api } from '../../lib/api'

type EditableInventory = { resource: string; amount: number }
type EditableModule = { module_key: string; level: number; is_active: boolean }

export function AdminPlayersPage() {
  const { stationId } = useParams()
  const navigate = useNavigate()
  const feedback = useActionFeedback()
  const queryClient = useQueryClient()
  const authz = useAdminAuthz()
  const players = useAdminPlayers()
  const detail = useAdminPlayerDetail(stationId, Boolean(stationId))
  const [search, setSearch] = useState('')
  const [stationName, setStationName] = useState('')
  const [specialization, setSpecialization] = useState('')
  const [level, setLevel] = useState(1)
  const [throughput, setThroughput] = useState(0)
  const [efficiency, setEfficiency] = useState(0)
  const [stability, setStability] = useState(0)
  const [reputation, setReputation] = useState(0)
  const [publicNotes, setPublicNotes] = useState('')
  const [isActive, setIsActive] = useState(true)
  const [inventories, setInventories] = useState<EditableInventory[]>([])
  const [modules, setModules] = useState<EditableModule[]>([])

  const canEdit = authz.data?.permissions.includes('*') || authz.data?.permissions.includes('players.edit')
  const canWipe = authz.data?.permissions.includes('*') || authz.data?.permissions.includes('players.wipe')

  const filteredPlayers = useMemo(() => {
    const source = players.data ?? []
    if (!search.trim()) return source
    const needle = search.toLowerCase()
    return source.filter(
      (player) =>
        player.username.toLowerCase().includes(needle) ||
        player.station_name.toLowerCase().includes(needle) ||
        player.email.toLowerCase().includes(needle)
    )
  }, [players.data, search])

  useEffect(() => {
    if (!stationId && filteredPlayers[0]) {
      navigate(`/admin/players/${filteredPlayers[0].station_id}`, { replace: true })
    }
  }, [filteredPlayers, navigate, stationId])

  useEffect(() => {
    if (!detail.data) return
    setStationName(detail.data.station_name)
    setSpecialization(detail.data.specialization)
    setLevel(detail.data.level)
    setThroughput(detail.data.throughput)
    setEfficiency(detail.data.efficiency)
    setStability(detail.data.stability)
    setReputation(detail.data.reputation)
    setPublicNotes(detail.data.public_notes)
    setIsActive(detail.data.is_active)
    setInventories(detail.data.inventories.map((item) => ({ ...item })))
    setModules(detail.data.modules.map((item) => ({ ...item })))
  }, [detail.data])

  async function save() {
    if (!stationId) return
    try {
      await api.patch(`/admin/players/${stationId}`, {
        station_name: stationName,
        specialization,
        level,
        throughput,
        efficiency,
        stability,
        reputation,
        public_notes: publicNotes,
        is_active: isActive,
        inventories,
        modules
      })
      await queryClient.invalidateQueries({ queryKey: ['admin', 'players'] })
      await queryClient.invalidateQueries({ queryKey: ['admin', 'players', stationId] })
      await queryClient.invalidateQueries({ queryKey: ['station'] })
      feedback.success('Показатели игрока обновлены.')
    } catch (error) {
      feedback.error(error)
    }
  }

  async function wipePlayer() {
    if (!stationId || !canWipe || !detail.data) return
    const confirmed = window.confirm(
      `Сделать вайп игрока ${detail.data.username}? Это сбросит станцию, ресурсы, модули, контракты и мета-прогресс, но сохранит аккаунт и роль.`
    )
    if (!confirmed) return
    try {
      await api.post(`/admin/players/${stationId}/wipe`)
      await queryClient.invalidateQueries({ queryKey: ['admin', 'players'] })
      await queryClient.invalidateQueries({ queryKey: ['admin', 'players', stationId] })
      await queryClient.invalidateQueries({ queryKey: ['station'] })
      await queryClient.invalidateQueries({ queryKey: ['market'] })
      await queryClient.invalidateQueries({ queryKey: ['contracts'] })
      feedback.success('Вайп игрока выполнен.')
    } catch (error) {
      feedback.error(error)
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[320px_1fr]">
      <section className="rounded-3xl border border-borderSoft bg-panel px-4 py-4">
        <div className="text-lg font-semibold text-textMain">Игроки</div>
        <div className="mt-2 text-sm text-textMute">Просмотр и ручная правка станций, ресурсов и модулей.</div>
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Поиск по игроку или станции"
          className="mt-4 w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain"
        />
        <div className="mt-4 space-y-2">
          {filteredPlayers.map((player) => (
            <button
              key={player.station_id}
              className={`w-full rounded-2xl border px-3 py-3 text-left ${
                player.station_id === stationId ? 'border-accent bg-accent/10' : 'border-borderSoft bg-panelSoft'
              }`}
              onClick={() => navigate(`/admin/players/${player.station_id}`)}
              type="button"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-textMain">{player.station_name}</div>
                  <div className="truncate text-xs text-textMute">@{player.username}</div>
                </div>
                <div className={`text-[10px] uppercase tracking-[0.18em] ${player.is_active ? 'text-accent' : 'text-danger'}`}>
                  {player.is_active ? 'active' : 'off'}
                </div>
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-borderSoft bg-panel px-4 py-4">
        {!detail.data ? (
          <div className="text-sm text-textMute">Выбери игрока слева.</div>
        ) : (
          <div className="space-y-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="text-lg font-semibold text-textMain">{detail.data.station_name}</div>
                <div className="mt-1 text-sm text-textMute">
                  @{detail.data.username} • {detail.data.email}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {canWipe ? (
                  <button
                    className="rounded-2xl border border-danger/50 bg-danger/10 px-4 py-3 text-sm text-danger"
                    onClick={wipePlayer}
                    type="button"
                  >
                    Вайп игрока
                  </button>
                ) : null}
                <button
                  className="rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50"
                  disabled={!canEdit}
                  onClick={save}
                  type="button"
                >
                  Сохранить
                </button>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              <label className="text-sm text-textMute">
                Станция
                <input value={stationName} onChange={(event) => setStationName(event.target.value)} className="mt-1 w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain" />
              </label>
              <label className="text-sm text-textMute">
                Специализация
                <input value={specialization} onChange={(event) => setSpecialization(event.target.value)} className="mt-1 w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain" />
              </label>
              <label className="flex items-center gap-3 rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain">
                <input checked={isActive} onChange={(event) => setIsActive(event.target.checked)} type="checkbox" />
                Аккаунт активен
              </label>
              <label className="text-sm text-textMute">
                Уровень
                <input value={level} onChange={(event) => setLevel(Number(event.target.value) || 1)} type="number" className="mt-1 w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain" />
              </label>
              <label className="text-sm text-textMute">
                Throughput
                <input value={throughput} onChange={(event) => setThroughput(Number(event.target.value) || 0)} type="number" step="0.1" className="mt-1 w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain" />
              </label>
              <label className="text-sm text-textMute">
                Efficiency
                <input value={efficiency} onChange={(event) => setEfficiency(Number(event.target.value) || 0)} type="number" step="0.01" className="mt-1 w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain" />
              </label>
              <label className="text-sm text-textMute">
                Stability
                <input value={stability} onChange={(event) => setStability(Number(event.target.value) || 0)} type="number" step="0.1" className="mt-1 w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain" />
              </label>
              <label className="text-sm text-textMute">
                Reputation
                <input value={reputation} onChange={(event) => setReputation(Number(event.target.value) || 0)} type="number" step="0.1" className="mt-1 w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain" />
              </label>
            </div>

            <label className="block text-sm text-textMute">
              Публичные заметки
              <textarea
                value={publicNotes}
                onChange={(event) => setPublicNotes(event.target.value)}
                rows={3}
                className="mt-1 w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain"
              />
            </label>

            <div className="grid gap-4 xl:grid-cols-2">
              <div>
                <div className="mb-2 text-sm font-semibold text-textMain">Ресурсы</div>
                <div className="space-y-2">
                  {inventories.map((item, index) => (
                    <div key={item.resource} className="grid grid-cols-[1fr_140px] gap-2">
                      <div className="rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain">
                        {item.resource}
                      </div>
                      <input
                        value={item.amount}
                        onChange={(event) =>
                          setInventories((current) =>
                            current.map((entry, entryIndex) =>
                              entryIndex === index ? { ...entry, amount: Number(event.target.value) || 0 } : entry
                            )
                          )
                        }
                        type="number"
                        step="0.1"
                        className="rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-textMain"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <div className="mb-2 text-sm font-semibold text-textMain">Модули</div>
                <div className="space-y-2">
                  {modules.map((item, index) => (
                    <div key={item.module_key} className="rounded-2xl border border-borderSoft bg-panelSoft px-3 py-3">
                      <div className="text-sm text-textMain">{item.module_key}</div>
                      <div className="mt-2 grid grid-cols-[1fr_1fr] gap-2">
                        <input
                          value={item.level}
                          onChange={(event) =>
                            setModules((current) =>
                              current.map((entry, entryIndex) =>
                                entryIndex === index ? { ...entry, level: Number(event.target.value) || 1 } : entry
                              )
                            )
                          }
                          type="number"
                          min={1}
                          className="rounded-2xl border border-borderSoft bg-bg/60 px-4 py-2 text-sm text-textMain"
                        />
                        <label className="flex items-center gap-2 rounded-2xl border border-borderSoft bg-bg/60 px-4 py-2 text-sm text-textMain">
                          <input
                            checked={item.is_active}
                            onChange={(event) =>
                              setModules((current) =>
                                current.map((entry, entryIndex) =>
                                  entryIndex === index ? { ...entry, is_active: event.target.checked } : entry
                                )
                              )
                            }
                            type="checkbox"
                          />
                          active
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}
