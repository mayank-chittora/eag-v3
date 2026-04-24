import { Newspaper } from 'lucide-react'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  message?: string
  icon?: React.ReactNode
  action?: React.ReactNode
  className?: string
}

export function EmptyState({
  message = 'No articles found.',
  icon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'col-span-full flex flex-col items-center justify-center py-16 text-center',
        className
      )}
    >
      <div className="text-gray-300 mb-4">
        {icon ?? <Newspaper size={48} aria-hidden="true" />}
      </div>
      <p className="text-gray-500 text-sm max-w-xs">{message}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
