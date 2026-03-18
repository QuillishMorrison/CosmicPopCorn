import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

type User = { id: string; email: string; username: string; roles?: string[] }

type AuthState = {
  accessToken: string | null
  user: User | null
  hasSessionHint: boolean
  setSession: (accessToken: string, user: User) => void
  setAccessToken: (accessToken: string) => void
  setUser: (user: User) => void
  logout: () => void
  clearSessionHint: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,
      hasSessionHint: false,
      setSession: (accessToken, user) => set({ accessToken, user, hasSessionHint: true }),
      setAccessToken: (accessToken) => set((state) => ({ ...state, accessToken })),
      setUser: (user) => set((state) => ({ ...state, user, hasSessionHint: true })),
      logout: () => set({ accessToken: null, user: null, hasSessionHint: false }),
      clearSessionHint: () => set((state) => ({ ...state, hasSessionHint: false }))
    }),
    {
      name: 'sector-relay-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        user: state.user,
        hasSessionHint: state.hasSessionHint
      })
    }
  )
)
