import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Button } from '../../components/ui'
import { api } from '../../lib/api'
import { useAuthStore } from '../../store/authStore'

const t = {
  requestFailed: '\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0432\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u044c \u0437\u0430\u043f\u0440\u043e\u0441',
  heading: '\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u0430\u0432\u0442\u043e\u043d\u043e\u043c\u043d\u043e\u0439 \u0441\u0442\u0430\u043d\u0446\u0438\u0435\u0439',
  subheading:
    '\u041a\u043e\u0440\u043e\u0442\u043a\u0438\u0435 \u0441\u0435\u0441\u0441\u0438\u0438. \u041e\u0431\u0449\u0438\u0439 \u0440\u044b\u043d\u043e\u043a. \u042f\u0441\u043d\u044b\u0435 \u0443\u0437\u043a\u0438\u0435 \u043c\u0435\u0441\u0442\u0430.',
  login: '\u0412\u0445\u043e\u0434',
  register: '\u0420\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044f',
  identity: 'Email \u0438\u043b\u0438 \u043b\u043e\u0433\u0438\u043d',
  username: '\u041b\u043e\u0433\u0438\u043d',
  stationName: '\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0441\u0442\u0430\u043d\u0446\u0438\u0438',
  password: '\u041f\u0430\u0440\u043e\u043b\u044c',
  freight: '\u0424\u0440\u0430\u0445\u0442\u043e\u0432\u044b\u0439 \u0443\u0437\u0435\u043b',
  repair: '\u0420\u0435\u043c\u043e\u043d\u0442\u043d\u044b\u0439 \u0443\u0437\u0435\u043b',
  data: '\u0411\u0438\u0440\u0436\u0430 \u0434\u0430\u043d\u043d\u044b\u0445',
  enter: '\u0412\u043e\u0439\u0442\u0438 \u0432 \u0441\u0435\u043a\u0442\u043e\u0440',
  launch: '\u0417\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u044c \u0441\u0442\u0430\u043d\u0446\u0438\u044e'
}

export function AuthPage() {
  const navigate = useNavigate()
  const setSession = useAuthStore((state) => state.setSession)
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setError(null)
    try {
      const payload =
        mode === 'login'
          ? { identity: form.get('identity'), password: form.get('password') }
          : {
              email: form.get('email'),
              username: form.get('username'),
              password: form.get('password'),
              station_name: form.get('station_name'),
              specialization: form.get('specialization')
            }
      const data = await api.post<{ access_token: string; user: { id: string; email: string; username: string; roles?: string[] } }>(
        mode === 'login' ? '/auth/login' : '/auth/register',
        payload
      )
      setSession(data.access_token, data.user)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : t.requestFailed)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,#203247_0%,#0b1118_65%)] p-4 text-textMain">
      <Card className="w-full max-w-md border-accent/15">
        <div className="mb-6">
          <div className="text-[11px] uppercase tracking-[0.35em] text-accentWarm">Sector Relay</div>
          <h1 className="mt-2 text-2xl font-semibold">{t.heading}</h1>
          <p className="mt-2 text-sm text-textMute">{t.subheading}</p>
        </div>
        <div className="mb-4 grid grid-cols-2 gap-2 rounded-xl bg-panelSoft p-1">
          <button
            type="button"
            className={`rounded-lg py-2 text-sm ${mode === 'login' ? 'bg-accent text-slate-950' : 'text-textMute'}`}
            onClick={() => setMode('login')}
          >
            {t.login}
          </button>
          <button
            type="button"
            className={`rounded-lg py-2 text-sm ${mode === 'register' ? 'bg-accent text-slate-950' : 'text-textMute'}`}
            onClick={() => setMode('register')}
          >
            {t.register}
          </button>
        </div>
        <form className="space-y-3" onSubmit={onSubmit}>
          {mode === 'login' ? (
            <input
              name="identity"
              placeholder={t.identity}
              className="w-full rounded-xl border border-borderSoft bg-bg px-4 py-3"
            />
          ) : (
            <>
              <input name="email" placeholder="Email" className="w-full rounded-xl border border-borderSoft bg-bg px-4 py-3" />
              <input name="username" placeholder={t.username} className="w-full rounded-xl border border-borderSoft bg-bg px-4 py-3" />
              <input
                name="station_name"
                placeholder={t.stationName}
                className="w-full rounded-xl border border-borderSoft bg-bg px-4 py-3"
              />
              <select name="specialization" className="w-full rounded-xl border border-borderSoft bg-bg px-4 py-3">
                <option value="freight_hub">{t.freight}</option>
                <option value="repair_nexus">{t.repair}</option>
                <option value="data_exchange">{t.data}</option>
              </select>
            </>
          )}
          <input type="password" name="password" placeholder={t.password} className="w-full rounded-xl border border-borderSoft bg-bg px-4 py-3" />
          {error ? <div className="rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div> : null}
          <Button type="submit" className="w-full">
            {mode === 'login' ? t.enter : t.launch}
          </Button>
        </form>
      </Card>
    </div>
  )
}
