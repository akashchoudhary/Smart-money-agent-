import React, { useState } from 'react'
import useSWR from 'swr'
import Link from 'next/link'
import { fetchAIPredictions } from '../lib/api'
import { TrendingUp, ScrollText } from 'lucide-react'
import DataSourceLogs from './DataSourceLogs'

type Tab = 'ai' | 'logs'

export default function AIBreakoutSignals() {
  const [tab, setTab] = useState<Tab>('ai')
  const { data, isLoading } = useSWR('ai-predictions', () => fetchAIPredictions(10), { refreshInterval: 20000 })

  return (
    <div className="glass-card h-full flex flex-col">
      {/* Header + tabs */}
      <div className="px-4 py-3 border-b flex items-center gap-2" style={{ borderColor: '#1e2d45' }}>
        <TrendingUp className="w-4 h-4 text-green-400" />
        <h3 className="font-bold text-white text-sm">Signals</h3>
        <div className="flex ml-auto gap-0.5">
          <button
            onClick={() => setTab('ai')}
            className="flex items-center gap-1 px-2 py-1 rounded text-xs transition-all"
            style={{
              background: tab === 'ai' ? '#1e2d45' : 'transparent',
              color: tab === 'ai' ? '#e2e8f0' : '#64748b',
            }}>
            <TrendingUp className="w-3 h-3" /> AI Signal
          </button>
          <button
            onClick={() => setTab('logs')}
            className="flex items-center gap-1 px-2 py-1 rounded text-xs transition-all"
            style={{
              background: tab === 'logs' ? '#1e2d45' : 'transparent',
              color: tab === 'logs' ? '#e2e8f0' : '#64748b',
            }}>
            <ScrollText className="w-3 h-3" /> Logs
          </button>
        </div>
      </div>

      {/* Tab: AI Signals */}
      {tab === 'ai' && (
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
      )}

      {/* Tab: Logs */}
      {tab === 'logs' && <DataSourceLogs />}
    </div>
  )
}
