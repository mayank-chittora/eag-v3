import { useNews } from '../hooks/useNews'
import { NewsCard } from '@/components/shared/NewsCard'
import { SkeletonCard } from '@/components/shared/SkeletonCard'
import type { Category, SentimentLabel } from '../types'

interface CategoryNewsSectionProps {
  category: Category
  date: string
  sentiment: SentimentLabel | ''
  maxItems?: number
}

export function CategoryNewsSection({ category, date, sentiment, maxItems = 10 }: CategoryNewsSectionProps) {
  // Use useNews with specific category filter and date/sentiment
  const { data, isLoading, isError } = useNews({
    categories: [category.slug],
    date,
    sentiment,
    pageSize: maxItems,
  })

  // We extract the array of articles or default to empty
  const articles = data?.data ?? []

  if (isError) return null // Hide category if fetch fails silently

  return (
    <section aria-labelledby={`cat-${category.slug}`} className="animate-in fade-in slide-in-from-bottom-2 duration-500 ease-out">
      <div className="flex items-center justify-between mb-4 mt-8">
        <h2
          id={`cat-${category.slug}`}
          className="text-xl font-bold text-gray-900 flex items-center gap-3"
        >
          <span
            className="w-3 h-3 rounded-full shrink-0 shadow-sm"
            style={{ backgroundColor: category.accentColor }}
            aria-hidden="true"
          />
          {category.name}
        </h2>
      </div>

      {isLoading ? (
        <div className="flex overflow-x-auto snap-x snap-mandatory space-x-4 pb-4 no-scrollbar">
          {/* Skeleton placeholders */}
          <div className="flex gap-4 min-w-max">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="snap-start w-80 shrink-0">
                <SkeletonCard count={1} />
              </div>
            ))}
          </div>
        </div>
      ) : articles.length === 0 ? (
        <div className="text-sm text-gray-500 italic py-4 rounded-md bg-gray-50 text-center border border-dashed border-gray-200">
          No news available for {category.name} on this date.
        </div>
      ) : (
        <div className="flex overflow-x-auto snap-x snap-mandatory space-x-4 pb-4 no-scrollbar">
          {articles.map((article) => (
             <div key={article.id} className="snap-start w-80 sm:w-96 shrink-0 transition-transform duration-300 hover:-translate-y-1">
               <NewsCard article={article} className="h-full" />
             </div>
          ))}
        </div>
      )}
    </section>
  )
}
