import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Button, Card, SectionTitle, Tooltip } from '../../components/ui'
import { useActionFeedback } from '../../hooks/useActionFeedback'
import { useNpcContracts, usePlayerContracts, useStation } from '../../hooks/useGameData'
import { api } from '../../lib/api'
import { contractSourceLabels, describeResource, labelForResource } from '../../lib/i18n'
import { useActionPreviewStore } from '../../store/actionPreviewStore'

const contractTypes = [
  {
    value: 'delivery',
    label: 'Доставка',
    description: 'Разовый запрос на конкретный объём ресурса. Подходит для срочной нехватки.'
  },
  {
    value: 'supply',
    label: 'Снабжение',
    description: 'Поставка под стабильную логистику. Чаще используется для топлива, деталей и сплава.'
  },
  {
    value: 'data',
    label: 'Данные',
    description: 'Передача аналитики и цифрового потока. Лучше всего подходит для дата-станций.'
  },
  {
    value: 'repair',
    label: 'Ремонт',
    description: 'Сервисный заказ для станций, которые работают через детали и ремонтную мощность.'
  },
  {
    value: 'processing',
    label: 'Переработка',
    description: 'Контракт на обработку и сортировку материалов. Полезен для throughput-специализаций.'
  }
]

const resourceOptions = ['fuel', 'parts', 'data', 'alloy', 'crew']

const t = {
  title: 'Контракты',
  subtitle: 'Здесь склад и торговля превращаются в деньги',
  npc: 'NPC-заказы',
  players: 'Игроки',
  needs: 'требуется',
  rep: 'репутация',
  accept: 'Выполнить контракт',
  cancel: 'Отменить оффер',
  mine: 'Мой оффер',
  mineHint: 'Свой контракт нельзя выполнять самому',
  closed: 'Контракт уже закрыт',
  emptyNpc: 'Пока пусто. Через пару тиков появятся новые заказы.',
  emptyPlayer: 'Офферов игроков пока нет. После размещения они появятся здесь.',
  offerTitle: 'Создать оффер',
  offerSub: 'Попроси другого игрока привезти нужный ресурс',
  placed: 'Оффер размещён. Он уже появился во вкладке игроков.',
  cancelled: 'Оффер отменён',
  place: 'Разместить оффер',
  titleTip:
    'На NPC-контрактах ты сдаёшь свой ресурс системе. Во вкладке игроков публикуются асинхронные заказы между станциями.',
  myOfferHint: 'После создания экран автоматически переключится на вкладку игроков.',
  contractType: 'Тип контракта',
  contractTypeTip:
    'Тип контракта это короткая пометка назначения заказа. Она помогает быстро понять, зачем нужен ресурс.',
  resource: 'Ресурс',
  quantity: 'Количество',
  reward: 'Награда',
  exampleTitle: 'Например: срочно нужны детали',
  onHand: 'На складе',
  lacking: 'Не хватает',
  resourceTip: 'Нажми на название ресурса, чтобы увидеть его короткое описание.'
}

export function ContractsPage() {
  const queryClient = useQueryClient()
  const feedback = useActionFeedback()
  const station = useStation({ refetchInterval: 1000 })
  const npc = useNpcContracts({ refetchInterval: 3000 })
  const player = usePlayerContracts({ refetchInterval: 3000 })
  const setPreview = useActionPreviewStore((state) => state.setPreview)
  const clearPreview = useActionPreviewStore((state) => state.clearPreview)
  const [tab, setTab] = useState<'npc' | 'player'>('npc')
  const [offerResource, setOfferResource] = useState('fuel')
  const [offerQuantity, setOfferQuantity] = useState(1)
  const [offerType, setOfferType] = useState('delivery')

  const holdings = useMemo(
    () => Object.fromEntries((station.data?.inventories ?? []).map((item) => [item.resource, item.amount])),
    [station.data]
  )

  useEffect(() => clearPreview, [clearPreview])

  const selectedContractType = contractTypes.find((item) => item.value === offerType) ?? contractTypes[0]
  const contracts = tab === 'npc' ? npc.data ?? [] : player.data ?? []
  const myStationId = station.data?.id ?? null
  const offerOnHand = Math.floor(holdings[offerResource] ?? 0)
  const offerLacking = Math.max(0, offerQuantity - offerOnHand)

  async function createContract(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const formElement = event.currentTarget
    const form = new FormData(formElement)

    if (offerLacking > 0) {
      feedback.error(`Не хватает: ${labelForResource(offerResource)} ${offerLacking}`)
      setPreview({
        title: t.place,
        description: selectedContractType.description,
        costs: [{ resource: offerResource, amount: offerQuantity }]
      })
      return
    }

    try {
      await api.post('/contracts/create', {
        title: form.get('title'),
        contract_type: form.get('contract_type'),
        resource: form.get('resource'),
        quantity: Number(form.get('quantity')),
        reward_credits: Number(form.get('reward_credits'))
      })
      setTab('player')
      feedback.success(t.placed)
      setOfferQuantity(1)
      setOfferResource('fuel')
      setOfferType('delivery')
      formElement.reset()
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['contracts', 'player'] }),
        queryClient.invalidateQueries({ queryKey: ['contracts', 'npc'] }),
        queryClient.invalidateQueries({ queryKey: ['station'] })
      ])
    } catch (error) {
      feedback.error(error)
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
      <Card>
        <SectionTitle
          title={
            <Tooltip label={t.titleTip}>
              <span>{t.title}</span>
            </Tooltip>
          }
          subtitle={t.subtitle}
        />
        <div className="mb-4 grid grid-cols-2 gap-2 rounded-xl bg-panelSoft p-1">
          <button
            type="button"
            className={`rounded-lg px-3 py-2 text-sm ${tab === 'npc' ? 'bg-accent text-slate-950' : 'text-textMute'}`}
            onClick={() => setTab('npc')}
          >
            {t.npc}
          </button>
          <button
            type="button"
            className={`rounded-lg px-3 py-2 text-sm ${tab === 'player' ? 'bg-accent text-slate-950' : 'text-textMute'}`}
            onClick={() => setTab('player')}
          >
            {t.players}
          </button>
        </div>

        <div className="space-y-3">
          {contracts.map((contract) => {
            const isMine = !!myStationId && contract.issuer_station_id === myStationId
            const isOpen = contract.status === 'open'
            const onHand = Math.floor(holdings[contract.resource] ?? 0)
            const lacking = Math.max(0, contract.quantity - onHand)
            const previewPayload = {
              title: `Контракт: ${contract.title}`,
              description: describeResource(contract.resource),
              costs: [{ resource: contract.resource, amount: contract.quantity }]
            }

            return (
              <div key={contract.id} className="rounded-2xl border border-borderSoft bg-panelSoft p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="font-semibold">{contract.title}</div>
                      {isMine ? (
                        <span className="rounded-full border border-accent/30 bg-accent/10 px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-accent">
                          {t.mine}
                        </span>
                      ) : null}
                    </div>
                    <div className="mt-1 text-xs text-textMute">
                      {contractSourceLabels[contract.source] ?? contract.source} • {t.needs} {contract.quantity}{' '}
                      <Tooltip label={describeResource(contract.resource)}>
                        <span>{labelForResource(contract.resource)}</span>
                      </Tooltip>
                    </div>
                    <div className="mt-2 text-xs text-textMute">
                      {t.onHand}: {onHand}
                      {lacking > 0 ? ` • ${t.lacking}: ${lacking}` : ''}
                    </div>
                    {isMine ? <div className="mt-2 text-xs text-textMute">{t.mineHint}</div> : null}
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-accent">{contract.reward_credits} кр.</div>
                    <div className="text-xs text-textMute">
                      {t.rep} +{contract.reward_reputation}
                    </div>
                  </div>
                </div>

                {isMine ? (
                  <Button
                    className="mt-4 w-full"
                    variant="ghost"
                    disabled={!isOpen}
                    onClick={async () => {
                      try {
                        await api.post(`/contracts/${contract.id}/cancel`)
                        feedback.success(t.cancelled)
                        await Promise.all([
                          queryClient.invalidateQueries({ queryKey: ['contracts', 'player'] }),
                          queryClient.invalidateQueries({ queryKey: ['station'] })
                        ])
                      } catch (error) {
                        feedback.error(error)
                      }
                    }}
                  >
                    {isOpen ? t.cancel : t.closed}
                  </Button>
                ) : (
                  <span
                    className="block"
                    onMouseEnter={() => setPreview(previewPayload)}
                    onFocus={() => setPreview(previewPayload)}
                    onTouchStart={() => setPreview(previewPayload)}
                    onMouseLeave={clearPreview}
                    onBlur={clearPreview}
                  >
                    <Button
                      className="mt-4 w-full"
                      onClick={async () => {
                        if (!isOpen) {
                          feedback.error(t.closed)
                          return
                        }
                        if (lacking > 0) {
                          setPreview(previewPayload)
                          feedback.error(`Не хватает: ${labelForResource(contract.resource)} ${lacking}`)
                          return
                        }
                        try {
                          await api.post(`/contracts/${contract.id}/accept`)
                          feedback.success(`Контракт «${contract.title}» выполнен`)
                          await Promise.all([
                            queryClient.invalidateQueries({ queryKey: ['contracts', 'player'] }),
                            queryClient.invalidateQueries({ queryKey: ['contracts', 'npc'] }),
                            queryClient.invalidateQueries({ queryKey: ['station'] })
                          ])
                        } catch (error) {
                          feedback.error(error)
                        }
                      }}
                    >
                      {isOpen ? t.accept : t.closed}
                    </Button>
                  </span>
                )}
              </div>
            )
          })}

          {!contracts.length ? (
            <div className="rounded-2xl border border-borderSoft bg-panelSoft p-4 text-sm text-textMute">
              {tab === 'npc' ? t.emptyNpc : t.emptyPlayer}
            </div>
          ) : null}
        </div>
      </Card>

      <Card>
        <SectionTitle title={t.offerTitle} subtitle={t.offerSub} />
        <form className="space-y-3" onSubmit={createContract}>
          <div className="text-xs text-textMute">{t.myOfferHint}</div>
          <input
            name="title"
            placeholder={t.exampleTitle}
            className="w-full rounded-xl border border-borderSoft bg-bg px-4 py-3"
          />

          <label className="block text-xs text-textMute">
            <Tooltip label={t.contractTypeTip}>
              <span>{t.contractType}</span>
            </Tooltip>
            <select
              name="contract_type"
              value={offerType}
              onChange={(event) => setOfferType(event.target.value)}
              className="mt-1 w-full rounded-xl border border-borderSoft bg-bg px-4 py-3 text-textMain"
            >
              {contractTypes.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <div className="text-xs text-textMute">{selectedContractType.description}</div>

          <label className="block text-xs text-textMute">
            {t.resource}
            <select
              name="resource"
              value={offerResource}
              onChange={(event) => setOfferResource(event.target.value)}
              className="mt-1 w-full rounded-xl border border-borderSoft bg-bg px-4 py-3 text-textMain"
            >
              {resourceOptions.map((resource) => (
                <option key={resource} value={resource}>
                  {labelForResource(resource)}
                </option>
              ))}
            </select>
          </label>
          <div className="text-xs text-textMute">
            <Tooltip label={describeResource(offerResource)}>
              <span>{t.resourceTip}</span>
            </Tooltip>
          </div>

          <input
            name="quantity"
            type="number"
            min="1"
            step="1"
            value={offerQuantity}
            onChange={(event) => setOfferQuantity(Math.max(1, Number(event.target.value) || 1))}
            placeholder={t.quantity}
            className="w-full rounded-xl border border-borderSoft bg-bg px-4 py-3"
          />
          <div className="text-xs text-textMute">
            {t.onHand}: {offerOnHand}
            {offerLacking > 0 ? ` • ${t.lacking}: ${offerLacking}` : ''}
          </div>

          <input
            name="reward_credits"
            type="number"
            min="1"
            step="1"
            placeholder={t.reward}
            className="w-full rounded-xl border border-borderSoft bg-bg px-4 py-3"
          />

          <span
            className="block"
            onMouseEnter={() =>
              setPreview({
                title: t.place,
                description: selectedContractType.description,
                costs: [{ resource: offerResource, amount: offerQuantity }]
              })
            }
            onFocus={() =>
              setPreview({
                title: t.place,
                description: selectedContractType.description,
                costs: [{ resource: offerResource, amount: offerQuantity }]
              })
            }
            onTouchStart={() =>
              setPreview({
                title: t.place,
                description: selectedContractType.description,
                costs: [{ resource: offerResource, amount: offerQuantity }]
              })
            }
            onMouseLeave={clearPreview}
            onBlur={clearPreview}
          >
            <Button type="submit" className="w-full">
              {t.place}
            </Button>
          </span>
        </form>
      </Card>
    </div>
  )
}
