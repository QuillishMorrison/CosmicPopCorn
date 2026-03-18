import { useEffect, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Button, Card, Progress, SectionTitle, Sparkline, StatPill, Tooltip } from '../../components/ui'
import { useActionFeedback } from '../../hooks/useActionFeedback'
import { useLiveDashboard } from '../../hooks/useLiveDashboard'
import { starterGuide } from '../../lib/gameContent'
import { api } from '../../lib/api'
import { describeResource, labelForResource, labelForSpecialization } from '../../lib/i18n'
import { useActionPreviewStore } from '../../store/actionPreviewStore'
import { useLiveDataStore } from '../../store/liveDataStore'
import type { ModuleDefinition } from '../../types/game'

const t = {
  loading: '\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0441\u0442\u0430\u043d\u0446\u0438\u0438...',
  loadError: '\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0441\u0442\u0430\u043d\u0446\u0438\u044e.',
  level: '\u0423\u0440.',
  credits: '\u041a\u0440\u0435\u0434\u0438\u0442\u044b',
  energy: '\u042d\u043d\u0435\u0440\u0433\u0438\u044f',
  flow: '\u041f\u043e\u0442\u043e\u043a',
  insight: '\u0418\u043d\u0441\u0430\u0439\u0442',
  efficiency: '\u042d\u0444\u0444\u0435\u043a\u0442\u0438\u0432\u043d\u043e\u0441\u0442\u044c',
  stability: '\u0421\u0442\u0430\u0431\u0438\u043b\u044c\u043d\u043e\u0441\u0442\u044c',
  reputation: '\u0420\u0435\u043f\u0443\u0442\u0430\u0446\u0438\u044f',
  stationMap: '\u0421\u0445\u0435\u043c\u0430 \u0441\u0442\u0430\u043d\u0446\u0438\u0438',
  stationMapTip:
    '\u0421\u0432\u0435\u0440\u0445\u0443 \u0432\u0430\u0436\u043d\u043e \u0432\u0438\u0434\u0435\u0442\u044c, \u0447\u0442\u043e \u0443\u0436\u0435 \u043f\u043e\u0441\u0442\u0440\u043e\u0435\u043d\u043e, \u0430 \u0447\u0442\u043e \u0435\u0449\u0451 \u043f\u0443\u0441\u0442\u043e.',
  blockers: '\u0423\u0437\u043a\u0438\u0435 \u043c\u0435\u0441\u0442\u0430',
  blockersTip:
    '\u042d\u0442\u043e \u043a\u043e\u0440\u043e\u0442\u043a\u0438\u0439 \u0432\u044b\u0432\u043e\u0434 \u0441\u0438\u043c\u0443\u043b\u044f\u0446\u0438\u0438: \u0447\u0442\u043e \u043f\u0440\u044f\u043c\u043e \u0441\u0435\u0439\u0447\u0430\u0441 \u0442\u043e\u0440\u043c\u043e\u0437\u0438\u0442 \u0441\u0442\u0430\u043d\u0446\u0438\u044e.',
  guide: '\u0427\u0442\u043e \u0434\u0435\u043b\u0430\u0442\u044c \u0441\u0435\u0439\u0447\u0430\u0441',
  buildable: '\u041f\u043e\u0441\u0442\u0440\u043e\u0439\u043a\u0438',
  buildableTip:
    '\u0417\u0434\u0435\u0441\u044c \u0432\u0441\u0435 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0435 \u043c\u043e\u0434\u0443\u043b\u0438 \u0441 \u0446\u0435\u043d\u043e\u0439 \u0438 \u043f\u043e\u043d\u044f\u0442\u043d\u044b\u043c \u0441\u043c\u044b\u0441\u043b\u043e\u043c.',
  market: '\u0420\u044b\u043d\u043e\u043a',
  contracts: '\u041a\u043e\u043d\u0442\u0440\u0430\u043a\u0442\u044b',
  report: '\u041e\u0442\u0447\u0451\u0442',
  resources: '\u0421\u043a\u043b\u0430\u0434',
  build: '\u041f\u043e\u0441\u0442\u0440\u043e\u0438\u0442\u044c',
  upgrade: '\u0423\u043b\u0443\u0447\u0448\u0438\u0442\u044c',
  buy: '\u041a\u0443\u043f\u0438\u0442\u044c',
  sell: '\u041f\u0440\u043e\u0434\u0430\u0442\u044c',
  fulfill: '\u0412\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u044c',
  notBuilt: '\u041d\u0435 \u043f\u043e\u0441\u0442\u0440\u043e\u0435\u043d',
  smooth: '\u0421\u0438\u0441\u0442\u0435\u043c\u0430 \u0438\u0434\u0451\u0442 \u0440\u043e\u0432\u043d\u043e.',
  noReport: '\u041e\u0442\u0447\u0451\u0442 \u043f\u043e\u044f\u0432\u0438\u0442\u0441\u044f \u043f\u043e\u0441\u043b\u0435 \u043f\u0435\u0440\u0432\u043e\u0433\u043e \u0437\u0430\u043c\u0435\u0442\u043d\u043e\u0433\u043e \u0446\u0438\u043a\u043b\u0430.',
  onHand: '\u041d\u0430 \u0441\u043a\u043b\u0430\u0434\u0435',
  new: '\u041d\u043e\u0432\u044b\u0439',
  moduleDetails:
    '\u0420\u043e\u043b\u044c: {role}. {description}',
  insufficientHint:
    '\u0412\u044b\u0431\u0435\u0440\u0438 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435, \u0438 \u0432\u0435\u0440\u0445\u043d\u044f\u044f \u043f\u0430\u043d\u0435\u043b\u044c \u043f\u043e\u043a\u0430\u0436\u0435\u0442, \u0447\u0435\u0433\u043e \u0438\u043c\u0435\u043d\u043d\u043e \u043d\u0435 \u0445\u0432\u0430\u0442\u0430\u0435\u0442.',
  marketIntel: 'Рынок и заказы',
  marketIntelTip: 'Чем выше уровень рыночного терминала, тем больше NPC-заказов видно на экране контрактов.',
  contractsVisible: 'Видно заказов',
  nextUnlock: 'Следующий порог',
  marketStageBase: 'Локальный канал',
  marketStageSector: 'Секторный доступ',
  marketStageExpanded: 'Расширенные лоты',
  marketStageVip: 'Премиум поток',
  actionReady: 'Готовое действие',
  actionMarketTitle: 'Открыть больше заказов',
  actionMarketBuild: 'Построить терминал',
  actionMarketUpgrade: 'Усилить терминал',
  actionEnergyTitle: 'Стабилизировать энергию',
  actionPartsTitle: 'Пополнить детали',
  actionContractTitle: 'Забрать быстрый контракт',
  actionBuyParts: 'Купить детали',
  actionAcceptContract: 'Выполнить контракт'
}

function formatAmount(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function formatMissingCosts(costs: { resource: string; amount: number }[], resources: Record<string, number>) {
  return costs
    .filter((entry) => (resources[entry.resource] ?? 0) < entry.amount)
    .map((entry) => `${labelForResource(entry.resource)} ${Math.ceil(entry.amount - (resources[entry.resource] ?? 0))}`)
    .join(', ')
}

function moduleCostForLevel(definition: ModuleDefinition, nextLevel: number) {
  const multiplier = 1 + (nextLevel - 1) * definition.upgrade_cost_growth
  return Object.entries(definition.base_cost).map(([resource, value]) => ({
    resource,
    amount: Math.round(value * multiplier)
  }))
}

export function DashboardPage() {
  const queryClient = useQueryClient()
  const feedback = useActionFeedback()
  const setPreview = useActionPreviewStore((state) => state.setPreview)
  const clearPreview = useActionPreviewStore((state) => state.clearPreview)
  useLiveDashboard()
  const live = useLiveDataStore((state) => state.snapshot)

  const handleAction = async (action: () => Promise<unknown>, successMessage: string) => {
    try {
      await action()
      feedback.success(successMessage)
      await queryClient.invalidateQueries({ queryKey: ['station'] })
    } catch (error) {
      feedback.error(error)
    }
  }

  const data = live?.station
  const reportItems = live?.reports
  const marketItems = live?.market
  const contractItems = live?.npc_contracts
  const latestReport = reportItems?.[0]
  const topMarket = marketItems ?? []
  const topContracts = contractItems ?? []
  const visibleContracts = live?.npc_contract_visibility ?? 2
  const resources = useMemo(
    () => Object.fromEntries((data?.inventories ?? []).map((item) => [item.resource, item.amount])),
    [data]
  )

  useEffect(() => clearPreview, [clearPreview])

  if (!data) return <div className="text-textMute">{t.loading}</div>

  const moduleCatalog = data.module_catalog ?? []
  const firstSession = data.modules.length <= 3 && (reportItems?.length ?? 0) <= 1
  const marketModule = data.modules.find((module) => module.module_key === 'market_terminal')
  const marketLevel = marketModule?.level ?? 0
  const nextContractUnlock = marketLevel >= 5 ? 8 : marketLevel >= 3 ? 8 : marketLevel >= 1 ? 6 : 4
  const marketStages = [
    { level: 0, title: t.marketStageBase, visible: 2 },
    { level: 1, title: t.marketStageSector, visible: 4 },
    { level: 3, title: t.marketStageExpanded, visible: 6 },
    { level: 5, title: t.marketStageVip, visible: 8 }
  ]
  const energyModule = data.modules.find((module) => module.module_key === 'reactor')
  const actionCards = [
    {
      key: 'market',
      title: t.actionMarketTitle,
      description:
        marketLevel === 0
          ? 'Терминал откроет первые дополнительные заказы и сделает рынок полезным с первой же минуты.'
          : `Сейчас видно ${visibleContracts} NPC-заказа. Следующий порог откроет до ${nextContractUnlock}.`,
      button: marketLevel === 0 ? t.actionMarketBuild : t.actionMarketUpgrade,
      action: () =>
        handleAction(
          () => api.post('/station/upgrade-module', { module_key: 'market_terminal' }),
          marketLevel === 0 ? 'Рыночный терминал построен' : 'Рыночный терминал улучшен'
        )
    },
    {
      key: 'energy',
      title: t.actionEnergyTitle,
      description:
        (resources.energy ?? 0) < 20
          ? 'Реактор даст запас энергии для новых модулей и снимет штрафы эффективности.'
          : 'Энергия держится нормально, но дополнительный реактор даст место под рост.',
      button: energyModule ? t.upgrade : t.build,
      action: () =>
        handleAction(
          () => api.post('/station/upgrade-module', { module_key: 'reactor' }),
          energyModule ? 'Реактор улучшен' : 'Реактор построен'
        )
    },
    {
      key: 'parts',
      title: (topContracts[0] && (resources[topContracts[0].resource] ?? 0) >= topContracts[0].quantity)
        ? t.actionContractTitle
        : t.actionPartsTitle,
      description:
        (topContracts[0] && (resources[topContracts[0].resource] ?? 0) >= topContracts[0].quantity)
          ? `Первый доступный контракт уже можно закрыть за ${topContracts[0].reward_credits} кр.`
          : 'Детали поддерживают ремонт, апгрейды и ранние контракты. Это самый безопасный быстрый докуп.',
      button:
        (topContracts[0] && (resources[topContracts[0].resource] ?? 0) >= topContracts[0].quantity)
          ? t.actionAcceptContract
          : t.actionBuyParts,
      action: () =>
        (topContracts[0] && (resources[topContracts[0].resource] ?? 0) >= topContracts[0].quantity)
          ? handleAction(
              () => api.post(`/contracts/${topContracts[0].id}/accept`),
              `Контракт выполнен: ${topContracts[0].title}`
            )
          : handleAction(() => api.post('/market/buy', { resource: 'parts', quantity: 20 }), 'Детали куплены')
    }
  ]

  return (
    <div className="space-y-4">
      <Card>
        <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="min-w-0">
            <div className="text-[10px] uppercase tracking-[0.28em] text-accentWarm">Sector Relay</div>
            <h1 className="mt-2 text-2xl font-semibold text-textMain">{data.name}</h1>
            <p className="mt-2 text-sm leading-relaxed text-textMute">
              {labelForSpecialization(data.specialization)} {'\u2022'} {t.level} {data.level}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <StatPill label={t.credits} value={formatAmount(resources.credits ?? 0)} />
            <StatPill label={t.energy} value={formatAmount(resources.energy ?? 0)} />
            <StatPill label={t.flow} value={data.throughput.toFixed(1)} />
            <StatPill label={t.insight} value={formatAmount(resources.insight ?? 0)} />
          </div>
        </div>
      </Card>

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <SectionTitle
            title={
              <Tooltip label={t.stationMapTip}>
                <span>{t.stationMap}</span>
              </Tooltip>
            }
          />
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {moduleCatalog.map((item) => {
              const built = data.modules.find((module) => module.module_key === item.key)
              return (
                <div
                  key={item.key}
                  className={`rounded-2xl border p-3 ${
                    built ? 'border-accent/35 bg-accent/8' : 'border-borderSoft bg-panelSoft'
                  }`}
                >
                    <div className="text-[10px] uppercase tracking-[0.2em] text-textMute">{item.category}</div>
                    <div className="mt-1 text-sm font-semibold text-textMain">
                      <Tooltip
                        label={t.moduleDetails
                        .replace('{role}', item.category)
                        .replace('{description}', item.description)}
                      >
                        <span>{item.name}</span>
                    </Tooltip>
                  </div>
                  <div className="mt-2 text-xs text-textMute">
                    {built ? `${t.level} ${built.level}` : t.notBuilt}
                  </div>
                </div>
              )
            })}
          </div>
        </Card>

        <Card>
          <SectionTitle
            title={
              <Tooltip label={t.blockersTip}>
                <span>{t.blockers}</span>
              </Tooltip>
            }
          />
          <div className="space-y-4">
            <div>
              <div className="mb-2 flex items-center justify-between text-sm text-textMute">
                <span>{t.efficiency}</span>
                <span>{Math.round(data.efficiency * 100)}%</span>
              </div>
              <Progress value={data.efficiency * 100} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-borderSoft p-3">
                <div className="text-xs text-textMute">{t.stability}</div>
                <div className="mt-1 text-lg font-semibold">{data.stability.toFixed(0)}</div>
              </div>
              <div className="rounded-xl border border-borderSoft p-3">
                <div className="text-xs text-textMute">{t.reputation}</div>
                <div className="mt-1 text-lg font-semibold">{data.reputation.toFixed(1)}</div>
              </div>
            </div>
            <div className="space-y-2">
              {data.bottlenecks.length ? (
                data.bottlenecks.map((issue) => (
                  <div key={issue} className="rounded-xl border border-borderSoft px-3 py-2 text-sm">
                    {issue}
                  </div>
                ))
              ) : (
                <div className="rounded-xl border border-accent/30 bg-accent/10 px-3 py-2 text-sm">
                  {t.smooth}
                </div>
              )}
            </div>
          </div>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1fr_1fr]">
        <Card>
          <SectionTitle title={t.guide} subtitle={firstSession ? starterGuide[0] : undefined} />
          <div className="grid gap-3">
            {actionCards.map((item) => (
              <div key={item.key} className="rounded-2xl border border-borderSoft bg-panelSoft p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-accentWarm">{t.actionReady}</div>
                    <div className="mt-1 text-base font-semibold text-textMain">{item.title}</div>
                    <div className="mt-2 text-sm leading-relaxed text-textMute">{item.description}</div>
                  </div>
                  <Button className="shrink-0" onClick={item.action}>
                    {item.button}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <SectionTitle
            title={
              <Tooltip label={t.marketIntelTip}>
                <span>{t.marketIntel}</span>
              </Tooltip>
            }
          />
          <div className="rounded-2xl border border-borderSoft bg-panelSoft p-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-borderSoft px-3 py-3">
                <div className="text-xs text-textMute">{t.level}</div>
                <div className="mt-1 text-lg font-semibold">{marketLevel}</div>
              </div>
              <div className="rounded-xl border border-borderSoft px-3 py-3">
                <div className="text-xs text-textMute">{t.contractsVisible}</div>
                <div className="mt-1 text-lg font-semibold">{visibleContracts}</div>
              </div>
            </div>
            <div className="mt-4 space-y-2">
              {marketStages.map((stage) => {
                const active = marketLevel >= stage.level
                const currentStage =
                  stage.level <= marketLevel &&
                  (!marketStages.find((candidate) => candidate.level > stage.level && candidate.level <= marketLevel))
                return (
                  <div
                    key={stage.level}
                    className={`rounded-xl border px-3 py-3 ${
                      active ? 'border-accent/40 bg-accent/10' : 'border-borderSoft bg-bg/40'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="text-sm font-medium text-textMain">{stage.title}</div>
                        <div className="text-xs text-textMute">{stage.visible} NPC-заказов</div>
                      </div>
                      <div className="text-xs text-textMute">
                        {stage.level === marketLevel || currentStage ? `Ур. ${stage.level}` : `Порог ${stage.level}`}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
            <div className="mt-4 rounded-xl border border-borderSoft px-3 py-3 text-sm text-textMute">
              {marketLevel >= 5
                ? 'Терминал раскрыт полностью: на экране контрактов доступен максимум заказов.'
                : `${t.nextUnlock}: ур. ${marketStages.find((stage) => stage.level > marketLevel)?.level ?? 5}`}
            </div>
          </div>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1fr_1fr]">
        <Card>
          <SectionTitle title={t.report} />
          {firstSession ? (
            <div className="rounded-xl border border-borderSoft bg-panelSoft px-4 py-4 text-sm text-textMute">
              {t.noReport}
            </div>
          ) : (
            <div className="rounded-xl border border-borderSoft bg-panelSoft p-4">
              <div className="text-base font-semibold">{String((latestReport?.summary.headline as string) ?? '')}</div>
              <div className="mt-2 text-sm text-textMute">
                {'\u041f\u0440\u0438\u0431\u044b\u043b\u044c'}: {String((latestReport?.summary.profit as number | undefined)?.toFixed?.(0) ?? 0)}
              </div>
            </div>
          )}
        </Card>
        <Card>
          <SectionTitle title={t.guide} subtitle={firstSession ? starterGuide[0] : undefined} />
          <div className="space-y-3">
            {(firstSession ? starterGuide : data.recommended_actions).map((item) => (
              <div key={item} className="rounded-xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm">
                {item}
              </div>
            ))}
          </div>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <SectionTitle
            title={
              <Tooltip label={t.buildableTip}>
                <span>{t.buildable}</span>
              </Tooltip>
            }
          />
          <div className="grid gap-3 md:grid-cols-2">
            {moduleCatalog.map((item) => {
              const current = data.modules.find((module) => module.module_key === item.key)
              const nextLevel = current ? current.level + 1 : 1
              const cost = moduleCostForLevel(item, nextLevel)
              const cannotAfford = cost.some((entry) => (resources[entry.resource] ?? 0) < entry.amount)
              return (
                <div
                  key={item.key}
                  className="rounded-2xl border border-borderSoft bg-panelSoft p-4"
                  onMouseEnter={() =>
                    setPreview({
                      title: `${current ? t.upgrade : t.build}: ${item.name}`,
                      description: item.description,
                      costs: cost
                    })
                  }
                  onFocus={() =>
                    setPreview({
                      title: `${current ? t.upgrade : t.build}: ${item.name}`,
                      description: item.description,
                      costs: cost
                    })
                  }
                  onTouchStart={() =>
                    setPreview({
                      title: `${current ? t.upgrade : t.build}: ${item.name}`,
                      description: item.description,
                      costs: cost
                    })
                  }
                  onMouseLeave={clearPreview}
                  onBlur={clearPreview}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-[10px] uppercase tracking-[0.2em] text-textMute">{item.category}</div>
                      <div className="mt-1 text-base font-semibold">
                        <Tooltip
                          label={t.moduleDetails
                            .replace('{role}', item.category)
                            .replace('{description}', item.description)}
                        >
                          <span>{item.name}</span>
                        </Tooltip>
                      </div>
                      <p className="mt-2 text-sm leading-relaxed text-textMute">{item.description}</p>
                    </div>
                    <div className="rounded-full border border-borderSoft px-2 py-1 text-xs text-textMute">
                      {current ? `${t.level} ${current.level}` : t.new}
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {cost.map((entry) => (
                      <Tooltip key={entry.resource} label={describeResource(entry.resource)}>
                        <span className="rounded-full border border-borderSoft px-2 py-1 text-xs text-textMute">
                          {labelForResource(entry.resource)} {entry.amount}
                        </span>
                      </Tooltip>
                    ))}
                  </div>
                  <Button
                    className="mt-4 w-full"
                    title={cannotAfford ? t.insufficientHint : undefined}
                    onClick={() =>
                      cannotAfford
                        ? feedback.error(`Не хватает: ${formatMissingCosts(cost, resources)}`)
                        : handleAction(
                            () => api.post('/station/upgrade-module', { module_key: item.key }),
                            current
                              ? `${item.name} ${'\u0443\u043b\u0443\u0447\u0448\u0435\u043d'}`
                              : `${item.name} ${'\u043f\u043e\u0441\u0442\u0440\u043e\u0435\u043d'}`
                          )
                    }
                  >
                    {current ? t.upgrade : t.build}
                  </Button>
                </div>
              )
            })}
          </div>
        </Card>

        <div className="space-y-4">
          <Card>
            <SectionTitle title={t.market} />
            <div className="space-y-3">
              {topMarket.map((row) => (
                <div key={row.resource} className="rounded-xl border border-borderSoft bg-panelSoft p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">
                        <Tooltip label={describeResource(row.resource)}>
                          <span>{labelForResource(row.resource)}</span>
                        </Tooltip>
                      </div>
                      <div className="text-xs text-textMute">
                        {t.onHand}: {formatAmount(resources[row.resource] ?? 0)}
                      </div>
                    </div>
                    <div className={`text-sm ${row.trend >= 0 ? 'text-accent' : 'text-danger'}`}>
                      {row.price.toFixed(1)} {'\u043a\u0440.'}
                    </div>
                  </div>
                  <Sparkline values={row.history} />
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    <Button
                      onClick={() =>
                        handleAction(
                          () => api.post('/market/buy', { resource: row.resource, quantity: 10 }),
                          `${t.buy}: ${labelForResource(row.resource)}`
                        )
                      }
                    >
                      {t.buy}
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() =>
                        handleAction(
                          () => api.post('/market/sell', { resource: row.resource, quantity: 10 }),
                          `${t.sell}: ${labelForResource(row.resource)}`
                        )
                      }
                    >
                      {t.sell}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <SectionTitle title={t.contracts} />
            <div className="space-y-3">
              {topContracts.map((contract) => (
                <div key={contract.id} className="rounded-xl border border-borderSoft bg-panelSoft p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="font-medium">{contract.title}</div>
                      <div className="mt-1 text-xs text-textMute">
                        {contract.quantity} {labelForResource(contract.resource)}
                      </div>
                    </div>
                    <div className="text-sm text-accent">{contract.reward_credits} {'\u043a\u0440.'}</div>
                  </div>
                  <Button
                    className="mt-3 w-full"
                    onClick={() =>
                      handleAction(
                        () => api.post(`/contracts/${contract.id}/accept`),
                        `${t.fulfill}: ${contract.title}`
                      )
                    }
                  >
                    {t.fulfill}
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </section>

      <Card className="lg:hidden">
        <SectionTitle title={t.resources} />
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-8">
          {data.inventories.map((item) => (
            <div key={item.resource} className="rounded-xl border border-borderSoft bg-panelSoft px-3 py-3">
              <div className="text-[10px] uppercase tracking-[0.2em] text-textMute">
                <Tooltip label={describeResource(item.resource)}>
                  <span>{labelForResource(item.resource)}</span>
                </Tooltip>
              </div>
              <div className="mt-1 text-lg font-semibold">{formatAmount(item.amount)}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
