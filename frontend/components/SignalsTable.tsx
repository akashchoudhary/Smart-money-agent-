import React, { useState } from 'react'
import Link from 'next/link'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { SignalResponse, scoreColor, scoreLabel, fmtMoney, fmtMarketCap } from '../lib/api'

interface Props {
  signals: SignalResponse[]
  loading?: boolean
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

export default function SignalsTable({ signals, loading }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('score')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const toggleSort = (key: SortKey) => {
    if (key === sortKey) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const sorted = [...signals].sort((a, b) => {
    const mul = sortDir === 'desc' ? -1 : 1
    return mul * (a[sortKey] - b[sortKey])
  })

  const SortIcon = ({ col }: { col: SortKey }) =>
    sortKey === col
      ? sortDir === 'desc' ? <ChevronDown className="w-3 h-3 inline" /> : <ChevronUp className="w-3 h-3 inline" />
      : null

  if (loading) {
    return (
      <div className="glass-card p-8 flex items-center justify-center">
        <div className="text-slate-500 animate-pulse">Loading signals…</div>
      </div>
    )
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-5 py-4 border-b" style={{ borderColor: '#1e2d45' }}>
        <h2 className="font-bold text-white">Top Smart Money Stocks</h2>
        <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>
          {signals.length} tickers tracked — sorted by Master Score
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full data-table">
          <thead>
            <tr style={{ borderBottom: '1px solid #1e2d45' }}>
              {[
                { label: '#', key: null },
                { label: 'Ticker', key: null },
                { label: 'Price', key: 'price' as SortKey },
                { label: 'Master Score', key: 'score' as SortKey },
                { label: 'Signal', key: null },
                { label: 'Options Flow', key: 'options_flow_score' as SortKey },
                { label: 'Gamma', key: 'gamma_score' as SortKey },
                { label: 'Dark Pool', key: 'dark_pool_flow' as SortKey },
                { label: 'Breakout Prob', key: 'breakout_probability' as SortKey },
                { label: 'Mkt Cap', key: null },
              ].map(({ label, key }) => (
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
            {sorted.map((s, idx) => (
              <tr key={s.ticker} className="border-b transition-colors"
                style={{ borderColor: '#1e2d45' }}>
                <td className="px-4 py-3 text-xs" style={{ color: '#1e2d45' }}>{idx + 1}</td>
                <td className="px-4 py-3">
                  <Link href={`/stocks/${s.ticker}`}
                    className="ticker-badge hover:text-white transition-colors">
                    {s.ticker}
                  </Link>
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
                <td className="px-4 py-3">
                  <MiniBar value={s.options_flow_score} color="#3b82f6" />
                </td>
                <td className="px-4 py-3">
                  <MiniBar value={s.gamma_score} color="#8b5cf6" />
                </td>
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
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
