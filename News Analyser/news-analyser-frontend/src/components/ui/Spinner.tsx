import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SpinnerProps {
  size?: number
  className?: string
}

export function Spinner({ size = 24, className }: SpinnerProps) {
  return (
    <div className={cn('flex items-center justify-center p-8', className)} role="status" aria-label="Loading">
      <Loader2 size={size} className="animate-spin text-primary" aria-hidden="true" />
    </div>
  )
}
