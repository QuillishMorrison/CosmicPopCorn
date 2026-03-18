import { create } from 'zustand'

export type ActionCost = {
  resource: string
  amount: number
}

export type ActionPreview = {
  title: string
  description?: string
  costs: ActionCost[]
}

type ActionPreviewState = {
  preview: ActionPreview | null
  setPreview: (preview: ActionPreview) => void
  clearPreview: () => void
}

export const useActionPreviewStore = create<ActionPreviewState>((set) => ({
  preview: null,
  setPreview: (preview) => set({ preview }),
  clearPreview: () => set({ preview: null })
}))
