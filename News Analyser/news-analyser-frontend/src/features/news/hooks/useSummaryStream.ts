import { useState, useRef, useCallback } from 'react'
import { format } from 'date-fns'
import { openSummaryStream } from '../services/summaryService'
import type { SseEvent, SummaryState } from '../types'

const INITIAL_STATE: SummaryState = {
  phase: 'idle',
  statusMessage: '',
  summaryText: '',
  marketText: '',
  errorMessage: '',
  articleCount: 0,
}

type ActiveSection = 'summary' | 'market'

export function useSummaryStream() {
  const [state, setState] = useState<SummaryState>(INITIAL_STATE)
  const cleanupRef = useRef<(() => void) | null>(null)
  const activeSectionRef = useRef<ActiveSection>('summary')

  const start = useCallback((categories: string[], date: Date) => {
    cleanupRef.current?.()

    setState({ ...INITIAL_STATE, phase: 'loading', statusMessage: 'Starting...' })
    activeSectionRef.current = 'summary'

    const dateStr = format(date, 'yyyy-MM-dd')

    const cleanup = openSummaryStream({
      categories,
      date: dateStr,
      onEvent: (event: SseEvent) => {
        setState((prev) => {
          switch (event.type) {
            case 'thinking':
              return { ...prev, phase: 'streaming', statusMessage: event.content }

            case 'tool_call': {
              const labels: Record<string, string> = {
                fetch_daily_news: 'Fetching news...',
                create_news_summary: 'Generating Summary...',
                analyze_market_impact: 'Analysing stock market trends...',
              }
              return { ...prev, statusMessage: labels[event.toolName ?? ''] ?? `${event.toolName}...` }
            }

            case 'tool_result': {
              if (event.toolName === 'fetch_daily_news') {
                return { ...prev, articleCount: event.articleCount ?? 0, statusMessage: event.content ?? '' }
              }
              if (event.toolName === 'create_news_summary') {
                activeSectionRef.current = 'market'
                return { ...prev, statusMessage: 'Analysing market impact...' }
              }
              if (event.toolName === 'analyze_market_impact') {
                return { ...prev, statusMessage: 'Finalising...' }
              }
              return prev
            }

            case 'text_chunk': {
              const section = activeSectionRef.current
              if (section === 'summary') {
                return { ...prev, summaryText: prev.summaryText + event.content }
              } else {
                return { ...prev, marketText: prev.marketText + event.content }
              }
            }

            case 'done':
              return { ...prev, phase: 'done', statusMessage: 'Done' }

            case 'error':
              return { ...prev, phase: 'error', errorMessage: event.content }

            default:
              return prev
          }
        })
      },
      onError: () => {
        setState((prev) => ({
          ...prev,
          phase: 'error',
          errorMessage: 'Connection lost. Please try again.',
        }))
      },
    })

    cleanupRef.current = cleanup
  }, [])

  const reset = useCallback(() => {
    cleanupRef.current?.()
    setState(INITIAL_STATE)
  }, [])

  return { state, start, reset }
}
