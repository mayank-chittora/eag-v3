import { cn } from '@/lib/utils'
import { SENTIMENT_COLORS, SENTIMENT_LABELS } from '@/lib/constants'
import type { SentimentLabel } from '@/features/news/types'

interface SentimentBadgeProps {
  sentiment: SentimentLabel
  className?: string
}

export function SentimentBadge({ sentiment, className }: SentimentBadgeProps) {
  const colors = SENTIMENT_COLORS[sentiment]
  return (
    <span
      role="status"
      aria-label={`Sentiment: ${SENTIMENT_LABELS[sentiment]}`}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold border',
        colors.bg, colors.text, colors.border,
        className
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', colors.dot)} aria-hidden="true" />
      {SENTIMENT_LABELS[sentiment]}
    </span>
  )
}
