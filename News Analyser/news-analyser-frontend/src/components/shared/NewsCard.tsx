import { ExternalLink, Clock } from 'lucide-react'
import { SentimentBadge } from './SentimentBadge'
import { CategoryChip } from './CategoryChip'
import { cn, formatRelativeTime, truncate } from '@/lib/utils'
import type { NewsArticle } from '@/features/news/types'

interface NewsCardProps {
  article: NewsArticle
  className?: string
}

export function NewsCard({ article, className }: NewsCardProps) {
  return (
    <article
      className={cn(
        'bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md',
        'hover:-translate-y-0.5 transition-all duration-150 flex flex-col',
        className
      )}
    >
      {article.imageUrl && (
        <div className="relative h-44 overflow-hidden rounded-t-lg">
          <img
            src={article.imageUrl}
            alt=""
            loading="lazy"
            className="w-full h-full object-cover"
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
        </div>
      )}

      <div className="p-4 flex flex-col flex-1 gap-3">
        {/* Source + time */}
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="font-medium text-gray-700">{article.sourceName}</span>
          <span aria-hidden="true">·</span>
          <Clock size={12} aria-hidden="true" />
          <time dateTime={article.publishedAt}>
            {formatRelativeTime(article.publishedAt)}
          </time>
        </div>

        {/* Headline */}
        <h3 className="font-merriweather font-bold text-gray-900 text-base leading-snug line-clamp-2">
          {article.headline}
        </h3>

        {/* Summary */}
        {article.summary && (
          <p className="text-sm text-gray-600 leading-relaxed line-clamp-2 flex-1">
            {truncate(article.summary, 180)}
          </p>
        )}

        {/* Footer: categories + sentiment + link */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-gray-100 mt-auto">
          <div className="flex flex-wrap gap-1">
            {article.categories.slice(0, 2).map((cat) => (
              <CategoryChip key={cat.id} category={cat} size="sm" />
            ))}
          </div>
          <div className="flex items-center gap-2">
            <SentimentBadge sentiment={article.sentiment} />
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Read full article: ${article.headline}`}
              className="text-gray-400 hover:text-primary transition-colors"
            >
              <ExternalLink size={14} aria-hidden="true" />
            </a>
          </div>
        </div>
      </div>
    </article>
  )
}
