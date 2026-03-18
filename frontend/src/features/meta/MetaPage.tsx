import { useQueryClient } from '@tanstack/react-query'
import { Button, Card, Progress, SectionTitle, Tooltip } from '../../components/ui'
import { useMetaTree } from '../../hooks/useGameData'
import { useActionFeedback } from '../../hooks/useActionFeedback'
import { api } from '../../lib/api'

const t = {
  loading: '\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0443\u043b\u0443\u0447\u0448\u0435\u043d\u0438\u0439...',
  title: '\u041c\u0435\u0442\u0430\u043f\u0440\u043e\u0433\u0440\u0435\u0441\u0441\u0438\u044f',
  sub: '\u041f\u043e\u0441\u0442\u043e\u044f\u043d\u043d\u044b\u0435 \u0443\u043b\u0443\u0447\u0448\u0435\u043d\u0438\u044f \u0437\u0430 \u0438\u043d\u0441\u0430\u0439\u0442',
  buy: '\u0423\u043b\u0443\u0447\u0448\u0438\u0442\u044c \u0434\u043e',
  tip:
    '\u0418\u043d\u0441\u0430\u0439\u0442 \u044d\u0442\u043e \u043c\u0435\u0442\u0430-\u0432\u0430\u043b\u044e\u0442\u0430. \u041a\u0430\u0436\u0434\u0430\u044f \u043f\u043e\u043a\u0443\u043f\u043a\u0430 \u0434\u0430\u0451\u0442 \u043f\u043e\u0441\u0442\u043e\u044f\u043d\u043d\u043e\u0435 \u0443\u0441\u0438\u043b\u0435\u043d\u0438\u0435 \u0431\u0430\u0437\u044b.'
}

export function MetaPage() {
  const queryClient = useQueryClient()
  const feedback = useActionFeedback()
  const meta = useMetaTree({ refetchInterval: 10000 })
  if (!meta.data) return <div className="text-textMute">{t.loading}</div>

  return (
    <Card>
      <SectionTitle
        title={
          <Tooltip label={t.tip}>
            <span>{t.title}</span>
          </Tooltip>
        }
        subtitle={t.sub}
      />
      <div className="grid gap-3">
        {meta.data.map((upgrade) => (
          <div key={upgrade.key} className="rounded-xl border border-borderSoft bg-panelSoft p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="font-medium">{upgrade.name}</div>
                <div className="mt-1 text-sm text-textMute">{upgrade.description}</div>
              </div>
              <div className="text-sm text-accent">{upgrade.base_cost * (upgrade.current_level + 1)} {'\u0438\u043d\u0441.'}</div>
            </div>
            <div className="mt-3">
              <Progress value={(upgrade.current_level / upgrade.max_level) * 100} />
            </div>
            <Button
              className="mt-3"
              onClick={async () => {
                try {
                  await api.post('/meta/purchase', { key: upgrade.key })
                  feedback.success(`${upgrade.name} ${'\u043a\u0443\u043f\u043b\u0435\u043d\u043e'}`)
                  await Promise.all([
                    queryClient.invalidateQueries({ queryKey: ['meta'] }),
                    queryClient.invalidateQueries({ queryKey: ['station'] })
                  ])
                } catch (error) {
                  feedback.error(error)
                }
              }}
            >
              {t.buy} {upgrade.current_level + 1}/{upgrade.max_level}
            </Button>
          </div>
        ))}
      </div>
    </Card>
  )
}
