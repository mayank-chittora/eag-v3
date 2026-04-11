export type SentimentLabel = 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'

export interface Category {
  id: number
  name: string
  slug: string
  accentColor: string
  lightBgColor: string
}

export interface NewsArticle {
  id: number
  url: string
  headline: string
  summary: string
  sourceName: string
  imageUrl?: string
  publishedAt: string
  sentiment: SentimentLabel
  categories: Category[]
}

export interface PageMeta {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

export interface PaginatedArticles {
  data: NewsArticle[]
  meta: PageMeta
}

export interface NewsFilter {
  date?: string
  categories?: string[]
  sentiment?: SentimentLabel | ''
  sources?: string[]
  page?: number
  pageSize?: number
}

