import React from 'react'
import useSWR from 'swr'
import { fetchDarkPool, fmtMoney } from '../lib/api'
import { Layers } from 'lucide-react'

export default function DarkPoolFeed() {
  const { data, isLoading } = useSWR('darkpool', () => fetchDarkPool(15), { refreshInterval: 15000 })

  return (
    <div className="glass-card h-full flex flex-col">
      <div className="px-4 py-3 border-b flex items-center gap-2" style={{ borderColor: '#1e2d45' }}>
        <Layers className="w-4 h-4 text-purple-400" />
        <h3 className="font-bold text-white text-sm">Dark Pool Feed</h3>
        <span className="live-dot ml-auto" />
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {isLoading && <div className="text-center py-8 text-slate-600 text-xs animate-pulse">Loading…</div>}
        {data?.map((row: any, i: number) => (
          <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg"
            style={{ background: '#0f1623' }}>
            <span className="ticker-badge text-sm">{row.ticker}</span>
            <div className="flex flex-col items-end">
              <span className="text-xs font-bold" style={{ color: row.dark_pool_flow > 5e6 ? '#00d084' : '#64748b' }}>
                {fmtMoney(row.dark_pool_flow)}
              </span>
              <span className="text-xs" style={{ color: '#1e2d45' }}>net flow</span>
            </div>
            <span className={`text-xs ${row.signal === 'bullish' ? 'bull' : row.signal === 'bearish' ? 'bear' : 'neutral'}`}>
              {row.signal.toUpperCase()}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
