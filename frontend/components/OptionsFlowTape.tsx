import React from 'react'
import useSWR from 'swr'
import { fetchOptionsFlow, fmtMoney } from '../lib/api'
import { Activity } from 'lucide-react'

export default function OptionsFlowTape() {
  const { data, isLoading } = useSWR('options-flow', () => fetchOptionsFlow(15), { refreshInterval: 15000 })

  return (
    <div className="glass-card h-full flex flex-col">
      <div className="px-4 py-3 border-b flex items-center gap-2" style={{ borderColor: '#1e2d45' }}>
        <Activity className="w-4 h-4 text-blue-400" />
        <h3 className="font-bold text-white text-sm">Options Flow Tape</h3>
        <span className="live-dot ml-auto" />
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {isLoading && (
          <div className="text-center py-8 text-slate-600 text-xs animate-pulse">Loading…</div>
        )}
        {data?.map((row: any, i: number) => (
          <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg transition-colors"
            style={{ background: '#0f1623' }}>
            <span className="ticker-badge text-sm">{row.ticker}</span>
            <span className="text-xs" style={{ color: '#00d084' }}>
              {row.options_flow_score.toFixed(0)}
            </span>
            <span className="text-xs" style={{ color: '#64748b' }}>score</span>
            <span className={`text-xs font-bold ${row.signal === 'bullish' ? 'bull' : row.signal === 'bearish' ? 'bear' : 'neutral'}`}>
              {row.signal.toUpperCase()}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
