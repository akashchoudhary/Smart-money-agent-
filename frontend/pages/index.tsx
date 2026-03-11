import React, { useState } from 'react'
import useSWR from 'swr'
import { fetchSignals, fetchAlerts, exportUrls, scoreColor, scoreLabel, fmtMoney, fmtMarketCap } from '../lib/api'
import SignalsTable from '../components/SignalsTable'
import GammaRadar from '../components/GammaRadar'
import DarkPoolFeed from '../components/DarkPoolFeed'
import OptionsFlowTape from '../components/OptionsFlowTape'
import AIBreakoutSignals from '../components/AIBreakoutSignals'
import { Download, AlertTriangle, TrendingUp, BarChart2, Layers } from 'lucide-react'

export default function Dashboard() {
  const [minScore, setMinScore] = useState(0)
  const [signalFilter, setSignalFilter] = useState('')

  const { data: signals = [], isLoading } = useSWR(
    ['signals', minScore, signalFilter],
    () => fetchSignals(minScore || undefined, signalFilter || undefined),
    { refreshInterval: 30000 }
  )

  const explosive = signals.filter(s => s.score >= 85)
  const strong = signals.filter(s => s.score >= 70 && s.score < 85)
  const bullish = signals.filter(s => s.signal === 'bullish')

  const statCards = [
    { label: 'Tracked Tickers', value: signals.length, color: '#3b82f6', icon: BarChart2 },
    { label: 'Explosive Setups', value: explosive.length, color: '#00d084', icon: TrendingUp },
    { label: 'Strong Positioning', value: strong.length, color: '#f97316', icon: TrendingUp },
    { label: 'Bullish Signals', value: bullish.length, color: '#00d084', icon: AlertTriangle },
  ]

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
      <SignalsTable signals={signals} loading={isLoading} />

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
