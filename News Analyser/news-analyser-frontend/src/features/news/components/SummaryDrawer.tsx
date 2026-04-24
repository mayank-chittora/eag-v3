import { useEffect, useRef } from 'react'
import { X, Loader2, CheckCircle2, AlertCircle, Newspaper, TrendingUp, Zap } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'
import type { SummaryState } from '../types'

interface SummaryDrawerProps {
  isOpen: boolean
  state: SummaryState
  onClose: () => void
  onRegenerate: () => void
}

function StatusBar({
  phase,
  statusMessage,
  articleCount,
}: Pick<SummaryState, 'phase' | 'statusMessage' | 'articleCount'>) {
  if (phase === 'idle') return null
  const isActive = phase === 'loading' || phase === 'streaming'
  return (
    <div
      className={cn(
        'flex items-center gap-2 px-3 py-2 text-xs font-medium rounded-md',
        isActive && 'bg-blue-50 text-blue-700',
        phase === 'done' && 'bg-green-50 text-green-700',
        phase === 'error' && 'bg-red-50 text-red-700'
      )}
    >
      {isActive && <Loader2 size={12} className="animate-spin shrink-0" aria-hidden="true" />}
      {phase === 'done' && <CheckCircle2 size={12} className="shrink-0" aria-hidden="true" />}
      {phase === 'error' && <AlertCircle size={12} className="shrink-0" aria-hidden="true" />}
      <span className="truncate">{statusMessage}</span>
      {articleCount > 0 && phase !== 'error' && (
        <span className="ml-auto shrink-0 text-gray-400">{articleCount} articles</span>
      )}
    </div>
  )
}

function TypingCursor() {
  return (
    <span
      className="inline-block w-0.5 h-4 bg-blue-600 ml-0.5 align-middle animate-pulse"
      aria-hidden="true"
    />
  )
}

function MarkdownSection({
  title,
  icon,
  content,
  showCursor,
}: {
  title: string
  icon: React.ReactNode
  content: string
  showCursor: boolean
}) {
  if (!content) return null
  return (
    <section aria-label={title}>
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
      </div>
      <div className="text-sm text-gray-700 leading-relaxed">
        <ReactMarkdown
          components={{
            h2: ({ children }) => (
              <p className="font-semibold text-gray-800 mt-4 mb-1">{children}</p>
            ),
            h3: ({ children }) => (
              <p className="font-medium text-gray-800 mt-3 mb-1">{children}</p>
            ),
            strong: ({ children }) => (
              <strong className="font-semibold text-gray-900">{children}</strong>
            ),
            ul: ({ children }) => <ul className="list-disc pl-4 space-y-1 my-2">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal pl-4 space-y-1 my-2">{children}</ol>,
            li: ({ children }) => <li className="text-sm">{children}</li>,
            p: ({ children }) => <p className="mb-2">{children}</p>,
            hr: () => <hr className="my-4 border-gray-100" />,
          }}
        >
          {content}
        </ReactMarkdown>
        {showCursor && <TypingCursor />}
      </div>
    </section>
  )
}

export function SummaryDrawer({ isOpen, state, onClose, onRegenerate }: SummaryDrawerProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const { phase, statusMessage, summaryText, marketText, errorMessage, articleCount } = state
  const isStreaming = phase === 'streaming' || phase === 'loading'

  useEffect(() => {
    if (scrollRef.current && isStreaming) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [summaryText, marketText, isStreaming])

  useEffect(() => {
    if (!isOpen) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const showSummaryCursor = isStreaming && !!summaryText && !marketText
  const showMarketCursor = isStreaming && !!marketText

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      <aside
        role="complementary"
        aria-label="AI News Summary"
        className={cn(
          'fixed top-0 right-0 z-50 h-full w-full sm:w-[520px] lg:w-[600px]',
          'bg-white shadow-xl flex flex-col',
          'transition-transform duration-300 ease-in-out',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 shrink-0">
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-blue-600" aria-hidden="true" />
            <h1 className="text-sm font-semibold text-gray-900">AI News Summary</h1>
          </div>
          <div className="flex items-center gap-1">
            {phase === 'done' && (
              <button
                onClick={onRegenerate}
                className="text-xs text-blue-600 hover:text-blue-700 font-medium px-3 py-1.5 rounded-md hover:bg-blue-50 transition-colors"
              >
                Regenerate
              </button>
            )}
            <button
              onClick={onClose}
              aria-label="Close summary panel"
              className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
        </div>

        {/* Status bar */}
        <div className="px-5 pt-3 pb-1 shrink-0">
          <StatusBar phase={phase} statusMessage={statusMessage} articleCount={articleCount} />
        </div>

        {/* Scrollable content */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-4 space-y-6">
          {/* Skeleton while loading */}
          {isStreaming && !summaryText && (
            <div className="space-y-3 animate-pulse" aria-label="Loading summary">
              <div className="h-4 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-full" />
              <div className="h-4 bg-gray-200 rounded w-5/6" />
              <div className="h-4 bg-gray-200 rounded w-full" />
              <div className="h-4 bg-gray-200 rounded w-2/3" />
            </div>
          )}

          {/* Error state */}
          {phase === 'error' && (
            <div className="flex flex-col items-center gap-3 py-12 text-center">
              <AlertCircle size={32} className="text-red-400" aria-hidden="true" />
              <p className="text-sm text-gray-600">{errorMessage}</p>
              <button
                onClick={onRegenerate}
                className="text-sm text-blue-600 hover:underline font-medium"
              >
                Try again
              </button>
            </div>
          )}

          <MarkdownSection
            title="Today's News Summary"
            icon={<Newspaper size={14} className="text-blue-600" aria-hidden="true" />}
            content={summaryText}
            showCursor={showSummaryCursor}
          />

          {summaryText && marketText && <hr className="border-gray-100" />}

          <MarkdownSection
            title="Market Impact Analysis"
            icon={<TrendingUp size={14} className="text-green-600" aria-hidden="true" />}
            content={marketText}
            showCursor={showMarketCursor}
          />
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-gray-100 shrink-0">
          <p className="text-xs text-gray-400 text-center">
            Powered by Gemini 2.5 Flash · Analysis may not reflect actual market outcomes
          </p>
        </div>
      </aside>
    </>
  )
}
