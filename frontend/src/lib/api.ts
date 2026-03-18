import { useAuthStore } from '../store/authStore'

function withApiPrefix(path: string) {
  return path.startsWith('/api/') ? path : `/api${path}`
}

type ApiValidationItem = {
  msg?: string
  loc?: Array<string | number>
  field?: string
  message?: string
}

type ApiErrorPayload = {
  detail?: string | ApiValidationItem[]
  message?: string
}

function normalizeErrorMessage(payload: ApiErrorPayload | null | undefined) {
  if (!payload) return 'Request failed'

  if (typeof payload.detail === 'string' && payload.detail.trim()) {
    return payload.detail
  }

  if (Array.isArray(payload.detail) && payload.detail.length) {
    return payload.detail
      .map((item: ApiValidationItem) => {
        const field = item.field ?? (Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : undefined)
        if (typeof item.message === 'string' && item.message.trim()) return item.message
        if (field === 'username') return 'Логин содержит недопустимые символы.'
        if (field === 'email') return 'Введите корректный email.'
        if (field === 'password') return 'Пароль не прошёл проверку.'
        if (field === 'station_name') return 'Название станции слишком короткое или слишком длинное.'
        if (field === 'key') {
          return 'Поле key — это технический slug. Тут нужна только латиница в нижнем регистре, цифры и _. Название при этом можно писать по-русски.'
        }
        return item.msg ?? 'Некорректные данные.'
      })
      .join(' ')
  }

  if (typeof payload.message === 'string' && payload.message.trim()) {
    return payload.message
  }

  return 'Request failed'
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = useAuthStore.getState().accessToken
  const isFormData = options.body instanceof FormData
  const response = await fetch(withApiPrefix(path), {
    ...options,
    credentials: 'include',
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {})
    }
  })
  if (response.status === 401 && token) {
    const refreshed = await tryRefresh()
    if (refreshed) {
      return request<T>(path, options)
    }
  }
  if (!response.ok) {
    const error = (await response.json().catch(() => ({ detail: 'Request failed' }))) as ApiErrorPayload
    throw new Error(normalizeErrorMessage(error))
  }
  return response.json() as Promise<T>
}

async function tryRefresh(): Promise<boolean> {
  try {
    const response = await fetch(withApiPrefix('/auth/refresh'), { method: 'POST', credentials: 'include' })
    if (!response.ok) {
      if (response.status === 401) {
        useAuthStore.getState().clearSessionHint?.()
      }
      return false
    }
    const data = (await response.json()) as { access_token: string }
    useAuthStore.getState().setAccessToken(data.access_token)
    return true
  } catch {
    useAuthStore.getState().logout()
    return false
  }
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  postForm: <T>(path: string, body: FormData) => request<T>(path, { method: 'POST', body })
}
