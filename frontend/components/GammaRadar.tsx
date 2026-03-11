import React from 'react'
import useSWR from 'swr'
import { fetchGamma } from '../lib/api'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts'
import { Zap } from 'lucide-react'

export default function GammaRadar() {
  const { data, isLoading } = useSWR('gamma', () => fetchGamma(8), { refreshInterval: 20000 })

  const chartData = data?.slice(0, 8).map((row: any) => ({
    ticker: row.ticker,
    score: Math.round(row.gamma_score),
  })) ?? []

  return (
    <div className="glass-card h-full flex flex-col">
      <div className="px-4 py-3 border-b flex items-center gap-2" style={{ borderColor: '#1e2d45' }}>
        <Zap className="w-4 h-4 text-yellow-400" />
        <h3 className="font-bold text-white text-sm">Gamma Squeeze Radar</h3>
      </div>
      <div className="flex-1 p-2">
        {isLoading
          ? <div className="flex items-center justify-center h-full text-slate-600 text-xs animate-pulse">Loading…</div>
          : (
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={chartData}>
                <PolarGrid stroke="#1e2d45" />
                <PolarAngleAxis dataKey="ticker" tick={{ fill: '#64748b', fontSize: 11 }} />
                <Radar name="Gamma Score" dataKey="score" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.25} strokeWidth={2} />
                <Tooltip
                  contentStyle={{ background: '#141c2e', border: '1px solid #1e2d45', borderRadius: 8 }}
                  labelStyle={{ color: '#e2e8f0' }}
                  itemStyle={{ color: '#8b5cf6' }}
                />
              </RadarChart>
            </ResponsiveContainer>
          )
        }
      </div>
      <div className="px-4 pb-3">
        <div className="flex flex-wrap gap-2">
          {data?.slice(0, 5).map((row: any) => (
            <div key={row.ticker} className="flex items-center gap-1 text-xs px-2 py-1 rounded"
              style={{ background: '#0f1623', color: '#8b5cf6' }}>
              <span className="font-bold">{row.ticker}</span>
              <span style={{ color: '#64748b' }}>{row.gamma_score.toFixed(0)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
