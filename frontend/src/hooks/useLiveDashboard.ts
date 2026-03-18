import { useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import { useLiveDataStore } from '../store/liveDataStore'
import type { LiveDashboardSnapshot } from '../types/game'

function buildWebSocketUrl(token: string) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/station/live?token=${encodeURIComponent(token)}`
}

export function useLiveDashboard() {
  const token = useAuthStore((state) => state.accessToken)
  const setSnapshot = useLiveDataStore((state) => state.setSnapshot)
  const setConnected = useLiveDataStore((state) => state.setConnected)
  const clear = useLiveDataStore((state) => state.clear)

  useEffect(() => {
    if (!token) {
      clear()
      return
    }

    const socket = new WebSocket(buildWebSocketUrl(token))

    socket.onopen = () => {
      setConnected(true)
    }

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as LiveDashboardSnapshot
      setSnapshot(payload)
    }

    socket.onclose = () => {
      setConnected(false)
    }

    socket.onerror = () => {
      setConnected(false)
    }

    return () => {
      clear()
      setConnected(false)
      socket.close()
    }
  }, [clear, setConnected, setSnapshot, token])
}
