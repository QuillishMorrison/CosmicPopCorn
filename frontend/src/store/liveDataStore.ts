import { create } from 'zustand'
import type { LiveDashboardSnapshot } from '../types/game'

type LiveDataState = {
  snapshot: LiveDashboardSnapshot | null
  connected: boolean
  setSnapshot: (snapshot: LiveDashboardSnapshot) => void
  setConnected: (connected: boolean) => void
  clear: () => void
}

export const useLiveDataStore = create<LiveDataState>((set) => ({
  snapshot: null,
  connected: false,
  setSnapshot: (snapshot) => set({ snapshot }),
  setConnected: (connected) => set({ connected }),
  clear: () => set({ snapshot: null, connected: false })
}))
