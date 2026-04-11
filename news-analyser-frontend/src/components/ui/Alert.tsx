import { AlertCircle, CheckCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AlertProps {
  variant?: 'error' | 'success' | 'info'
  children: React.ReactNode
  className?: string
}

const variants = {
  error:   { bg: 'bg-red-50 border-red-200 text-red-800',   icon: AlertCircle },
  success: { bg: 'bg-green-50 border-green-200 text-green-800', icon: CheckCircle },
  info:    { bg: 'bg-blue-50 border-blue-200 text-blue-800', icon: Info },
}

export function Alert({ variant = 'error', children, className }: AlertProps) {
  const { bg, icon: Icon } = variants[variant]
  return (
    <div role="alert" className={cn('flex items-start gap-3 rounded-lg border p-4 text-sm', bg, className)}>
      <Icon size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
      <span>{children}</span>
    </div>
  )
}
