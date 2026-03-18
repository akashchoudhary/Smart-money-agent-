import React from 'react'
import useSWR from 'swr'
import { fetchLogs } from '../lib/api'

const SOURCE_COLORS: Record<string, string> = {
  real:  '#00d084',
  mock:  '#f59e0b',
  error: '#ff4d6d',
}

const ENGINE_LABELS: Record<string, string> = {
  price:   'Price',
  insider: 'Insider',
  options: 'Options',
}

export default function DataSourceLogs() {
  const { data: logs = [], isLoading } = useSWR('logs', () => fetchLogs(80), { refreshInterval: 15000 })

  return (
    <div className="flex-1 overflow-y-auto" style={{ fontSize: 11 }}>
      {isLoading && (
        <div className="text-center py-6 text-slate-600 animate-pulse text-xs">Loading logs…</div>
      )}
      {!isLoading && logs.length === 0 && (
        <div className="text-center py-6 text-xs" style={{ color: '#64748b' }}>
          No log entries yet — trigger a data refresh.
        </div>
      )}
      {logs.map((entry: any, i: number) => (
        <div key={i} className="px-3 py-1.5 border-b flex items-start gap-2"
          style={{ borderColor: '#1e2d45' }}>
          {/* source pill */}
          <span className="shrink-0 px-1.5 py-0.5 rounded font-bold uppercase"
            style={{
              background: `${SOURCE_COLORS[entry.source] ?? '#64748b'}20`,
              color: SOURCE_COLORS[entry.source] ?? '#64748b',
              fontSize: 9,
              letterSpacing: '0.05em',
            }}>
            {entry.source}
          </span>
          {/* engine badge */}
          <span className="shrink-0 px-1.5 py-0.5 rounded"
            style={{ background: '#1e2d45', color: '#94a3b8', fontSize: 9 }}>
            {ENGINE_LABELS[entry.engine] ?? entry.engine}
          </span>
          {/* ticker */}
          <span className="font-bold shrink-0" style={{ color: '#e2e8f0', minWidth: 36 }}>
            {entry.ticker}
          </span>
          {/* detail */}
          <span className="flex-1 truncate" style={{ color: '#64748b' }} title={entry.detail}>
            {entry.detail}
          </span>
          {/* time */}
          <span className="shrink-0" style={{ color: '#334155' }}>{entry.ts}</span>
        </div>
      ))}
    </div>
  )
}
