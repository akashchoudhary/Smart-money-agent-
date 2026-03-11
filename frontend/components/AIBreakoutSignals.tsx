import React from 'react'
import useSWR from 'swr'
import Link from 'next/link'
import { fetchAIPredictions } from '../lib/api'
import { TrendingUp } from 'lucide-react'

export default function AIBreakoutSignals() {
  const { data, isLoading } = useSWR('ai-predictions', () => fetchAIPredictions(10), { refreshInterval: 20000 })

  return (
    <div className="glass-card h-full flex flex-col">
      <div className="px-4 py-3 border-b flex items-center gap-2" style={{ borderColor: '#1e2d45' }}>
        <TrendingUp className="w-4 h-4 text-green-400" />
        <h3 className="font-bold text-white text-sm">AI Breakout Signals</h3>
        <span className="text-xs ml-auto px-1.5 py-0.5 rounded" style={{ background: '#1e2d45', color: '#64748b' }}>
          XGBoost
        </span>
      </div>
      <div className="flex-1 overflow-y-auto divide-y" style={{ borderColor: '#1e2d45' }}>
        {isLoading && <div className="text-center py-8 text-slate-600 text-xs animate-pulse">Loading…</div>}
        {data?.map((row: any, i: number) => {
          const prob = row.breakout_probability
          const pct = (prob * 100).toFixed(0)
          const color = prob >= 0.7 ? '#00d084' : prob >= 0.5 ? '#f59e0b' : '#64748b'
          return (
            <div key={i} className="px-4 py-3 flex items-center gap-3">
              <span className="text-xs" style={{ color: '#64748b', width: 16 }}>{i + 1}</span>
              <Link href={`/stocks/${row.ticker}`} className="ticker-badge flex-1 hover:text-white transition-colors">
                {row.ticker}
              </Link>
              <div className="flex-1">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <div className="flex-1 h-1.5 rounded-full" style={{ background: '#1e2d45' }}>
                    <div className="h-1.5 rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
                  </div>
                  <span className="text-xs font-bold" style={{ color }}>{pct}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs" style={{ color: '#64748b' }}>breakout prob</span>
                  <span className={`text-xs ${row.signal === 'bullish' ? 'bull' : row.signal === 'bearish' ? 'bear' : 'neutral'}`}>
                    {row.signal}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
