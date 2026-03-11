import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { TrendingUp, Activity, Layers, BarChart2, Bell, Download } from 'lucide-react'

interface LayoutProps { children: React.ReactNode }

export default function Layout({ children }: LayoutProps) {
  const router = useRouter()
  const nav = [
    { href: '/', label: 'Dashboard', icon: BarChart2 },
    { href: '/?tab=options', label: 'Options Flow', icon: Activity },
    { href: '/?tab=darkpool', label: 'Dark Pool', icon: Layers },
    { href: '/?tab=ai', label: 'AI Signals', icon: TrendingUp },
  ]

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#080c14' }}>
      {/* Top nav */}
      <header style={{ background: '#0f1623', borderBottom: '1px solid #1e2d45' }}
        className="sticky top-0 z-50 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg,#3b82f6,#8b5cf6)' }}>
            <TrendingUp className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-lg tracking-wide text-white">
            SMART MONEY
            <span className="text-blue-400 ml-1">INTELLIGENCE</span>
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full ml-2"
            style={{ background: '#1e2d45', color: '#64748b' }}>BETA</span>
        </div>

        <nav className="hidden md:flex items-center gap-1">
          {nav.map(({ href, label, icon: Icon }) => {
            const active = router.asPath === href
            return (
              <Link key={href} href={href}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all ${
                  active ? 'bg-blue-600/20 text-blue-400' : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}>
                <Icon className="w-3.5 h-3.5" />
                {label}
              </Link>
            )
          })}
        </nav>

        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs" style={{ color: '#00d084' }}>
            <span className="live-dot" />
            LIVE
          </span>
          <a href="http://localhost:8000/export/csv" target="_blank" rel="noreferrer"
            className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg transition-all"
            style={{ background: '#1e2d45', color: '#94a3b8' }}>
            <Download className="w-3 h-3" />
            Export
          </a>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1 px-4 py-6 max-w-screen-2xl mx-auto w-full">
        {children}
      </main>

      <footer className="text-center py-4 text-xs" style={{ color: '#1e2d45' }}>
        Smart Money Intelligence Platform — For educational purposes only. Not financial advice.
      </footer>
    </div>
  )
}
