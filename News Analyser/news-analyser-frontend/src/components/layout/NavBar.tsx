import { useNavigate } from 'react-router-dom'
import { Newspaper } from 'lucide-react'
import { cn } from '@/lib/utils'
import { APP_NAME } from '@/lib/constants'

export function NavBar() {
  const navigate = useNavigate()

  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-sm border-b border-gray-200">
      <nav
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-14"
        aria-label="Main navigation"
      >
        {/* Logo */}
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 font-semibold text-gray-900 hover:text-primary transition-colors"
          aria-label="Go to home"
        >
          <Newspaper size={20} className="text-primary" aria-hidden="true" />
          <span>{APP_NAME}</span>
        </button>

      </nav>
    </header>
  )
}
