# News Analyser — Frontend Development Rules

## 1. Project Structure

Use a strict **feature-based** folder layout. Never place business logic in `pages/` or `components/`.

```
news-analyser-frontend/
├── public/
│   ├── favicon.svg
│   └── robots.txt
├── src/
│   ├── app/
│   │   ├── store.ts                  # Zustand store root (re-exports all stores)
│   │   ├── router.tsx                # React Router v6 route definitions
│   │   ├── queryClient.ts            # TanStack Query client config
│   │   └── App.tsx                   # Root component, providers wrapper
│   ├── assets/
│   │   ├── icons/                    # SVG icons not in Lucide
│   │   └── images/                   # Static images, logo
│   ├── components/
│   │   ├── ui/                       # Primitives: Button, Badge, Input, Spinner, Alert
│   │   ├── layout/                   # NavBar, Sidebar, Footer, PageWrapper
│   │   └── shared/                   # Cross-feature: SentimentBadge, CategoryChip,
│   │                                 #   NewsCard, SkeletonCard, EmptyState
│   ├── features/
│   │   ├── news/
│   │   │   ├── components/           # NewsGrid, NewsFilter, NewsCardDetailed
│   │   │   ├── hooks/                # useNews.ts, useNewsFilter.ts
│   │   │   ├── services/             # newsService.ts (all API calls for news)
│   │   │   ├── store/                # newsStore.ts (Zustand slice)
│   │   │   └── types.ts              # NewsArticle, NewsFilter, PaginatedNews TS types
│   │   ├── quiz/
│   │   │   ├── components/           # QuizCard, QuizOptions, QuizResult, QuizProgress
│   │   │   ├── hooks/                # useQuiz.ts, useQuizTimer.ts
│   │   │   ├── services/             # quizService.ts
│   │   │   ├── store/                # quizStore.ts
│   │   │   └── types.ts              # QuizQuestion, QuizSession, QuizAnswer
│   │   ├── categories/
│   │   │   ├── components/           # CategoryFilterBar, CategorySelector
│   │   │   ├── hooks/                # useCategories.ts
│   │   │   ├── services/             # categoryService.ts
│   │   │   └── types.ts              # Category
│   │   └── historical/
│   │       ├── components/           # DatePicker, HistoricalNewsFeed
│   │       ├── hooks/                # useHistoricalNews.ts
│   │       ├── services/             # historicalService.ts
│   │       └── types.ts              # HistoricalQuery
│   ├── lib/
│   │   ├── apiClient.ts              # Axios instance with base URL, interceptors
│   │   ├── utils.ts                  # cn() utility, formatDate, truncate helpers
│   │   └── constants.ts             # APP_NAME, MAX_HISTORICAL_DAYS, QUIZ_QUESTION_COUNT
│   ├── pages/
│   │   ├── InterestSelectionPage.tsx
│   │   ├── NewsFeedPage.tsx
│   │   ├── HistoricalPage.tsx
│   │   ├── QuizPage.tsx
│   │   └── QuizResultPage.tsx
│   ├── main.tsx                      # ReactDOM.createRoot entry point
│   └── index.css                     # Tailwind directives + CSS variables
├── .env.example
├── index.html
├── tailwind.config.ts
├── tsconfig.json
└── vite.config.ts
```

---

## 2. Tech Stack (Exact Versions)

| Dependency                | Version | Purpose                            |
|---------------------------|---------|------------------------------------|
| react                     | 18.x    | UI framework                       |
| react-dom                 | 18.x    | DOM rendering                      |
| typescript                | 5.x     | Type safety                        |
| vite                      | 5.x     | Build tool + dev server            |
| tailwindcss               | 3.x     | Utility-first CSS                  |
| react-router-dom          | 6.x     | Client-side routing                |
| @tanstack/react-query     | 5.x     | Server state + caching             |
| zustand                   | 4.x     | Client/UI state management         |
| axios                     | 1.x     | HTTP client                        |
| lucide-react              | latest  | Icon library                       |
| clsx + tailwind-merge     | latest  | `cn()` conditional class utility   |
| vitest                    | latest  | Unit/integration test runner       |
| @testing-library/react    | latest  | Component testing                  |
| jest-axe                  | latest  | Accessibility testing              |
| msw                       | 2.x     | API mocking in tests               |

---

## 3. Component Rules

### 3.1 General Rules
- **Always** use functional components. Never use class components.
- **Always** use TypeScript. No `.jsx` files — only `.tsx`.
- Define the props interface **before** writing JSX. Think through the interface first.
- Export components as named exports (not default exports), except for pages.
- File name = component name (PascalCase). E.g., `NewsCard.tsx` exports `NewsCard`.
- Co-locate the test file: `NewsCard.tsx` → `NewsCard.test.tsx` in the same directory.

### 3.2 Styling
- Use **TailwindCSS classes exclusively**. No inline `style={{}}` except for dynamic values
  that cannot be expressed as Tailwind classes (e.g., a computed percentage width for a progress bar).
- Use the `cn()` utility from `lib/utils.ts` for all conditional class merging. Never concatenate strings.
- Never hardcode hex colour values in JSX. Use only Tailwind's colour system or the CSS variables
  defined in `index.css` (which map to design-guidelines.md tokens).
- Keep component JSX under 80 lines. If it exceeds this, extract sub-components.

```ts
// lib/utils.ts — the cn() utility
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

### 3.3 TypeScript Rules
- No `any` types. Use `unknown` when the type is genuinely unknown, then narrow.
- All API response types must be defined in the relevant `features/*/types.ts` file.
- Use `interface` for object shapes, `type` for unions/intersections.
- Props interfaces must be named `{ComponentName}Props`. E.g., `NewsCardProps`.

---

## 4. State Management

### 4.1 Zustand — Client/UI State
Use Zustand for state that does NOT come from the server:
- Selected interest categories (user preference, persisted to localStorage)
- Selected sentiment filter
- Currently selected date (historical page)
- Quiz session state (current question index, answers)
- UI state (sidebar open/closed, theme preference)

```ts
// features/categories/store/categoriesStore.ts (example pattern)
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface CategoriesState {
  selected: string[]
  toggle: (category: string) => void
  clearAll: () => void
}

export const useCategoriesStore = create<CategoriesState>()(
  persist(
    (set) => ({
      selected: [],
      toggle: (category) =>
        set((state) => ({
          selected: state.selected.includes(category)
            ? state.selected.filter((c) => c !== category)
            : [...state.selected, category],
        })),
      clearAll: () => set({ selected: [] }),
    }),
    { name: 'news-analyser-categories' }
  )
)
```

### 4.2 TanStack Query — Server State
Use TanStack Query for all data that comes from the API.

- Every API endpoint gets its own custom hook in `features/*/hooks/`.
- Use `queryKey` factories (arrays) for consistent cache key management.
- Always specify `staleTime`:

| Query Type           | staleTime   | Rationale                                   |
|----------------------|-------------|---------------------------------------------|
| Live news feed       | 5 minutes   | News is fresh but not real-time             |
| Historical articles  | 24 hours    | Historical data never changes               |
| Categories list      | 1 hour      | Rarely changes                              |
| Quiz questions       | 0           | Always fresh — never cache quiz data        |

```ts
// features/news/hooks/useNews.ts (example pattern)
import { useQuery } from '@tanstack/react-query'
import { newsService } from '../services/newsService'
import type { NewsFilter } from '../types'

export function useNews(filter: NewsFilter) {
  return useQuery({
    queryKey: ['news', filter],
    queryFn: () => newsService.getNews(filter),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
```

---

## 5. API Communication

### 5.1 Axios Client Setup
```ts
// lib/apiClient.ts
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080/api/v1',
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor — unwrap ApiResponse<T>
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // Normalise error shape
    const message = error.response?.data?.error?.message ?? 'Unexpected error'
    return Promise.reject(new Error(message))
  }
)
```

### 5.2 API Response Contract
All backend responses follow this shape:
```ts
interface ApiResponse<T> {
  data: T
  meta?: {
    page: number
    pageSize: number
    total: number
    totalPages: number
  }
  error?: {
    code: string
    message: string
  }
}
```

### 5.3 Service Layer Rule
**Never** call `apiClient` directly from a hook or component.
All API calls must go through service functions in `features/*/services/*.ts`.

```ts
// features/news/services/newsService.ts (example pattern)
import { apiClient } from '@/lib/apiClient'
import type { NewsFilter, PaginatedNews } from '../types'

export const newsService = {
  getNews: (filter: NewsFilter): Promise<PaginatedNews> =>
    apiClient.get('/news', { params: filter }),

  getNewsByDate: (date: string, filter: NewsFilter): Promise<PaginatedNews> =>
    apiClient.get('/historical', { params: { date, ...filter } }),
}
```

---

## 6. Routing

### 6.1 Route Map
```tsx
// app/router.tsx
import { createBrowserRouter } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Spinner } from '@/components/ui/Spinner'

const InterestSelectionPage = lazy(() => import('@/pages/InterestSelectionPage'))
const NewsFeedPage = lazy(() => import('@/pages/NewsFeedPage'))
const HistoricalPage = lazy(() => import('@/pages/HistoricalPage'))
const QuizPage = lazy(() => import('@/pages/QuizPage'))
const QuizResultPage = lazy(() => import('@/pages/QuizResultPage'))

export const router = createBrowserRouter([
  {
    path: '/',
    element: <PageWrapper />,
    children: [
      { index: true, element: <Suspense fallback={<Spinner />}><InterestSelectionPage /></Suspense> },
      { path: 'news', element: <Suspense fallback={<Spinner />}><NewsFeedPage /></Suspense> },
      { path: 'historical', element: <Suspense fallback={<Spinner />}><HistoricalPage /></Suspense> },
      { path: 'quiz', element: <Suspense fallback={<Spinner />}><QuizPage /></Suspense> },
      { path: 'quiz/result', element: <Suspense fallback={<Spinner />}><QuizResultPage /></Suspense> },
    ],
  },
])
```

### 6.2 Navigation Rules
- After interest selection, navigate to `/news` (React Router `useNavigate`).
- The quiz result page receives score via React Router `state`. Never put quiz scores in the URL.
- Always use `<Link>` or `useNavigate` for internal navigation. Never use `window.location`.

---

## 7. Loading, Error & Empty States

Every data-fetching component **must** handle all three states explicitly:

```tsx
// Pattern — must be followed in every component that uses useQuery
const { data, isLoading, isError, error } = useNews(filter)

if (isLoading) return <SkeletonCard count={6} />
if (isError) return <Alert variant="error">{error.message}</Alert>
if (!data?.items.length) return <EmptyState message="No articles match your filters." />

return <NewsGrid items={data.items} />
```

Never render `undefined` or `null` without a fallback. Never show a blank screen.

---

## 8. Performance Rules

- Use `React.memo` only when profiling shows unnecessary re-renders. Do not add it speculatively.
- Use `useCallback` and `useMemo` only for stable references passed to memoised children or
  expensive computations. Do not wrap every function.
- All route-level components are code-split via `React.lazy` (see §6.1 above).
- Images: always use `loading="lazy"` on `<img>` tags below the fold.
- News source logos: use `<img>` with fixed `width`/`height` to avoid layout shift (CLS).

---

## 9. Testing Requirements

### 9.1 What to Test
- Every component in `components/ui/` and `components/shared/` requires a test.
- Every custom hook requires a test using `renderHook` from RTL.
- Every service function requires a test with MSW mocking the API.
- Page-level tests: happy path + key error state per page.

### 9.2 Test File Location
Co-locate test files next to the source file:
- `NewsCard.tsx` → `NewsCard.test.tsx`
- `useNews.ts` → `useNews.test.ts`

### 9.3 Accessibility in Tests
Every component test must include an axe accessibility check:
```ts
import { axe } from 'jest-axe'

it('has no accessibility violations', async () => {
  const { container } = render(<NewsCard {...mockProps} />)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})
```

---

## 10. Environment Variables

All environment variables must be prefixed with `VITE_` and documented in `.env.example`.

```bash
# .env.example
VITE_API_BASE_URL=http://localhost:8080/api/v1
```

Never hardcode URLs, ports, or environment-specific values in source files.

---

## 11. Code Quality Rules

- Run `eslint` and `tsc --noEmit` before marking any task done. Fix all errors.
- No `console.log` statements in committed code. Use the browser devtools or a proper logger.
- Imports: group in order — (1) React/library imports, (2) internal `@/` path imports, (3) relative imports. Blank line between groups.
- Use `@/` path aliases for all internal imports (configured in `tsconfig.json` and `vite.config.ts`).
- Named exports everywhere except page components (page components use default export for lazy loading).
