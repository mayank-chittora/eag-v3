import { Filter } from 'lucide-react'
import { CategoryChip } from '@/components/shared/CategoryChip'
import { useCategories } from '@/features/categories/components/useCategories'
import type { SentimentLabel } from '../types'

interface NewsFilterBarProps {
  selectedCategories: string[]
  selectedSentiment: SentimentLabel | ''
  onCategoryToggle: (slug: string) => void
  onSentimentChange: (sentiment: SentimentLabel | '') => void
}

const SENTIMENT_OPTIONS: { value: SentimentLabel | ''; label: string }[] = [
  { value: '', label: 'All Sentiments' },
  { value: 'POSITIVE', label: '● Positive' },
  { value: 'NEGATIVE', label: '● Negative' },
  { value: 'NEUTRAL',  label: '● Neutral' },
]

export function NewsFilterBar({
  selectedCategories,
  selectedSentiment,
  onCategoryToggle,
  onSentimentChange,
}: NewsFilterBarProps) {
  const { data: categories, isLoading } = useCategories()

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
      <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
        <Filter size={14} aria-hidden="true" />
        Filters
      </div>

      {/* Sentiment filter */}
      <div>
        <label htmlFor="sentiment-filter" className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-2 block">
          Sentiment
        </label>
        <select
          id="sentiment-filter"
          value={selectedSentiment}
          onChange={(e) => onSentimentChange(e.target.value as SentimentLabel | '')}
          className="w-full border border-gray-200 rounded-md px-3 py-1.5 text-sm text-gray-700 bg-white focus:ring-2 focus:ring-primary focus:border-primary outline-none"
        >
          {SENTIMENT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      {/* Category filter */}
      <div>
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-2">
          Categories {selectedCategories.length > 0 && `(${selectedCategories.length})`}
        </p>
        {isLoading ? (
          <div className="flex flex-wrap gap-2">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-6 w-20 bg-gray-200 rounded-full animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {categories?.map((cat) => (
              <CategoryChip
                key={cat.id}
                category={cat}
                selected={selectedCategories.includes(cat.slug)}
                onClick={() => onCategoryToggle(cat.slug)}
                size="sm"
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
