import { NavLink, Outlet } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  TrendingUp,
  DollarSign,
  FileText,
  Settings,
  Bell,
  BarChart3,
  Leaf,
} from 'lucide-react'

const navigation = [
  {
    name: 'Lending Sentiment',
    href: '/',
    icon: TrendingUp,
    description: 'Market sentiment analysis',
  },
  {
    name: 'Feedstock Prices',
    href: '/prices',
    icon: DollarSign,
    description: 'IOSCO-compliant price index',
  },
  {
    name: 'Policy & Carbon',
    href: '/policy',
    icon: FileText,
    description: 'Policy tracker & calculator',
  },
]

export function DashboardLayout() {
  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="sidebar flex flex-col">
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-border-subtle">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent">
            <Leaf size={18} className="text-background" />
          </div>
          <div>
            <h1 className="font-bold text-text-primary">ABFI.io</h1>
            <p className="text-xs text-text-muted">Intelligence Suite</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn('sidebar-item', isActive && 'active')
              }
            >
              <item.icon size={18} />
              <div>
                <span className="block text-sm font-medium">{item.name}</span>
              </div>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border-subtle">
          <button className="sidebar-item w-full">
            <Settings size={18} />
            <span className="text-sm">Settings</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {/* Header */}
        <header className="sticky top-0 z-10 flex items-center justify-between px-8 py-4 bg-background/80 backdrop-blur-sm border-b border-border-subtle">
          <div>
            <h2 className="text-xl font-semibold text-text-primary">Dashboard</h2>
            <p className="text-sm text-text-muted">
              Australian Bioenergy Market Intelligence
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button className="p-2 rounded-lg hover:bg-surface-hover transition-colors">
              <Bell size={20} className="text-text-secondary" />
            </button>
            <div className="flex items-center gap-2">
              <BarChart3 size={16} className="text-bullish" />
              <span className="text-sm font-medium">Live</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
