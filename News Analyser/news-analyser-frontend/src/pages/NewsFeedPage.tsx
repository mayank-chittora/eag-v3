import { useState, useMemo } from 'react'
import { format, subDays, parseISO } from 'date-fns'
import { Sparkles } from 'lucide-react'
import { CategoryNewsSection } from '@/features/news/components/CategoryNewsSection'
import { SummaryDrawer } from '@/features/news/components/SummaryDrawer'
import { useCategories } from '@/features/categories/components/useCategories'
import { useCategoriesStore } from '@/features/categories/services/categoriesStore'
import { useSummaryStream } from '@/features/news/hooks/useSummaryStream'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/shared/EmptyState'
import { MAX_HISTORICAL_DAYS } from '@/lib/constants'
import type { Category, SentimentLabel } from '@/features/news/types'

export default function NewsFeedPage() {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date())
  const [selectedSentiment, setSelectedSentiment] = useState<SentimentLabel | ''>('')
  const [drawerOpen, setDrawerOpen] = useState(false)

  const { selected: selectedCategories } = useCategoriesStore()
  const { data: allCategories, isLoading } = useCategories()
  const { state: summaryState, start: startSummary } = useSummaryStream()

  const handleGenerateSummary = () => {
    const categories =
      selectedCategories.length > 0
        ? selectedCategories
        : (allCategories ?? []).map((c) => c.slug)
    setDrawerOpen(true)
    startSummary(categories, selectedDate)
  }

  const handleRegenerate = () => {
    const categories =
      selectedCategories.length > 0
        ? selectedCategories
        : (allCategories ?? []).map((c) => c.slug)
    startSummary(categories, selectedDate)
  }

  const todayStr = format(new Date(), 'yyyy-MM-dd')
  const dateStr  = format(selectedDate, 'yyyy-MM-dd')
  const isToday  = dateStr === todayStr
  const minDate  = format(subDays(new Date(), MAX_HISTORICAL_DAYS), 'yyyy-MM-dd')

  // Resolve Category objects to render
  const categoryObjects = useMemo<Category[]>(() => {
    if (!allCategories?.length) return []
    
    // If user has selected categories, show those. Otherwise, show all.
    const activeSlugs = selectedCategories.length > 0
      ? selectedCategories
      : allCategories.map(c => c.slug)
      
    return activeSlugs
      .map((slug) => allCategories.find((c) => c.slug === slug))
      .filter((c): c is Category => c !== undefined)
  }, [allCategories, selectedCategories])

  return (
    <div className="space-y-2 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
        <h1 className="text-2xl font-black font-merriweather text-gray-900 tracking-tight">
          {isToday ? "Today's News" : `News from ${format(selectedDate, 'MMM d, yyyy')}`}
        </h1>
        
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Button
            variant="primary"
            size="sm"
            onClick={handleGenerateSummary}
            disabled={isLoading}
            className="shrink-0 gap-1.5"
            aria-label="Generate AI summary for selected categories"
          >
            <Sparkles size={14} aria-hidden="true" />
            Generate Summary
          </Button>

          <select
            value={selectedSentiment}
            onChange={(e) => setSelectedSentiment(e.target.value as SentimentLabel | '')}
            className="text-sm border border-gray-200 rounded-md px-3 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary bg-white"
            aria-label="Filter by sentiment"
          >
            <option value="">All Sentiments</option>
            <option value="POSITIVE">Positive</option>
            <option value="NEUTRAL">Neutral</option>
            <option value="NEGATIVE">Negative</option>
          </select>
          
          <input
            type="date"
            value={dateStr}
            max={todayStr}
            min={minDate}
            onChange={(e) => {
              if (e.target.value) setSelectedDate(parseISO(e.target.value))
            }}
            className="text-sm border border-gray-200 rounded-md px-3 py-1.5 text-gray-700 bg-white
                       focus:outline-none focus:ring-2 focus:ring-primary"
            aria-label="Select date"
          />
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center min-h-[40vh]">
          <Spinner size={32} />
        </div>
      )}

      {!isLoading && categoryObjects.length > 0 && (
        <div className="flex flex-col gap-8">
          {categoryObjects.map((cat) => (
            <CategoryNewsSection
              key={cat.slug}
              category={cat}
              date={dateStr}
              sentiment={selectedSentiment}
              maxItems={10} 
            />
          ))}
        </div>
      )}

      {!isLoading && categoryObjects.length === 0 && (
        <EmptyState message="No categories available. Please check back later." />
      )}

      <SummaryDrawer
        isOpen={drawerOpen}
        state={summaryState}
        onClose={() => setDrawerOpen(false)}
        onRegenerate={handleRegenerate}
      />
    </div>
  )
}
