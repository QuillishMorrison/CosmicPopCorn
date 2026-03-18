import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

export const MAX_HUB_MARKET_PINS = 3

type MarketPinsState = {
  pinsByStation: Record<string, string[]>
  setPinnedResources: (stationId: string, resources: string[]) => void
}

function normalizePins(resources: string[]): string[] {
  const uniquePins: string[] = []
  for (const resource of resources) {
    if (!resource || uniquePins.includes(resource)) {
      continue
    }
    uniquePins.push(resource)
    if (uniquePins.length >= MAX_HUB_MARKET_PINS) {
      break
    }
  }
  return uniquePins
}

export const useHubMarketPinsStore = create<MarketPinsState>()(
  persist(
    (set) => ({
      pinsByStation: {},
      setPinnedResources: (stationId, resources) =>
        set((state) => {
          if (!stationId) {
            return state
          }
          return {
            pinsByStation: {
              ...state.pinsByStation,
              [stationId]: normalizePins(resources)
            }
          }
        })
    }),
    {
      name: 'sector-relay-market-pins',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        pinsByStation: state.pinsByStation
      })
    }
  )
)
