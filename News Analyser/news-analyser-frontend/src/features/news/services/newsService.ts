import { apiClient } from '@/lib/apiClient'
import type { NewsFilter, PaginatedArticles, NewsArticle } from '../types'

export const newsService = {
  getNews: (filter: NewsFilter): Promise<PaginatedArticles> =>
    apiClient.get('/news', {
      params: {
        ...filter,
        categories: filter.categories?.join(','),
        sources: filter.sources?.join(','),
        sentiment: filter.sentiment || undefined,
      },
    }),

  getArticleById: (id: number): Promise<{ data: NewsArticle }> =>
    apiClient.get(`/news/${id}`),
}
