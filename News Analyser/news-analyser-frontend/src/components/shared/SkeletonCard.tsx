import { cn } from '@/lib/utils'

interface SkeletonCardProps {
  count?: number
  className?: string
}

function SingleSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('bg-white rounded-lg border border-gray-200 p-4 animate-pulse', className)}>
      <div className="h-3 bg-gray-200 rounded w-1/3 mb-3" />
      <div className="h-5 bg-gray-200 rounded w-full mb-2" />
      <div className="h-5 bg-gray-200 rounded w-3/4 mb-3" />
      <div className="h-3 bg-gray-200 rounded w-full mb-1" />
      <div className="h-3 bg-gray-200 rounded w-5/6 mb-4" />
      <div className="flex justify-between">
        <div className="h-5 bg-gray-200 rounded-full w-20" />
        <div className="h-5 bg-gray-200 rounded-full w-16" />
      </div>
    </div>
  )
}

export function SkeletonCard({ count = 6, className }: SkeletonCardProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <SingleSkeleton key={i} className={className} />
      ))}
    </>
  )
}
