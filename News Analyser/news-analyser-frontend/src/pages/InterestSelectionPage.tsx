import { useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { CategoryChip } from '@/components/shared/CategoryChip'
import { Spinner } from '@/components/ui/Spinner'
import { Alert } from '@/components/ui/Alert'
import { useCategories } from '@/features/categories/components/useCategories'
import { useCategoriesStore } from '@/features/categories/services/categoriesStore'
import { useNewsStore } from '@/features/news/store/newsStore'

export default function InterestSelectionPage() {
  const navigate = useNavigate()
  const { data: categories, isLoading, isError, error } = useCategories()
  const { selected, toggle, setAll, clearAll } = useCategoriesStore()
  const { setCategories } = useNewsStore()

  const handleProceed = () => {
    setCategories(selected)
    navigate('/news')
  }

  const handleSelectAll = () => {
    if (categories) {
      setAll(categories.map((c) => c.slug))
    }
  }

  return (
    <div className="max-w-3xl mx-auto py-8 space-y-8">
      {/* Hero */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 bg-primary-light text-primary rounded-full px-4 py-1.5 text-sm font-medium">
          <Sparkles size={14} aria-hidden="true" />
          Personalise your news feed
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
          What topics interest you?
        </h1>
        <p className="text-gray-500 text-base max-w-md mx-auto">
          Select one or more categories to tailor your daily news highlights — covering markets,
          politics, sports, and more.
        </p>
      </div>

      {/* Category grid */}
      {isLoading && <Spinner />}
      {isError && <Alert variant="error">{(error as Error)?.message ?? 'Failed to load categories.'}</Alert>}

      {categories && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500">
              {selected.length > 0 ? `${selected.length} selected` : 'Select at least one'}
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleSelectAll}
                className="text-xs text-primary hover:underline"
              >
                Select all
              </button>
              {selected.length > 0 && (
                <>
                  <span className="text-gray-300">·</span>
                  <button onClick={clearAll} className="text-xs text-gray-500 hover:underline">
                    Clear
                  </button>
                </>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {categories.map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={() => toggle(cat.slug)}
                aria-pressed={selected.includes(cat.slug)}
                style={
                  selected.includes(cat.slug)
                    ? { backgroundColor: cat.lightBgColor, borderColor: cat.accentColor }
                    : undefined
                }
                className={`
                  flex items-center justify-center py-4 px-3 rounded-xl border-2 font-medium text-sm
                  transition-all duration-150 cursor-pointer text-center
                  ${selected.includes(cat.slug)
                    ? 'shadow-sm'
                    : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                  }
                `}
              >
                <span style={selected.includes(cat.slug) ? { color: cat.accentColor } : undefined}>
                  {cat.name}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* CTA */}
      <div className="flex justify-center pt-4">
        <Button
          size="lg"
          onClick={handleProceed}
          disabled={selected.length === 0}
          className="min-w-48"
        >
          Show me today's news →
        </Button>
      </div>
    </div>
  )
}
