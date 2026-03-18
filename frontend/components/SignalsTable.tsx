import React, { useState } from 'react'
import Link from 'next/link'
import useSWR from 'swr'
import { ChevronUp, ChevronDown, Plus, X, Pin } from 'lucide-react'
import { SignalResponse, scoreColor, scoreLabel, fmtMoney, fmtMarketCap, fetchStock, stockDetailToSignal } from '../lib/api'

interface Props {
  signals: SignalResponse[]
  loading?: boolean
  customTickers: string[]
  pinnedTicker: string | null
  onAddTicker: (ticker: string) => void
  onRemoveTicker: (ticker: string) => void
  onClearPin: () => void
}

type SortKey = keyof Pick<SignalResponse, 'score' | 'breakout_probability' | 'dark_pool_flow' | 'options_flow_score' | 'gamma_score' | 'price'>

const ScoreBadge = ({ score }: { score: number }) => (
  <span className="font-bold text-base" style={{ color: scoreColor(score) }}>
    {score.toFixed(1)}
  </span>
)

const MiniBar = ({ value, color = '#3b82f6' }: { value: number; color?: string }) => (
  <div className="flex items-center gap-1.5">
    <div className="w-16 rounded-full h-1.5" style={{ background: '#1e2d45' }}>
      <div className="h-1.5 rounded-full transition-all"
        style={{ width: `${Math.min(100, value)}%`, background: color }} />
    </div>
    <span className="text-xs" style={{ color: '#64748b' }}>{value.toFixed(0)}</span>
  </div>
)

function SignalRow({ s, idx, badge, onRemove }: {
  s: SignalResponse
  idx: number | string
  badge?: React.ReactNode
  onRemove?: () => void
}) {
  return (
    <tr className="border-b transition-colors" style={{ borderColor: '#1e2d45' }}>
      <td className="px-4 py-3 text-xs" style={{ color: '#1e2d45' }}>{idx}</td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1.5">
          <Link href={`/stocks/${s.ticker}`} className="ticker-badge hover:text-white transition-colors">
            {s.ticker}
          </Link>
          {badge}
          {onRemove && (
            <button onClick={onRemove} className="ml-auto text-slate-600 hover:text-red-400 transition-colors">
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </td>
      <td className="px-4 py-3 text-white font-medium">
        ${s.price.toFixed(2)}
        <span className={`ml-1.5 text-xs ${s.change_pct >= 0 ? 'bull' : 'bear'}`}>
          {s.change_pct >= 0 ? '+' : ''}{s.change_pct.toFixed(2)}%
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex flex-col">
          <ScoreBadge score={s.score} />
          <span className="text-xs mt-0.5" style={{ color: scoreColor(s.score), opacity: 0.7 }}>
            {scoreLabel(s.score)}
          </span>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className={`text-xs font-bold px-2 py-0.5 rounded ${
          s.signal === 'bullish' ? 'bg-green-900/40 text-green-400' :
          s.signal === 'bearish' ? 'bg-red-900/40 text-red-400' :
          'bg-slate-800 text-slate-400'
        }`}>
          {s.signal.toUpperCase()}
        </span>
      </td>
      <td className="px-4 py-3"><MiniBar value={s.options_flow_score} color="#3b82f6" /></td>
      <td className="px-4 py-3"><MiniBar value={s.gamma_score} color="#8b5cf6" /></td>
      <td className="px-4 py-3 text-xs" style={{ color: s.dark_pool_flow > 5e6 ? '#00d084' : '#64748b' }}>
        {fmtMoney(s.dark_pool_flow)}
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1.5">
          <div className="w-20 rounded-full h-1.5" style={{ background: '#1e2d45' }}>
            <div className="h-1.5 rounded-full"
              style={{
                width: `${s.breakout_probability * 100}%`,
                background: `hsl(${s.breakout_probability * 120},70%,50%)`
              }} />
          </div>
          <span className="text-xs font-bold" style={{ color: `hsl(${s.breakout_probability * 120},70%,60%)` }}>
            {(s.breakout_probability * 100).toFixed(0)}%
          </span>
        </div>
      </td>
      <td className="px-4 py-3 text-xs" style={{ color: '#64748b' }}>
        {fmtMarketCap(s.market_cap)}
      </td>
    </tr>
  )
}

function FetchedRow({ ticker, idx, badge, onRemove }: {
  ticker: string
  idx: number | string
  badge?: React.ReactNode
  onRemove?: () => void
}) {
  const { data, isLoading, error } = useSWR(
    `stock-custom-${ticker}`,
    () => fetchStock(ticker).then(stockDetailToSignal),
    { refreshInterval: 30000 }
  )

  if (isLoading) {
    return (
      <tr className="border-b" style={{ borderColor: '#1e2d45' }}>
        <td className="px-4 py-3 text-xs" style={{ color: '#1e2d45' }}>{idx}</td>
        <td className="px-4 py-3" colSpan={9}>
          <div className="flex items-center gap-2">
            <span className="ticker-badge">{ticker}</span>
            <span className="text-xs animate-pulse" style={{ color: '#64748b' }}>Fetching…</span>
            {onRemove && (
              <button onClick={onRemove} className="ml-2 text-slate-600 hover:text-red-400">
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </td>
      </tr>
    )
  }

  if (error || !data) {
    return (
      <tr className="border-b" style={{ borderColor: '#1e2d45' }}>
        <td className="px-4 py-3 text-xs" style={{ color: '#1e2d45' }}>{idx}</td>
        <td className="px-4 py-3" colSpan={9}>
          <div className="flex items-center gap-2">
            <span className="ticker-badge">{ticker}</span>
            <span className="text-xs text-red-400">Failed to load</span>
            {onRemove && (
              <button onClick={onRemove} className="ml-2 text-slate-600 hover:text-red-400">
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </td>
      </tr>
    )
  }

  return <SignalRow s={data} idx={idx} badge={badge} onRemove={onRemove} />
}

export default function SignalsTable({ signals, loading, customTickers, pinnedTicker, onAddTicker, onRemoveTicker, onClearPin }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('score')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [addInput, setAddInput] = useState('')
  const [showAddInput, setShowAddInput] = useState(false)

  const toggleSort = (key: SortKey) => {
    if (key === sortKey) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const handleAdd = () => {
    const t = addInput.trim().toUpperCase()
    if (!t) return
    onAddTicker(t)
    setAddInput('')
    setShowAddInput(false)
  }

  // Filter regular signals: exclude pinned + custom tickers to avoid duplicates
  const specialTickers = new Set([
    ...(pinnedTicker ? [pinnedTicker] : []),
    ...customTickers,
  ])
  const regularSignals = [...signals]
    .filter(s => !specialTickers.has(s.ticker))
    .sort((a, b) => {
      const mul = sortDir === 'desc' ? -1 : 1
      return mul * (a[sortKey] - b[sortKey])
    })

  const SortIcon = ({ col }: { col: SortKey }) =>
    sortKey === col
      ? sortDir === 'desc' ? <ChevronDown className="w-3 h-3 inline" /> : <ChevronUp className="w-3 h-3 inline" />
      : null

  const cols = [
    { label: '#',            key: null },
    { label: 'Ticker',       key: null },
    { label: 'Price',        key: 'price' as SortKey },
    { label: 'Master Score', key: 'score' as SortKey },
    { label: 'Signal',       key: null },
    { label: 'Options Flow', key: 'options_flow_score' as SortKey },
    { label: 'Gamma',        key: 'gamma_score' as SortKey },
    { label: 'Dark Pool',    key: 'dark_pool_flow' as SortKey },
    { label: 'Breakout Prob',key: 'breakout_probability' as SortKey },
    { label: 'Mkt Cap',      key: null },
  ]

  if (loading) {
    return (
      <div className="glass-card p-8 flex items-center justify-center">
        <div className="text-slate-500 animate-pulse">Loading signals…</div>
      </div>
    )
  }

  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b flex items-center gap-3" style={{ borderColor: '#1e2d45' }}>
        <div className="flex-1">
          <h2 className="font-bold text-white">Top Smart Money Stocks</h2>
          <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>
            {signals.length + customTickers.length + (pinnedTicker ? 1 : 0)} tickers tracked — sorted by Master Score
          </p>
        </div>

        {/* Add stock button / inline input */}
        {showAddInput ? (
          <div className="flex items-center gap-2">
            <input
              autoFocus
              value={addInput}
              onChange={e => setAddInput(e.target.value.toUpperCase())}
              onKeyDown={e => { if (e.key === 'Enter') handleAdd(); if (e.key === 'Escape') setShowAddInput(false) }}
              placeholder="e.g. NVDA"
              maxLength={8}
              className="text-xs px-3 py-1.5 rounded-lg w-28 uppercase"
              style={{ background: '#0d1526', color: '#e2e8f0', border: '1px solid #3b82f6', outline: 'none' }}
            />
            <button onClick={handleAdd}
              className="text-xs px-3 py-1.5 rounded-lg font-bold transition-all"
              style={{ background: '#3b82f620', color: '#3b82f6', border: '1px solid #3b82f6' }}>
              Add
            </button>
            <button onClick={() => setShowAddInput(false)}
              className="text-xs px-2 py-1.5 rounded-lg transition-all"
              style={{ background: '#1e2d45', color: '#64748b' }}>
              <X className="w-3 h-3" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowAddInput(true)}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-all hover:text-white"
            style={{ background: '#141c2e', color: '#64748b', border: '1px solid #1e2d45' }}>
            <Plus className="w-3.5 h-3.5" /> Add Stock
          </button>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full data-table">
          <thead>
            <tr style={{ borderBottom: '1px solid #1e2d45' }}>
              {cols.map(({ label, key }) => (
                <th key={label}
                  className={`px-4 py-3 text-left ${key ? 'cursor-pointer hover:text-white select-none' : ''}`}
                  style={{ color: '#64748b' }}
                  onClick={() => key && toggleSort(key)}>
                  {label} {key && <SortIcon col={key} />}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Pinned ticker (from search) — always first */}
            {pinnedTicker && (
              <FetchedRow
                ticker={pinnedTicker}
                idx="★"
                badge={
                  <span className="text-xs px-1.5 py-0.5 rounded font-bold"
                    style={{ background: '#3b82f620', color: '#3b82f6', fontSize: 9 }}>
                    SEARCH
                  </span>
                }
                onRemove={onClearPin}
              />
            )}

            {/* Custom added tickers */}
            {customTickers.map((ticker, i) => (
              <FetchedRow
                key={ticker}
                ticker={ticker}
                idx={`+${i + 1}`}
                badge={
                  <span className="text-xs px-1.5 py-0.5 rounded font-bold"
                    style={{ background: '#8b5cf620', color: '#8b5cf6', fontSize: 9 }}>
                    ADDED
                  </span>
                }
                onRemove={() => onRemoveTicker(ticker)}
              />
            ))}

            {/* Regular signals */}
            {regularSignals.map((s, idx) => (
              <SignalRow key={s.ticker} s={s} idx={idx + 1} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
