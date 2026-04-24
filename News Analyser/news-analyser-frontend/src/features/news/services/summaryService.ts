import type { SseEvent, SseEventType } from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080/api/v1'

const SSE_EVENT_TYPES: SseEventType[] = [
  'thinking',
  'tool_call',
  'tool_result',
  'text_chunk',
  'done',
  'error',
]

export interface SummaryStreamOptions {
  categories: string[]
  date: string
  onEvent: (event: SseEvent) => void
  onError: (err: Event) => void
}

export function openSummaryStream(options: SummaryStreamOptions): () => void {
  const params = new URLSearchParams()
  options.categories.forEach((cat) => params.append('categories', cat))
  params.set('date', options.date)

  const url = `${BASE_URL}/summary?${params.toString()}`
  const source = new EventSource(url)

  SSE_EVENT_TYPES.forEach((type) => {
    source.addEventListener(type, (e: MessageEvent) => {
      try {
        const parsed: SseEvent = JSON.parse(e.data)
        options.onEvent(parsed)
        if (type === 'done' || type === 'error') {
          source.close()
        }
      } catch {
        // malformed event — ignore
      }
    })
  })

  source.onerror = (e) => {
    source.close()
    options.onError(e)
  }

  return () => source.close()
}
