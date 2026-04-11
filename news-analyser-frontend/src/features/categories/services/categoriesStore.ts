import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface CategoriesState {
  selected: string[] // slugs
  toggle: (slug: string) => void
  setAll: (slugs: string[]) => void
  clearAll: () => void
}

export const useCategoriesStore = create<CategoriesState>()(
  persist(
    (set) => ({
      selected: [],

      toggle: (slug) =>
        set((state) => ({
          selected: state.selected.includes(slug)
            ? state.selected.filter((s) => s !== slug)
            : [...state.selected, slug],
        })),

      setAll: (slugs) => set({ selected: slugs }),

      clearAll: () => set({ selected: [] }),
    }),
    { name: 'news-analyser-categories' }
  )
)
