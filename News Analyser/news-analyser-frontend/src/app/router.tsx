import { createBrowserRouter } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Spinner } from '@/components/ui/Spinner'

const InterestSelectionPage = lazy(() => import('@/pages/InterestSelectionPage'))
const NewsFeedPage           = lazy(() => import('@/pages/NewsFeedPage'))

function Fallback() {
  return <Spinner size={32} className="min-h-[40vh]" />
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <PageWrapper />,
    children: [
      { index: true, element: <Suspense fallback={<Fallback />}><InterestSelectionPage /></Suspense> },
      { path: 'news', element: <Suspense fallback={<Fallback />}><NewsFeedPage /></Suspense> },
    ],
  },
])
