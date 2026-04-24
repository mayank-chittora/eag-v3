export const APP_NAME = 'News Analyser'
export const MAX_HISTORICAL_DAYS = 365
export const NEWS_PAGE_SIZE = 20

export const SENTIMENT_LABELS = {
  POSITIVE: 'Positive',
  NEGATIVE: 'Negative',
  NEUTRAL: 'Neutral',
} as const

export const SENTIMENT_COLORS = {
  POSITIVE: { text: 'text-green-700', bg: 'bg-green-50', border: 'border-green-200', dot: 'bg-green-500' },
  NEGATIVE: { text: 'text-red-700', bg: 'bg-red-50', border: 'border-red-200', dot: 'bg-red-500' },
  NEUTRAL:  { text: 'text-gray-600', bg: 'bg-gray-100', border: 'border-gray-200', dot: 'bg-gray-400' },
}
