import { useQuery } from '@tanstack/react-query'
import { categoryService } from '../services/categoryService'

export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: () => categoryService.getCategories(),
    staleTime: 60 * 60 * 1000, // 1 hour
    select: (res) => res.data,
  })
}

export function useSources() {
  return useQuery({
    queryKey: ['sources'],
    queryFn: () => categoryService.getSources(),
    staleTime: 60 * 60 * 1000,
    select: (res) => res.data,
  })
}
