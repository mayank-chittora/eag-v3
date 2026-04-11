import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, parseISO, formatDistanceToNow } from 'date-fns'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateStr: string | Date): string {
  const date = typeof dateStr === 'string' ? parseISO(dateStr) : dateStr
  return format(date, 'MMM d, yyyy')
}

export function formatRelativeTime(dateStr: string | Date): string {
  const date = typeof dateStr === 'string' ? parseISO(dateStr) : dateStr
  return formatDistanceToNow(date, { addSuffix: true })
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength).trim() + '…'
}

export function slugToLabel(slug: string): string {
  return slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}
