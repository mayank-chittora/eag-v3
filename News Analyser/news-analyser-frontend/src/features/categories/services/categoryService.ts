import { apiClient } from '@/lib/apiClient'
import type { Category } from '@/features/news/types'

export const categoryService = {
  getCategories: (): Promise<{ data: Category[] }> =>
    apiClient.get('/categories'),

  getSources: (): Promise<{ data: string[] }> =>
    apiClient.get('/categories/sources'),
}
