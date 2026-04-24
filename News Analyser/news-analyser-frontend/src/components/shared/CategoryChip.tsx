import { cn } from '@/lib/utils'
import type { Category } from '@/features/news/types'

interface CategoryChipProps {
  category: Category
  selected?: boolean
  onClick?: () => void
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function CategoryChip({
  category,
  selected = false,
  onClick,
  size = 'md',
  className,
}: CategoryChipProps) {
  const sizes = {
    sm: 'px-2.5 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base',
  }

  return (
    <button
      type="button"
      role={onClick ? 'checkbox' : undefined}
      aria-checked={onClick ? selected : undefined}
      onClick={onClick}
      style={
        selected
          ? { backgroundColor: category.lightBgColor, borderColor: category.accentColor, color: category.accentColor }
          : undefined
      }
      className={cn(
        'inline-flex items-center rounded-full border font-medium transition-all duration-150',
        sizes[size],
        selected
          ? 'shadow-sm'
          : 'bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-200',
        onClick && 'cursor-pointer',
        className
      )}
    >
      {category.name}
    </button>
  )
}
