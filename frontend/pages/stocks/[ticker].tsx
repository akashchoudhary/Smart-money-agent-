import React from 'react'
import { useRouter } from 'next/router'
import useSWR from 'swr'
import Link from 'next/link'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, ReferenceLine
} from 'recharts'
import { fetchStock, scoreColor, scoreLabel, fmtMoney, fmtMarketCap } from '../../lib/api'
import ScoreGauge from '../../components/ScoreGauge'
import StockChart from '../../components/StockChart'
import { ArrowLeft, TrendingUp, Layers, Zap, Users } from 'lucide-react'

const tooltipStyle = {
  contentStyle: { background: '#141c2e', border: '1px solid #1e2d45', borderRadius: 8, fontSize: 11 },
  labelStyle: { color: '#e2e8f0' },
}

function StatRow({ label, value, color = '#e2e8f0' }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b" style={{ borderColor: '#1e2d45' }}>
      <span className="text-xs" style={{ color: '#64748b' }}>{label}</span>
      <span className="text-xs font-bold" style={{ color }}>{value}</span>
    </div>
  )
}

export default function StockDetail() {
  const { query } = useRouter()
  const ticker = (query.ticker as string || '').toUpperCase()
  const { data, isLoading, error } = useSWR(ticker ? `stock-${ticker}` : null, () => fetchStock(ticker), { refreshInterval: 30000 })

  if (!ticker) return null

  if (isLoading) return (
    <div className="flex items-center justify-center h-64 text-slate-600 animate-pulse text-sm">
      Fetching {ticker}…
    </div>
  )

  if (error || !data) return (
    <div className="flex items-center justify-center h-64 text-red-400 text-sm">
      Failed to load data for {ticker}
    </div>
  )

  const { market_data: md, master_signal: ms, price_history, dark_pool_history,
    gamma_history, options_flow_history, insider_trades, ai_signal } = data

  const dpChart = dark_pool_history.slice(-30).map(d => ({
    time: d.timestamp.slice(5, 10),
    net: Math.round(d.dark_pool_net_flow / 1e6 * 10) / 10,
  }))

  const gammaChart = gamma_history.slice(-30).map(g => ({
    time: g.timestamp.slice(5, 10),
    gex: Math.round(g.gamma_exposure / 1e6),
  }))

  const optionsChart = options_flow_history.slice(0, 10).map(o => ({
    strike: o.strike,
    premium: Math.round(o.premium / 1e3),
    type: o.option_type,
  }))

  const subScores = [
    { label: 'Options Flow', value: ms.options_flow_score, color: '#3b82f6' },
    { label: 'Gamma Exposure', value: ms.gamma_exposure_score, color: '#8b5cf6' },
    { label: 'Dark Pool', value: ms.dark_pool_score, color: '#06b6d4' },
    { label: 'Volume Spike', value: ms.volume_spike_score, color: '#f59e0b' },
    { label: 'Insider Buying', value: ms.insider_buying_score, color: '#f97316' },
    { label: 'Institutional', value: ms.institutional_flow_score, color: '#ec4899' },
    { label: 'AI Score', value: ms.ai_score, color: '#00d084' },
  ]

  return (
    <div className="space-y-5">
      {/* Back + header */}
      <div className="flex items-center gap-4">
        <Link href="/" className="flex items-center gap-1.5 text-xs hover:text-white transition-colors"
          style={{ color: '#64748b' }}>
          <ArrowLeft className="w-3.5 h-3.5" /> Back
        </Link>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-white">{ticker}</h1>
            <span className="text-xl font-bold text-white">${md.price.toFixed(2)}</span>
            <span className={`text-sm font-bold ${md.change_pct >= 0 ? 'bull' : 'bear'}`}>
              {md.change_pct >= 0 ? '+' : ''}{md.change_pct.toFixed(2)}%
            </span>
            <span className={`text-xs font-bold px-2 py-1 rounded ${
              ms.direction === 'bullish' ? 'bg-green-900/40 text-green-400' :
              ms.direction === 'bearish' ? 'bg-red-900/40 text-red-400' : 'bg-slate-800 text-slate-400'
            }`}>
              {ms.direction.toUpperCase()}
            </span>
          </div>
          <p className="text-xs mt-1" style={{ color: '#64748b' }}>
            Market Cap: {fmtMarketCap(md.market_cap)} · Vol: {(md.volume / 1e6).toFixed(1)}M
            · 30d Avg: {(md.avg_volume_30d / 1e6).toFixed(1)}M
            · Short: {(md.short_interest * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Score + sub-scores */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-card p-5 flex flex-col items-center gap-3">
          <ScoreGauge score={ms.master_score} label />
          <p className="text-xs text-center" style={{ color: '#64748b' }}>
            Master Score — weighted composite of all signals
          </p>
        </div>

        <div className="glass-card p-5 col-span-2">
          <h3 className="font-bold text-white text-sm mb-4">Signal Breakdown</h3>
          <div className="space-y-2.5">
            {subScores.map(({ label, value, color }) => (
              <div key={label} className="flex items-center gap-3">
                <span className="text-xs w-32 shrink-0" style={{ color: '#64748b' }}>{label}</span>
                <div className="flex-1 h-2 rounded-full" style={{ background: '#1e2d45' }}>
                  <div className="h-2 rounded-full transition-all"
                    style={{ width: `${Math.min(100, value)}%`, background: color }} />
                </div>
                <span className="text-xs font-bold w-10 text-right" style={{ color }}>
                  {value.toFixed(0)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Prediction card */}
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="w-4 h-4 text-green-400" />
          <h3 className="font-bold text-white text-sm">AI Prediction</h3>
          <span className="text-xs ml-auto" style={{ color: '#64748b' }}>{ai_signal.model_version}</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold" style={{ color: `hsl(${ai_signal.breakout_probability * 120},70%,55%)` }}>
              {(ai_signal.breakout_probability * 100).toFixed(0)}%
            </div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>Breakout Probability</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-white">{(ai_signal.confidence * 100).toFixed(0)}%</div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>Model Confidence</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold" style={{ color: md.volume_ratio > 3 ? '#00d084' : '#64748b' }}>
              {md.volume_ratio.toFixed(2)}x
            </div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>Volume Ratio</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold" style={{ color: '#f59e0b' }}>
              {(md.short_interest * 100).toFixed(1)}%
            </div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>Short Interest</div>
          </div>
        </div>
      </div>

      {/* Price chart */}
      <StockChart data={price_history} ticker={ticker} />

      {/* Dark pool + Gamma charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h3 className="font-bold text-white text-sm">Dark Pool Net Flow (30d)</h3>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={dpChart}>
              <CartesianGrid stroke="#1e2d45" strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 10 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={v => `${v}M`} />
              <Tooltip {...tooltipStyle} formatter={(v: number) => [`${v}M`, 'Net Flow']} />
              <ReferenceLine y={0} stroke="#1e2d45" />
              <Area dataKey="net" stroke="#06b6d4" fill="#06b6d420" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-4 h-4 text-yellow-400" />
            <h3 className="font-bold text-white text-sm">Gamma Exposure (30d)</h3>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={gammaChart}>
              <CartesianGrid stroke="#1e2d45" strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 10 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={v => `${v}M`} />
              <Tooltip {...tooltipStyle} formatter={(v: number) => [`${v}M`, 'GEX']} />
              <ReferenceLine y={0} stroke="#1e2d45" />
              <Bar dataKey="gex" fill="#8b5cf6" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Options flow */}
      <div className="glass-card p-4">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="w-4 h-4 text-blue-400" />
          <h3 className="font-bold text-white text-sm">Options Flow (by strike)</h3>
        </div>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={optionsChart}>
            <CartesianGrid stroke="#1e2d45" strokeDasharray="3 3" />
            <XAxis dataKey="strike" tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={v => `$${v}`} />
            <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={v => `${v}K`} />
            <Tooltip {...tooltipStyle} formatter={(v: number) => [`$${v}K`, 'Premium']} />
            <Bar dataKey="premium" radius={[2, 2, 0, 0]}
              fill="#3b82f6"
              label={{ position: 'top', fontSize: 9, fill: '#64748b' }} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Insider trades */}
      <div className="glass-card overflow-hidden">
        <div className="px-4 py-3 border-b flex items-center gap-2" style={{ borderColor: '#1e2d45' }}>
          <Users className="w-4 h-4 text-orange-400" />
          <h3 className="font-bold text-white text-sm">Insider Trades</h3>
        </div>
        {insider_trades.length === 0
          ? <div className="px-4 py-6 text-xs" style={{ color: '#64748b' }}>No qualifying insider trades in window</div>
          : (
            <table className="w-full data-table">
              <thead>
                <tr style={{ borderBottom: '1px solid #1e2d45' }}>
                  {['Insider', 'Role', 'Type', 'Shares', 'Value', 'Price', 'Date'].map(h => (
                    <th key={h} className="px-4 py-2 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {insider_trades.map((t, i) => (
                  <tr key={i} className="border-b" style={{ borderColor: '#1e2d45' }}>
                    <td className="px-4 py-2.5 text-white">{t.insider_name}</td>
                    <td className="px-4 py-2.5" style={{ color: '#64748b' }}>{t.role}</td>
                    <td className="px-4 py-2.5">
                      <span className={`font-bold ${t.transaction_type === 'buy' ? 'bull' : 'bear'}`}>
                        {t.transaction_type.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-2.5" style={{ color: '#94a3b8' }}>
                      {t.shares.toLocaleString()}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: t.transaction_type === 'buy' ? '#00d084' : '#ff4d6d' }}>
                      {fmtMoney(t.transaction_value)}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: '#64748b' }}>
                      ${t.price_per_share.toFixed(2)}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: '#64748b' }}>{t.filing_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        }
      </div>
    </div>
  )
}
