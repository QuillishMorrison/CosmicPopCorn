import { useQueryClient } from '@tanstack/react-query'
import { Button, Card, SectionTitle, Tooltip } from '../../components/ui'
import { useNotifications, useSector } from '../../hooks/useGameData'
import { useActionFeedback } from '../../hooks/useActionFeedback'
import { api } from '../../lib/api'
import { labelForSpecialization } from '../../lib/i18n'

const t = {
  loading: '\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0441\u0435\u043a\u0442\u043e\u0440\u0430...',
  market: '\u0420\u044b\u043d\u043e\u043a',
  level: '\u0423\u0440.',
  events: '\u0421\u043e\u0431\u044b\u0442\u0438\u044f',
  eventsSub: '\u041c\u044f\u0433\u043a\u0438\u0435 \u043c\u0438\u0440\u043e\u0432\u044b\u0435 \u043c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u044b',
  notifications: '\u0423\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u044f',
  notificationsSub:
    '\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0435 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f \u0441\u0442\u0430\u043d\u0446\u0438\u0438 \u0438 \u0441\u0435\u043a\u0442\u043e\u0440\u0430',
  markRead: '\u041e\u0442\u043c\u0435\u0442\u0438\u0442\u044c \u043f\u0440\u043e\u0447\u0438\u0442\u0430\u043d\u043d\u044b\u043c',
  sectorTip:
    '\u0417\u0434\u0435\u0441\u044c \u0432\u0438\u0434\u043d\u043e, \u043a\u0442\u043e \u0436\u0438\u0432\u0451\u0442 \u0432 \u0441\u0435\u043a\u0442\u043e\u0440\u0435, \u043a\u0430\u043a\u0438\u0435 \u0438\u0434\u0443\u0442 \u0441\u043e\u0431\u044b\u0442\u0438\u044f \u0438 \u043a\u0430\u043a\u0438\u0435 \u0441\u0438\u0433\u043d\u0430\u043b\u044b \u043f\u0440\u0438\u0448\u043b\u0438 \u0442\u0432\u043e\u0435\u0439 \u0441\u0442\u0430\u043d\u0446\u0438\u0438.'
}

export function SectorPage() {
  const queryClient = useQueryClient()
  const feedback = useActionFeedback()
  const sector = useSector({ refetchInterval: 5000 })
  const notifications = useNotifications({ refetchInterval: 5000 })
  if (!sector.data) return <div className="text-textMute">{t.loading}</div>

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_0.9fr]">
      <Card>
        <SectionTitle
          title={
            <Tooltip label={t.sectorTip}>
              <span>{sector.data.sector_name}</span>
            </Tooltip>
          }
          subtitle={`${t.market}: ${sector.data.market_mood}`}
        />
        <div className="space-y-3">
          {sector.data.players.map((player) => (
            <div key={player.station_id} className="rounded-xl border border-borderSoft bg-panelSoft p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="font-medium">{player.station_name}</div>
                  <div className="text-xs text-textMute">
                    {player.owner_username} {'\u2022'} {labelForSpecialization(player.specialization)}
                  </div>
                </div>
                <div className="text-sm text-accent">
                  {t.level} {player.level}
                </div>
              </div>
            </div>
          ))}
        </div>
        <SectionTitle title={t.events} subtitle={t.eventsSub} />
        <div className="space-y-3">
          {sector.data.events.map((event) => (
            <div key={event.id} className="rounded-xl border border-borderSoft bg-panelSoft p-4">
              <div className="font-medium">{event.title}</div>
              <div className="mt-1 text-sm text-textMute">{event.description}</div>
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <SectionTitle title={t.notifications} subtitle={t.notificationsSub} />
        <div className="space-y-3">
          {notifications.data?.map((item) => (
            <div key={item.id} className="rounded-xl border border-borderSoft bg-panelSoft p-4">
              <div className="font-medium">{item.title}</div>
              <div className="mt-1 text-sm text-textMute">{item.message}</div>
              {!item.read_at ? (
                <Button
                  className="mt-3"
                  variant="ghost"
                  onClick={async () => {
                    try {
                      await api.post(`/notifications/${item.id}/read`)
                      feedback.success('\u0423\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0435 \u043e\u0442\u043c\u0435\u0447\u0435\u043d\u043e')
                      await queryClient.invalidateQueries({ queryKey: ['notifications'] })
                    } catch (error) {
                      feedback.error(error)
                    }
                  }}
                >
                  {t.markRead}
                </Button>
              ) : null}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
