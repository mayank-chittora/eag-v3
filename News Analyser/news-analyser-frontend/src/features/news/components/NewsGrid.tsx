import { NewsCard } from '@/components/shared/NewsCard'
import { SkeletonCard } from '@/components/shared/SkeletonCard'
import { EmptyState } from '@/components/shared/EmptyState'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import type { NewsArticle, PageMeta } from '../types'

interface NewsGridProps {
  articles: NewsArticle[]
  isLoading: boolean
  isError: boolean
  error?: Error | null
  meta?: PageMeta
  onLoadMore?: () => void
  isLoadingMore?: boolean
}

export function NewsGrid({
  articles,
  isLoading,
  isError,
  error,
  meta,
  onLoadMore,
  isLoadingMore,
}: NewsGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
        <SkeletonCard count={8} />
      </div>
    )
  }

  if (isError) {
    return <Alert variant="error">{error?.message ?? 'Failed to load news.'}</Alert>
  }

  if (articles.length === 0) {
    return (
      <EmptyState message="Nothing here yet — try broadening your filters." />
    )
  }

  const hasMore = meta && meta.page < meta.totalPages - 1

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
        {articles.map((article) => (
          <NewsCard key={article.id} article={article} />
        ))}
        {isLoadingMore && <SkeletonCard count={4} />}
      </div>

      {hasMore && onLoadMore && (
        <div className="flex justify-center pt-2">
          <Button variant="outline" onClick={onLoadMore} loading={isLoadingMore}>
            Load more articles
          </Button>
        </div>
      )}

      {meta && (
        <p className="text-center text-xs text-gray-400">
          Showing {articles.length} of {meta.total.toLocaleString()} articles
        </p>
      )}
    </div>
  )
}
