import { create } from 'zustand'
import type { NewsFilter, SentimentLabel } from '../types'

interface NewsState {
  filter: NewsFilter
  setCategories: (categories: string[]) => void
  setSentiment: (sentiment: SentimentLabel | '') => void
  setSources: (sources: string[]) => void
  setPage: (page: number) => void
  resetFilter: () => void
}

const DEFAULT_FILTER: NewsFilter = {
  categories: [],
  sentiment: '',
  sources: [],
  page: 0,
  pageSize: 20,
}

export const useNewsStore = create<NewsState>((set) => ({
  filter: { ...DEFAULT_FILTER },

  setCategories: (categories) =>
    set((state) => ({ filter: { ...state.filter, categories, page: 0 } })),

  setSentiment: (sentiment) =>
    set((state) => ({ filter: { ...state.filter, sentiment, page: 0 } })),

  setSources: (sources) =>
    set((state) => ({ filter: { ...state.filter, sources, page: 0 } })),

  setPage: (page) =>
    set((state) => ({ filter: { ...state.filter, page } })),

  resetFilter: () => set({ filter: { ...DEFAULT_FILTER } }),
}))
