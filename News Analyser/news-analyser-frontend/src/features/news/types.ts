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

export type SseEventType =
  | 'thinking'
  | 'tool_call'
  | 'tool_result'
  | 'text_chunk'
  | 'done'
  | 'error'

export interface SseEvent {
  type: SseEventType
  content: string
  toolName?: string
  articleCount?: number
}

export type SummaryPhase = 'idle' | 'loading' | 'streaming' | 'done' | 'error'

export interface SummaryState {
  phase: SummaryPhase
  statusMessage: string
  summaryText: string
  marketText: string
  errorMessage: string
  articleCount: number
}

