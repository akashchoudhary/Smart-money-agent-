import React, { useState, useEffect } from 'react'
import useSWR from 'swr'
import { fetchSignals, fetchAlerts, exportUrls, scoreColor, scoreLabel, fmtMoney, fmtMarketCap } from '../lib/api'
import SignalsTable from '../components/SignalsTable'
import GammaRadar from '../components/GammaRadar'
import DarkPoolFeed from '../components/DarkPoolFeed'
import OptionsFlowTape from '../components/OptionsFlowTape'
import AIBreakoutSignals from '../components/AIBreakoutSignals'
import { Download, AlertTriangle, TrendingUp, BarChart2, Search, X } from 'lucide-react'

const STORAGE_KEY = 'smp_custom_tickers'

export default function Dashboard() {
  const [minScore, setMinScore] = useState(0)
  const [signalFilter, setSignalFilter] = useState('')

  // Search bar state
  const [searchInput, setSearchInput] = useState('')
  const [pinnedTicker, setPinnedTicker] = useState<string | null>(null)

  // Custom added tickers (persisted to localStorage)
  const [customTickers, setCustomTickers] = useState<string[]>(() => {
    if (typeof window === 'undefined') return []
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { return [] }
  })

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(customTickers))
    }
  }, [customTickers])

  const { data: signals = [], isLoading } = useSWR(
    ['signals', minScore, signalFilter],
    () => fetchSignals(minScore || undefined, signalFilter || undefined),
    { refreshInterval: 30000 }
  )

  const explosive = signals.filter(s => s.score >= 85)
  const strong = signals.filter(s => s.score >= 70 && s.score < 85)
  const bullish = signals.filter(s => s.signal === 'bullish')

  const statCards = [
    { label: 'Tracked Tickers', value: signals.length + customTickers.length + (pinnedTicker ? 1 : 0), color: '#3b82f6', icon: BarChart2 },
    { label: 'Explosive Setups', value: explosive.length, color: '#00d084', icon: TrendingUp },
    { label: 'Strong Positioning', value: strong.length, color: '#f97316', icon: TrendingUp },
    { label: 'Bullish Signals', value: bullish.length, color: '#00d084', icon: AlertTriangle },
  ]

  const handleSearch = () => {
    const t = searchInput.trim().toUpperCase()
    if (!t) return
    setPinnedTicker(t)
    setSearchInput('')
  }

  const handleAddTicker = (ticker: string) => {
    if (!customTickers.includes(ticker) && ticker !== pinnedTicker) {
      setCustomTickers(prev => [...prev, ticker])
    }
  }

  const handleRemoveTicker = (ticker: string) => {
    setCustomTickers(prev => prev.filter(t => t !== ticker))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Smart Money Dashboard</h1>
          <p className="text-sm mt-1" style={{ color: '#64748b' }}>
            Institutional flow • Options activity • Dark pool • AI signals
          </p>
        </div>
        <div className="flex gap-2">
          <a href={exportUrls.csv} target="_blank" rel="noreferrer"
            className="flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg transition-all hover:text-white"
            style={{ background: '#141c2e', color: '#64748b', border: '1px solid #1e2d45' }}>
            <Download className="w-3.5 h-3.5" /> CSV
          </a>
          <a href={exportUrls.excel} target="_blank" rel="noreferrer"
            className="flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg transition-all hover:text-white"
            style={{ background: '#141c2e', color: '#64748b', border: '1px solid #1e2d45' }}>
            <Download className="w-3.5 h-3.5" /> Excel
          </a>
          <a href={exportUrls.json} target="_blank" rel="noreferrer"
            className="flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg transition-all hover:text-white"
            style={{ background: '#141c2e', color: '#64748b', border: '1px solid #1e2d45' }}>
            <Download className="w-3.5 h-3.5" /> JSON
          </a>
        </div>
      </div>

      {/* Search bar */}
      <div className="glass-card p-4">
        <div className="flex items-center gap-3">
          <Search className="w-4 h-4 shrink-0" style={{ color: '#64748b' }} />
          <input
            value={searchInput}
            onChange={e => setSearchInput(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="Search ticker — e.g. NVDA, AAPL, TSLA…"
            maxLength={8}
            className="flex-1 bg-transparent text-sm uppercase outline-none"
            style={{ color: '#e2e8f0' }}
          />
          {searchInput && (
            <button onClick={() => setSearchInput('')} style={{ color: '#64748b' }}>
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={handleSearch}
            disabled={!searchInput.trim()}
            className="text-xs px-4 py-1.5 rounded-lg font-bold transition-all disabled:opacity-40"
            style={{ background: '#3b82f6', color: '#fff' }}>
            Search
          </button>
        </div>
        {pinnedTicker && (
          <div className="mt-2 flex items-center gap-2 text-xs" style={{ color: '#64748b' }}>
            <span>Showing</span>
            <span className="font-bold px-1.5 py-0.5 rounded" style={{ background: '#3b82f620', color: '#3b82f6' }}>
              {pinnedTicker}
            </span>
            <span>at the top of the list</span>
            <button onClick={() => setPinnedTicker(null)} className="ml-1 hover:text-red-400 transition-colors">
              <X className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map(({ label, value, color, icon: Icon }) => (
          <div key={label} className="glass-card p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center"
              style={{ background: `${color}20` }}>
              <Icon className="w-5 h-5" style={{ color }} />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{value}</div>
              <div className="text-xs" style={{ color: '#64748b' }}>{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2">
          <label className="text-xs" style={{ color: '#64748b' }}>Min Score:</label>
          <select
            value={minScore}
            onChange={e => setMinScore(Number(e.target.value))}
            className="text-xs px-2 py-1.5 rounded-lg"
            style={{ background: '#141c2e', color: '#e2e8f0', border: '1px solid #1e2d45' }}>
            <option value={0}>All</option>
            <option value={40}>40+ Accumulation</option>
            <option value={70}>70+ Strong</option>
            <option value={85}>85+ Explosive</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs" style={{ color: '#64748b' }}>Signal:</label>
          <select
            value={signalFilter}
            onChange={e => setSignalFilter(e.target.value)}
            className="text-xs px-2 py-1.5 rounded-lg"
            style={{ background: '#141c2e', color: '#e2e8f0', border: '1px solid #1e2d45' }}>
            <option value="">All</option>
            <option value="bullish">Bullish</option>
            <option value="bearish">Bearish</option>
            <option value="neutral">Neutral</option>
          </select>
        </div>
      </div>

      {/* Main signals table */}
      <SignalsTable
        signals={signals}
        loading={isLoading}
        customTickers={customTickers}
        pinnedTicker={pinnedTicker}
        onAddTicker={handleAddTicker}
        onRemoveTicker={handleRemoveTicker}
        onClearPin={() => setPinnedTicker(null)}
      />

      {/* Widget row */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4" style={{ minHeight: 360 }}>
        <div className="xl:col-span-1"><GammaRadar /></div>
        <div className="xl:col-span-1"><DarkPoolFeed /></div>
        <div className="xl:col-span-1"><OptionsFlowTape /></div>
        <div className="xl:col-span-1"><AIBreakoutSignals /></div>
      </div>
    </div>
  )
}
