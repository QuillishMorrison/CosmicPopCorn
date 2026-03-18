import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useActionFeedback } from '../hooks/useActionFeedback'
import { useChatThreads, useDirectChat, useGlobalChat } from '../hooks/useGameData'
import { api } from '../lib/api'
import { useAuthStore } from '../store/authStore'

const t = {
  open: 'Чат',
  title: 'Связь сектора',
  subtitle: 'Глобальный канал и личные сообщения',
  global: 'Глобал',
  direct: 'Личка',
  placeholderGlobal: 'Написать в глобал',
  placeholderDirect: 'Сообщение игроку',
  emptyGlobal: 'Глобальный канал пока тихий.',
  emptyDirect: 'Выбери игрока слева, чтобы открыть личку.',
  noPlayers: 'Игроки сектора не найдены.',
  loadingPlayers: 'Загружаю игроков...',
  noHistory: 'История переписки пока пустая.',
  send: 'Отправить',
  close: 'Закрыть',
  choosePlayer: 'Выбери игрока для лички',
  dmWith: 'Личка с',
  stationFallback: 'Станция сектора',
  me: 'Вы'
}

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

export function ChatWidget() {
  const queryClient = useQueryClient()
  const feedback = useActionFeedback()
  const currentUser = useAuthStore((state) => state.user)
  const [isOpen, setIsOpen] = useState(false)
  const [tab, setTab] = useState<'global' | 'direct'>('global')
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null)

  const globalScrollerRef = useRef<HTMLDivElement | null>(null)
  const directScrollerRef = useRef<HTMLDivElement | null>(null)

  const globalChat = useGlobalChat({ enabled: isOpen, refetchInterval: isOpen && tab === 'global' ? 3000 : false })
  const threads = useChatThreads({ enabled: isOpen, refetchInterval: isOpen ? 5000 : false })
  const directChat = useDirectChat(selectedUserId, { enabled: isOpen && tab === 'direct', refetchInterval: 3000 })

  const activeThread = useMemo(
    () => threads.data?.find((item) => item.user_id === selectedUserId) ?? null,
    [selectedUserId, threads.data]
  )

  useEffect(() => {
    if (tab !== 'direct') return
    if (!threads.data?.length) {
      setSelectedUserId(null)
      return
    }
    if (!selectedUserId || !threads.data.some((item) => item.user_id === selectedUserId)) {
      setSelectedUserId(threads.data[0].user_id)
    }
  }, [tab, threads.data, selectedUserId])

  useEffect(() => {
    const target = tab === 'global' ? globalScrollerRef.current : directScrollerRef.current
    if (!target) return
    target.scrollTop = target.scrollHeight
  }, [tab, globalChat.data, directChat.data, selectedUserId, isOpen])

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    const body = String(data.get('body') ?? '')

    try {
      if (tab === 'global') {
        await api.post('/chat/global', { body })
        await queryClient.invalidateQueries({ queryKey: ['chat', 'global'] })
      } else {
        if (!selectedUserId) return
        await api.post(`/chat/direct/${selectedUserId}`, { body })
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: ['chat', 'direct', selectedUserId] }),
          queryClient.invalidateQueries({ queryKey: ['chat', 'threads'] })
        ])
      }

      form.reset()
    } catch (error) {
      feedback.error(error)
    }
  }

  function renderMessageCard(
    item: {
      id: string
      sender_user_id: string
      sender_username: string
      body: string
      created_at: string
    },
    mine = false
  ) {
    return (
      <div
        key={item.id}
        className={`max-w-[88%] rounded-2xl px-3 py-2.5 shadow-sm ${
          mine ? 'bg-accent text-slate-950' : 'border border-borderSoft bg-panelSoft text-textMain'
        }`}
      >
        <div className={`text-[11px] ${mine ? 'text-slate-800/75' : 'text-textMute'}`}>
          {mine ? t.me : item.sender_username} • {formatTime(item.created_at)}
        </div>
        <div className="mt-1 whitespace-pre-wrap break-words text-sm leading-relaxed">{item.body}</div>
      </div>
    )
  }

  return (
    <>
      <button
        type="button"
        className="fixed bottom-20 right-4 z-40 rounded-full border border-borderSoft bg-panel/92 px-4 py-3 text-sm font-semibold text-textMain shadow-panel backdrop-blur transition hover:border-accent/40 hover:text-accent md:bottom-5"
        onClick={() => setIsOpen((value) => !value)}
      >
        {t.open}
      </button>

      {isOpen ? (
        <section className="fixed bottom-36 right-4 z-40 flex h-[560px] max-h-[72vh] w-[min(95vw,420px)] flex-col overflow-hidden rounded-[22px] border border-borderSoft bg-[#0d141d]/95 shadow-panel backdrop-blur md:bottom-20">
          <header className="shrink-0 border-b border-borderSoft bg-panel/55 px-4 py-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="text-sm font-semibold text-textMain">{t.title}</div>
                <div className="mt-1 text-xs text-textMute">{t.subtitle}</div>
              </div>
              <button
                type="button"
                className="rounded-full border border-borderSoft px-3 py-1 text-xs text-textMute transition hover:text-textMain"
                onClick={() => setIsOpen(false)}
              >
                {t.close}
              </button>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-2 rounded-xl bg-panelSoft/80 p-1">
              <button
                type="button"
                className={`rounded-lg px-3 py-2 text-sm transition ${
                  tab === 'global' ? 'bg-accent text-slate-950' : 'text-textMute hover:text-textMain'
                }`}
                onClick={() => setTab('global')}
              >
                {t.global}
              </button>
              <button
                type="button"
                className={`rounded-lg px-3 py-2 text-sm transition ${
                  tab === 'direct' ? 'bg-accent text-slate-950' : 'text-textMute hover:text-textMain'
                }`}
                onClick={() => setTab('direct')}
              >
                {t.direct}
              </button>
            </div>
          </header>

          {tab === 'global' ? (
            <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
              <div ref={globalScrollerRef} className="min-h-0 flex-1 space-y-2 overflow-y-auto px-3 py-3">
                {globalChat.data?.length ? (
                  globalChat.data.map((item) => (
                    <div key={item.id} className="flex justify-start">
                      {renderMessageCard(item)}
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-borderSoft bg-panelSoft/70 px-4 py-4 text-sm text-textMute">
                    {t.emptyGlobal}
                  </div>
                )}
              </div>

              <form className="shrink-0 border-t border-borderSoft bg-panel/55 p-3" onSubmit={sendMessage}>
                <div className="flex items-end gap-2">
                  <input
                    name="body"
                    placeholder={t.placeholderGlobal}
                    className="min-w-0 flex-1 rounded-2xl border border-borderSoft bg-panelSoft px-3 py-3 text-sm text-textMain outline-none transition focus:border-accent/45"
                  />
                  <button className="rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-slate-950 transition hover:brightness-105" type="submit">
                    {t.send}
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div className="grid min-h-0 flex-1 grid-cols-[136px_1fr] overflow-hidden">
              <aside className="min-h-0 overflow-hidden border-r border-borderSoft bg-panel/45 px-2 py-3">
                <div className="h-full space-y-2 overflow-y-auto">
                  {threads.isLoading ? (
                    <div className="px-2 py-3 text-xs text-textMute">{t.loadingPlayers}</div>
                  ) : threads.data?.length ? (
                    threads.data.map((thread) => (
                      <button
                        key={thread.user_id}
                        type="button"
                        className={`w-full rounded-2xl border px-3 py-3 text-left transition ${
                          selectedUserId === thread.user_id
                            ? 'border-accent/35 bg-accent/10 text-textMain'
                            : 'border-transparent bg-transparent text-textMute hover:border-borderSoft hover:bg-panelSoft/80 hover:text-textMain'
                        }`}
                        onClick={() => setSelectedUserId(thread.user_id)}
                      >
                        <div className="truncate text-sm font-medium">{thread.username}</div>
                        <div className="mt-1 truncate text-[11px] text-textMute">{thread.station_name ?? t.stationFallback}</div>
                        {thread.last_message ? (
                          <div className="mt-2 truncate text-[11px] text-textMute/80">{thread.last_message}</div>
                        ) : null}
                      </button>
                    ))
                  ) : (
                    <div className="px-2 py-3 text-xs text-textMute">{t.noPlayers}</div>
                  )}
                </div>
              </aside>

              <div className="flex min-h-0 flex-col overflow-hidden">
                <div className="shrink-0 border-b border-borderSoft bg-panel/35 px-3 py-3 text-xs text-textMute">
                  {activeThread ? `${t.dmWith} ${activeThread.username}` : t.choosePlayer}
                </div>

                <div ref={directScrollerRef} className="min-h-0 flex-1 space-y-2 overflow-y-auto px-3 py-3">
                  {selectedUserId && directChat.data?.length ? (
                    directChat.data.map((item) => {
                      const mine = item.sender_user_id === currentUser?.id
                      return (
                        <div key={item.id} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
                          {renderMessageCard(item, mine)}
                        </div>
                      )
                    })
                  ) : (
                    <div className="rounded-2xl border border-dashed border-borderSoft bg-panelSoft/70 px-4 py-4 text-sm text-textMute">
                      {selectedUserId ? t.noHistory : t.emptyDirect}
                    </div>
                  )}
                </div>

                <form className="shrink-0 border-t border-borderSoft bg-panel/55 p-3" onSubmit={sendMessage}>
                  <div className="flex items-end gap-2">
                    <input
                      name="body"
                      placeholder={t.placeholderDirect}
                      disabled={!selectedUserId}
                      className="min-w-0 flex-1 rounded-2xl border border-borderSoft bg-panelSoft px-3 py-3 text-sm text-textMain outline-none transition focus:border-accent/45 disabled:opacity-50"
                    />
                    <button
                      className="rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-slate-950 transition hover:brightness-105 disabled:opacity-50"
                      type="submit"
                      disabled={!selectedUserId}
                    >
                      {t.send}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </section>
      ) : null}
    </>
  )
}
