import { FormEvent } from 'react'
import { Button, Card, SectionTitle } from '../../components/ui'
import { useActionFeedback } from '../../hooks/useActionFeedback'
import { api } from '../../lib/api'
import { useAuthStore } from '../../store/authStore'

const t = {
  account: '\u0410\u043a\u043a\u0430\u0443\u043d\u0442',
  accountSub: '\u0411\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u044b\u0439 \u0434\u043e\u0441\u0442\u0443\u043f \u0438 \u043f\u0440\u043e\u0444\u0438\u043b\u044c',
  user: '\u0418\u0433\u0440\u043e\u043a',
  password: '\u0421\u043c\u0435\u043d\u0430 \u043f\u0430\u0440\u043e\u043b\u044f',
  passwordSub: '\u0423\u043c\u0435\u0440\u0435\u043d\u043d\u0430\u044f \u043f\u043e\u043b\u0438\u0442\u0438\u043a\u0430 \u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u0438',
  current: '\u0422\u0435\u043a\u0443\u0449\u0438\u0439 \u043f\u0430\u0440\u043e\u043b\u044c',
  next: '\u041d\u043e\u0432\u044b\u0439 \u043f\u0430\u0440\u043e\u043b\u044c',
  submit: '\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u043f\u0430\u0440\u043e\u043b\u044c'
}

export function SettingsPage() {
  const user = useAuthStore((state) => state.user)
  const feedback = useActionFeedback()

  async function changePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    try {
      await api.post('/auth/change-password', {
        current_password: form.get('current_password'),
        new_password: form.get('new_password')
      })
      event.currentTarget.reset()
      feedback.success('\u041f\u0430\u0440\u043e\u043b\u044c \u043e\u0431\u043d\u043e\u0432\u043b\u0451\u043d')
    } catch (error) {
      feedback.error(error)
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <SectionTitle title={t.account} subtitle={t.accountSub} />
        <div className="space-y-3 rounded-xl bg-panelSoft p-4">
          <div>
            <span className="text-textMute">{t.user}:</span> {user?.username}
          </div>
          <div>
            <span className="text-textMute">Email:</span> {user?.email}
          </div>
        </div>
      </Card>
      <Card>
        <SectionTitle title={t.password} subtitle={t.passwordSub} />
        <form className="space-y-3" onSubmit={changePassword}>
          <input type="password" name="current_password" placeholder={t.current} className="w-full rounded-xl border border-borderSoft bg-bg px-4 py-3" />
          <input type="password" name="new_password" placeholder={t.next} className="w-full rounded-xl border border-borderSoft bg-bg px-4 py-3" />
          <Button type="submit">{t.submit}</Button>
        </form>
      </Card>
    </div>
  )
}
