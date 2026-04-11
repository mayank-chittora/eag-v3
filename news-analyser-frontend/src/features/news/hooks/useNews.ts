import { useQuery } from '@tanstack/react-query'
import { newsService } from '../services/newsService'
import type { NewsFilter } from '../types'

export function useNews(filter: NewsFilter) {
  return useQuery({
    queryKey: ['news', filter],
    queryFn: () => newsService.getNews(filter),
    staleTime: 5 * 60 * 1000,
  })
}
