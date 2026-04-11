import { Outlet } from 'react-router-dom'
import { NavBar } from './NavBar'

export function PageWrapper() {
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <NavBar />
      <main id="main-content" className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>
      <footer className="border-t border-gray-200 bg-white py-4 text-center text-xs text-gray-400">
        © {new Date().getFullYear()} News Analyser · Stay informed, stay ahead.
      </footer>
    </div>
  )
}
