import { create } from 'zustand'

export type ToastItem = {
  id: string
  title: string
  tone: 'success' | 'error' | 'info'
  count: number
  updatedAt: number
}

export type ToastInput = {
  title: string
  tone: ToastItem['tone']
}

type ToastState = {
  items: ToastItem[]
  push: (toast: ToastInput) => void
  remove: (id: string) => void
}

export const useToastStore = create<ToastState>((set) => ({
  items: [],
  push: (toast) =>
    set((state) => {
      const existing = state.items.find((item) => item.title === toast.title && item.tone === toast.tone)
      if (existing) {
        return {
          items: state.items.map((item) =>
            item.id === existing.id
              ? {
                  ...item,
                  count: item.count + 1,
                  updatedAt: Date.now()
                }
              : item
          )
        }
      }

      return {
        items: [
          ...state.items,
          {
            ...toast,
            id: crypto.randomUUID(),
            count: 1,
            updatedAt: Date.now()
          }
        ]
      }
    }),
  remove: (id) =>
    set((state) => ({
      items: state.items.filter((item) => item.id !== id)
    }))
}))
