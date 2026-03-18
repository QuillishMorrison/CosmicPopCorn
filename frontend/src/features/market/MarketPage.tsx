import { useEffect, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Button, Card, SectionTitle, Sparkline, StatPill, Tooltip } from '../../components/ui'
import { useActionFeedback } from '../../hooks/useActionFeedback'
import { useMarket, useStation } from '../../hooks/useGameData'
import { api } from '../../lib/api'
import { describeResource, labelForResource } from '../../lib/i18n'
import { useActionPreviewStore } from '../../store/actionPreviewStore'

const t = {
  loading: '\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0440\u044b\u043d\u043a\u0430...',
  title: '\u0420\u044b\u043d\u043e\u043a \u0441\u0435\u043a\u0442\u043e\u0440\u0430',
  subtitle:
    '\u041f\u043e\u043a\u0443\u043f\u0430\u0439 \u0434\u0435\u0444\u0438\u0446\u0438\u0442\u043d\u043e\u0435, \u043f\u0440\u043e\u0434\u0430\u0432\u0430\u0439 \u0438\u0437\u0431\u044b\u0442\u043a\u0438',
  credits: '\u041a\u0440\u0435\u0434\u0438\u0442\u044b',
  fuel: '\u0422\u043e\u043f\u043b\u0438\u0432\u043e',
  parts: '\u0414\u0435\u0442\u0430\u043b\u0438',
  data: '\u0414\u0430\u043d\u043d\u044b\u0435',
  onHand: '\u041d\u0430 \u0441\u043a\u043b\u0430\u0434\u0435',
  buy: '\u041a\u0443\u043f\u0438\u0442\u044c',
  sell: '\u041f\u0440\u043e\u0434\u0430\u0442\u044c',
  marketTip:
    '\u0426\u0435\u043d\u0430 \u043f\u043b\u0430\u0432\u0430\u0435\u0442 \u043e\u0442 \u0441\u0434\u0435\u043b\u043e\u043a \u0438 \u0441\u043e\u0431\u044b\u0442\u0438\u0439 \u0441\u0435\u043a\u0442\u043e\u0440\u0430. \u0414\u0435\u0440\u0436\u0438 \u0434\u0435\u0444\u0438\u0446\u0438\u0442 \u043f\u043e\u0434 \u043a\u043e\u043d\u0442\u0440\u043e\u043b\u0435\u043c, \u0430 \u0438\u0437\u043b\u0438\u0448\u043a\u0438 \u0441\u0431\u0440\u0430\u0441\u044b\u0432\u0430\u0439 \u043d\u0430 \u043f\u0438\u043a\u0435.',
  priceNow: '\u0426\u0435\u043d\u0430 \u0441\u0435\u0439\u0447\u0430\u0441',
  tradeHint:
    '\u0412\u044b\u0431\u0435\u0440\u0438 \u043a\u043d\u043e\u043f\u043a\u0443 \u043f\u043e\u043a\u0443\u043f\u043a\u0438 \u0438\u043b\u0438 \u043f\u0440\u043e\u0434\u0430\u0436\u0438, \u0447\u0442\u043e\u0431\u044b \u0432\u0435\u0440\u0445\u043d\u044f\u044f \u043f\u0430\u043d\u0435\u043b\u044c \u043f\u043e\u043a\u0430\u0437\u0430\u043b\u0430 \u0437\u0430\u0442\u0440\u0430\u0442\u044b \u0438 \u0434\u0435\u0444\u0438\u0446\u0438\u0442.'
}

export function MarketPage() {
  const queryClient = useQueryClient()
  const feedback = useActionFeedback()
  const setPreview = useActionPreviewStore((state) => state.setPreview)
  const clearPreview = useActionPreviewStore((state) => state.clearPreview)
  const market = useMarket({ refetchInterval: 3000 })
  const station = useStation({ refetchInterval: 1000 })

  const holdings = useMemo(
    () => Object.fromEntries((station.data?.inventories ?? []).map((item) => [item.resource, item.amount])),
    [station.data]
  )

  useEffect(() => clearPreview, [clearPreview])

  const handleTrade = async (resource: string, side: 'buy' | 'sell', quantity: number) => {
    try {
      await api.post(`/market/${side}`, { resource, quantity })
      feedback.success(
        `${side === 'buy' ? '\u041f\u043e\u043a\u0443\u043f\u043a\u0430' : '\u041f\u0440\u043e\u0434\u0430\u0436\u0430'}: ${labelForResource(resource)} x${quantity}`
      )
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['market'] }),
        queryClient.invalidateQueries({ queryKey: ['station'] })
      ])
    } catch (error) {
      feedback.error(error)
    }
  }

  if (!market.data || !station.data) return <div className="text-textMute">{t.loading}</div>

  return (
    <div className="space-y-4">
      <Card>
        <SectionTitle
          title={
            <Tooltip label={t.marketTip}>
              <span>{t.title}</span>
            </Tooltip>
          }
          subtitle={t.subtitle}
        />
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <StatPill label={t.credits} value={String(Math.round(holdings.credits ?? 0))} />
          <StatPill label={t.fuel} value={String(Math.round(holdings.fuel ?? 0))} />
          <StatPill label={t.parts} value={String(Math.round(holdings.parts ?? 0))} />
          <StatPill label={t.data} value={String(Math.round(holdings.data ?? 0))} />
        </div>
      </Card>

      <div className="grid gap-3">
        {market.data.map((row) => (
          <Card key={row.resource} className="bg-panelSoft">
            {(() => {
              const buyFiveCost = row.price * 5
              const buyTwentyCost = row.price * 20
              const sellFiveBlocked = (holdings[row.resource] ?? 0) < 5
              const sellTwentyBlocked = (holdings[row.resource] ?? 0) < 20
              const buyFiveBlocked = (holdings.credits ?? 0) < buyFiveCost
              const buyTwentyBlocked = (holdings.credits ?? 0) < buyTwentyCost
              return (
            <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
              <div>
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-lg font-semibold">
                      <Tooltip label={describeResource(row.resource)}>
                        <span>{labelForResource(row.resource)}</span>
                      </Tooltip>
                    </div>
                    <div className="text-sm text-textMute">
                      {t.onHand}: {Math.round(holdings[row.resource] ?? 0)}
                    </div>
                  </div>
                  <div className={`text-right text-sm ${row.trend >= 0 ? 'text-accent' : 'text-danger'}`}>
                    <div>{row.price.toFixed(2)} {'\u043a\u0440.'}</div>
                    <div className="text-[11px] text-textMute">{t.priceNow}</div>
                  </div>
                </div>
                <div className="mt-2">
                  <Sparkline values={row.history} />
                </div>
                <div className="mt-2 text-xs text-textMute">{t.tradeHint}</div>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <span
                  onMouseEnter={() => setPreview({ title: `${t.buy} 5: ${labelForResource(row.resource)}`, description: describeResource(row.resource), costs: [{ resource: 'credits', amount: buyFiveCost }] })}
                  onFocus={() => setPreview({ title: `${t.buy} 5: ${labelForResource(row.resource)}`, description: describeResource(row.resource), costs: [{ resource: 'credits', amount: buyFiveCost }] })}
                  onTouchStart={() => setPreview({ title: `${t.buy} 5: ${labelForResource(row.resource)}`, description: describeResource(row.resource), costs: [{ resource: 'credits', amount: buyFiveCost }] })}
                  onMouseLeave={clearPreview}
                  onBlur={clearPreview}
                >
                  <Button
                    onClick={() =>
                      buyFiveBlocked
                        ? feedback.error(`Не хватает: Кредиты ${Math.ceil(buyFiveCost - (holdings.credits ?? 0))}`)
                        : void handleTrade(row.resource, 'buy', 5)
                    }
                  >
                    {`${t.buy} 5`}
                  </Button>
                </span>
                <span
                  onMouseEnter={() => setPreview({ title: `${t.buy} 20: ${labelForResource(row.resource)}`, description: describeResource(row.resource), costs: [{ resource: 'credits', amount: buyTwentyCost }] })}
                  onFocus={() => setPreview({ title: `${t.buy} 20: ${labelForResource(row.resource)}`, description: describeResource(row.resource), costs: [{ resource: 'credits', amount: buyTwentyCost }] })}
                  onTouchStart={() => setPreview({ title: `${t.buy} 20: ${labelForResource(row.resource)}`, description: describeResource(row.resource), costs: [{ resource: 'credits', amount: buyTwentyCost }] })}
                  onMouseLeave={clearPreview}
                  onBlur={clearPreview}
                >
                  <Button
                    variant="ghost"
                    onClick={() =>
                      buyTwentyBlocked
                        ? feedback.error(`Не хватает: Кредиты ${Math.ceil(buyTwentyCost - (holdings.credits ?? 0))}`)
                        : void handleTrade(row.resource, 'buy', 20)
                    }
                  >
                    {`${t.buy} 20`}
                  </Button>
                </span>
                <span
                  onMouseEnter={() => setPreview({ title: `${t.sell} 5: ${labelForResource(row.resource)}`, description: describeResource(row.resource), costs: [{ resource: row.resource, amount: 5 }] })}
                  onFocus={() => setPreview({ title: `${t.sell} 5: ${labelForResource(row.resource)}`, description: describeResource(row.resource), costs: [{ resource: row.resource, amount: 5 }] })}
                  onTouchStart={() => setPreview({ title: `${t.sell} 5: ${labelForResource(row.resource)}`, description: describeResource(row.resource), costs: [{ resource: row.resource, amount: 5 }] })}
                  onMouseLeave={clearPreview}
                  onBlur={clearPreview}
                >
                  <Button
                    variant="ghost"
                    onClick={() =>
                      sellFiveBlocked
                        ? feedback.error(`Не хватает: ${labelForResource(row.resource)} ${Math.ceil(5 - (holdings[row.resource] ?? 0))}`)
                        : void handleTrade(row.resource, 'sell', 5)
                    }
                  >
                    {`${t.sell} 5`}
                  </Button>
                </span>
                <span
                  onMouseEnter={() => setPreview({ title: `${t.sell} 20: ${labelForResource(row.resource)}`, description: describeResource(row.resource), costs: [{ resource: row.resource, amount: 20 }] })}
                  onFocus={() => setPreview({ title: `${t.sell} 20: ${labelForResource(row.resource)}`, description: describeResource(row.resource), costs: [{ resource: row.resource, amount: 20 }] })}
                  onTouchStart={() => setPreview({ title: `${t.sell} 20: ${labelForResource(row.resource)}`, description: describeResource(row.resource), costs: [{ resource: row.resource, amount: 20 }] })}
                  onMouseLeave={clearPreview}
                  onBlur={clearPreview}
                >
                  <Button
                    variant="ghost"
                    onClick={() =>
                      sellTwentyBlocked
                        ? feedback.error(`Не хватает: ${labelForResource(row.resource)} ${Math.ceil(20 - (holdings[row.resource] ?? 0))}`)
                        : void handleTrade(row.resource, 'sell', 20)
                    }
                  >
                    {`${t.sell} 20`}
                  </Button>
                </span>
              </div>
            </div>
              )
            })()}
          </Card>
        ))}
      </div>
    </div>
  )
}
